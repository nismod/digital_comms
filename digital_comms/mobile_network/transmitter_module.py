import os, sys, configparser
import csv
import glob

from rtree import index
import fiona
from shapely.geometry import shape, Point, Polygon, MultiPoint, mapping
from shapely.geometry.polygon import Polygon
from shapely.wkt import loads
from shapely.prepared import prep
import numpy as np
from pyproj import Proj, transform, Geod
from geographiclib.geodesic import Geodesic
import matplotlib.pyplot as plt
import pandas as pd
from scipy.spatial import Delaunay

from itertools import tee
from collections import OrderedDict

from digital_comms.mobile_network.path_loss_module import path_loss_calculator

#set seed for stochastic predictablity
np.random.seed(42)

# from built_env_module import find_line_of_sight

CONFIG = configparser.ConfigParser()
CONFIG.read(
    os.path.join(
        os.path.dirname(__file__), '..',  '..', 'scripts','script_config.ini'
        )
    )
BASE_PATH = CONFIG['file_locations']['base_path']

#data locations
DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')
DATA_RESULTS = os.path.join(BASE_PATH, '..' ,'results', 'system_simulator')

#set numpy seed
np.random.seed(42)

def read_postcode_sector(postcode_sector):

    postcode_area = ''.join(
        [i for i in postcode_sector[:2] if not i.isdigit()]
        )
    postcode_area = postcode_area.lower()
    with fiona.open(
        os.path.join(
            DATA_RAW, 'd_shapes', 'postcode_sectors', postcode_area + '.shp')
            , 'r') as source:

        return [
            sector for sector in source \
            if sector['properties']['postcode'].replace(
                " ", "") == postcode_sector][0]

def get_local_authority_ids(postcode_sector):

    with fiona.open(os.path.join(
        DATA_RAW, 'd_shapes','lad_uk_2016-12', 'lad_uk_2016-12.shp'),
        'r') as source:
        postcode_sector_geom = shape(postcode_sector['geometry'])
        return [
            lad['properties']['name'] for lad in source \
            if postcode_sector_geom.intersection(shape(lad['geometry']))
            ]

def import_area_lut(postcode_sector_name, lad_ids):

    for lad in lad_ids:
        path = os.path.join(
            DATA_RAW, '..', 'intermediate', 'mobile_geotype_lut',
            lad, lad + '.csv'
            )
        with open(path, 'r') as system_file:
            reader = csv.DictReader(system_file)
            for line in reader:
                if line['postcode_sector'].replace(
                    " ", "") == postcode_sector_name:
                    lut = {
                        'postcode_sector': line['postcode_sector'],
                        'indoor_probability': line['indoor_probability'],
                        'outdoor_probability': line['outdoor_probability'],
                        'residential_count': line['residential_count'],
                        'non_residential_count': line['non_residential_count'],
                        'area': line['area'],
                    }

    return lut

def determine_environment(postcode_sector_lut):

    estimated_population = float(postcode_sector_lut['residential_count'])*2.5

    population_density = (
        estimated_population / float(postcode_sector_lut['area'])
        )

    if population_density >= 7959:
        environment = 'urban'
    elif 3119 <= population_density < 7959:
        environment = 'suburban'
    elif 782 <= population_density < 3119:
        environment = 'suburban'
    elif 112 <= population_density < 782:
        environment = 'rural'
    elif 47 <= population_density < 112:
        environment = 'rural'
    elif 25 <= population_density < 47:
        environment = 'rural'
    elif population_density < 25:
        environment = 'rural'
    else:
        environment = 'Environment not determined'
        raise ValueError('Could not determine environment')

    return environment

def get_transmitters(postcode_sector):

    transmitters = []

    geom = shape(postcode_sector['geometry'])
    geom_length = geom.length
    geom_buffer = geom.buffer(geom_length)
    geom_box = geom_buffer.bounds

    id_number = 0

    with open(
        os.path.join(
            DATA_INTERMEDIATE, 'sitefinder', 'sitefinder_processed.csv'), 'r'
            ) as system_file:
            reader = csv.DictReader(system_file)
            for line in reader:
                if (
                    geom_box[0] <= float(line['longitude']) and
                    geom_box[1] <= float(line['latitude']) and
                    geom_box[2] >= float(line['longitude']) and
                    geom_box[3] >= float(line['latitude'])
                    ):
                    transmitters.append({
                        'type': "Feature",
                        'geometry': {
                            "type": "Point",
                            "coordinates": [
                                float(line['longitude']),
                                float(line['latitude'])
                                ]
                        },
                        'properties': {
                            # "operator": line[2],
                            "sitengr": 'site_id_{}'.format(id_number),
                            "ant_height": line['Antennaht'],
                            "tech": line['Transtype'],
                            "freq": line['Freqband'],
                            "type": line['Anttype'],
                            "power": line['Powerdbw'],
                            # "power_dbw": line['Powerdbw'],
                            # "max_power_dbw": line['Maxpwrdbw'],
                            # "max_power_dbm": line['Maxpwrdbm'],
                            "gain": 18,
                            "losses": 2,
                        }
                    })

                    id_number += 1
                else:
                    pass

    return transmitters

def generate_receivers(postcode_sector, postcode_sector_lut, quantity):
    """
    The indoor probability provides a likelihood of a user being indoor,
    given the building footprint area and number of floors for all
    building stock, in a postcode sector.

    Parameters
    ----------
    postcode_sector : polygon
        Shape of the area we want to generate receivers within.
    postcode_sector_lut : dict
        Contains information on indoor and outdoor probability.
    quantity: int
        Number of receivers we want to generate within the desired area.

    Output
    ------
    receivers : List of dicts
        Contains the quantity of desired receivers within the area boundary.

    """
    indoor_probability = postcode_sector_lut['indoor_probability']

    coordinates = []

    geom = shape(postcode_sector['geometry'])
    geom_box = geom.bounds

    minx = geom_box[0]
    miny = geom_box[1]
    maxx = geom_box[2]
    maxy = geom_box[3]

    receivers = []

    id_number = 0

    while len(receivers) < quantity:

        x_coord = np.random.uniform(low=minx, high=maxx, size=1)
        y_coord = np.random.uniform(low=miny, high=maxy, size=1)

        indoor_outdoor_probability = np.random.rand(1,1)[0][0]

        coordinates = list(zip(x_coord, y_coord))

        # Join the two
        postcode_sector_shape = shape(postcode_sector['geometry'])
        receiver = Point((x_coord, y_coord))
        if postcode_sector_shape.contains(receiver):
            receivers.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [coordinates[0][0],coordinates[0][1]],
                },
                'properties': {
                    'ue_id': "id_{}".format(id_number),
                    #"sitengr": 'TL4454059600',
                    "misc_losses": 4,
                    "gain": 4,
                    "losses": 4,
                    "indoor": (True if float(indoor_outdoor_probability) < \
                        float(indoor_probability) else False),
                }
            })
            id_number += 1

        else:
            pass

    return receivers

def find_and_deploy_new_transmitter(
    existing_transmitters, iteration_number, geojson_postcode_sector):
    """
    Given existing transmitter locations, try deploy a new one in the area
    which has the largest existing gap between transmitters.

    Parameters
    ----------
    existing_transmitters : List of objects
        Contains existing transmitters
    iteration_number : int
        The loop index, used for the providing the id for a new asset
    geojson_postcode_sector : GeoJson
        The postcode sector boundary in GeoJson format.

    """
    existing_transmitter_coordinates = []
    for existing_transmitter in existing_transmitters.values():
        existing_transmitter_coordinates.append(
            existing_transmitter.coordinates
            )

    #convert to numpy array
    existing_transmitter_coordinates = np.array(
        existing_transmitter_coordinates
        )

    #get delaunay grid
    tri = Delaunay(existing_transmitter_coordinates)

    #get coordinates from gri
    coord_groups = [tri.points[x] for x in tri.simplices]

    #convert coordinate groups to polygons
    polygons = [Polygon(x) for x in coord_groups]

    #sort based on area
    polygons = sorted(polygons, key=lambda x: x.area, reverse=True)

    geom = shape(geojson_postcode_sector['geometry'])

    #try to allocate using the delauney polygon with the largest area first
    try:
        for new_site_area in polygons:

            #get the centroid from the largest area
            centroid = new_site_area.centroid

            if geom.contains(centroid):
                break
            else:
                continue

        x_coord = np.random.uniform(low=minx, high=maxx, size=1)
        y_coord = np.random.uniform(low=miny, high=maxy, size=1)

    #if no delauney polygon centroids are in the area boundary, randomly allocate
    except:

        geom_box = geom.bounds

        minx = geom_box[0]
        miny = geom_box[1]
        maxx = geom_box[2]
        maxy = geom_box[3]

        random_transmitter_location = []

        while len(random_transmitter_location) == 0:

            x_coord = np.random.uniform(low=minx, high=maxx, size=1)
            y_coord = np.random.uniform(low=miny, high=maxy, size=1)

            receiver = Point((x_coord, y_coord))

            if geom.contains(receiver):
                centroid = receiver.centroid
                random_transmitter_location.append(receiver)

            else:

                continue

    NEW_TRANSMITTERS = []

    NEW_TRANSMITTERS.append({
        'type': "Feature",
        'geometry': {
            "type": "Point",
            "coordinates": [centroid.x, centroid.y]
        },
        'properties': {
                "operator": 'unknown',
                "sitengr": "{" + 'new' + "}{GEN" + str(iteration_number) + '}',
                "ant_height": 20,
                "tech": 'LTE',
                "freq": 700,
                "type": 17,
                "power": 30,
                "gain": 18,
                "losses": 2,
            }
        })

    return NEW_TRANSMITTERS

class NetworkManager(object):

    def __init__(self, area, transmitters, receivers):

        self.area = {}
        self.transmitters = {}
        self.receivers = {}

        area_id = area['properties']['postcode']
        self.area[area_id] = Area(area)

        for transmitter in transmitters:
            transmitter_id = transmitter['properties']["sitengr"]
            transmitter = Transmitter(transmitter)
            self.transmitters[transmitter_id] = transmitter

            area_containing_transmitters = self.area[area_id]
            area_containing_transmitters.add_transmitter(transmitter)

        for receiver in receivers:
            receiver_id = receiver['properties']["ue_id"]
            receiver = Receiver(receiver)
            self.receivers[receiver_id] = receiver

            area_containing_receivers = self.area[area_id]
            area_containing_receivers.add_receiver(receiver)

    def build_new_assets(self, list_of_new_assets, area_id):

        for transmitter in list_of_new_assets:
            transmitter_id = transmitter['properties']["sitengr"]
            transmitter = Transmitter(transmitter)

            self.transmitters[transmitter_id] = transmitter

            for area_containing_transmitters in self.area.values():
                if area_containing_transmitters.id == area_id:
                    area_containing_transmitters.add_transmitter(transmitter)

    def estimate_link_budget(
        self, frequency, bandwidth, environment, modulation_and_coding_lut):
        """
        Takes propagation parameters and calculates capacity.

        """
        results = []

        for receiver in self.receivers.values():

            closest_transmitters = self.find_closest_available_transmitters(
                receiver
            )

            #add function here to check if closest cell is available for use?

            path_loss = self.calculate_path_loss(
                closest_transmitters[0], receiver, frequency, environment
            )
            
            received_power = self.calc_received_power(
                closest_transmitters[0], receiver, path_loss
            )

            interference = self.calculate_interference(
                closest_transmitters, receiver, frequency, environment)
            
            noise = self.calculate_noise(
                bandwidth
            )

            sinr = self.calculate_sinr(
                received_power, interference, noise
            )

            spectral_efficiency = self.modulation_scheme_and_coding_rate(
                sinr, modulation_and_coding_lut
            )

            estimated_capacity = self.link_budget_capacity(
                bandwidth, spectral_efficiency
            )
            
            data = {'sinr': sinr, 'capacity_mbps': estimated_capacity}

            results.append(data)

        return results

    def find_closest_available_transmitters(self, receiver):
        """
        Returns a list of all transmitters, ranked based on proximity
        to the receiver.

        """
        idx = index.Index()

        for transmitter in self.transmitters.values():
            idx.insert(0, Point(transmitter.coordinates).bounds, transmitter)

        number_of_transmitters = len(self.transmitters.values())

        all_closest_transmitters =  list(
            idx.nearest(
                Point(receiver.coordinates).bounds,
                number_of_transmitters, objects='raw')
                )

        return all_closest_transmitters

    def calculate_path_loss(self, closest_transmitter,
        receiver, frequency, environment):

        # for area in self.area.values():
        #     local_authority_ids = area.local_authority_ids

        x2_receiver = receiver.coordinates[0]
        y2_receiver = receiver.coordinates[1]

        x1_transmitter, y1_transmitter = transform_coordinates(
            Proj(init='epsg:27700'), Proj(init='epsg:4326'),
            closest_transmitter.coordinates[0],
            closest_transmitter.coordinates[1],
            )

        x2_receiver, y2_receiver = transform_coordinates(
            Proj(init='epsg:27700'), Proj(init='epsg:4326'),
            receiver.coordinates[0],
            receiver.coordinates[1],
            )

        Geo = Geodesic.WGS84

        i_strt_distance = Geo.Inverse(
            y1_transmitter, x1_transmitter,  y2_receiver, x2_receiver
            )

        interference_strt_distance = round(i_strt_distance['s12'],0)

        ant_height = 20 #ant_height = closest_transmitter.ant_height
        ant_type =  'macro' #ant_type = closest_transmitter.ant_type

        # type_of_sight, building_height, street_width = built_environment_module(
        # transmitter_geom, receiver_geom
        #

        type_of_sight = randomly_select_los()
        # if interference_strt_distance < 500 :
        #     type_of_sight = find_line_of_sight(
        #     x1_transmitter, y1_transmitter, x2_receiver, y2_receiver, local_authority_ids
        #     )
        # else:
        #     type_of_sight = 'nlos'

        building_height = 20
        street_width = 20
        above_roof = 0
        location = receiver.indoor

        path_loss = path_loss_calculator(
            frequency,
            interference_strt_distance,
            ant_height,
            ant_type,
            building_height,
            street_width,
            environment,
            type_of_sight,
            receiver.ue_height,
            above_roof,
            location
            )

        return path_loss

    def calc_received_power(self, transmitter, receiver, path_loss):
        """
        Calculate received power based on transmitter and receiver
        characteristcs, and path loss.

        Equivalent Isotropically Radiated Power (EIRP) = Power + Gain - Losses

        """
        #calculate Equivalent Isotropically Radiated Power (EIRP)
        eirp = float(transmitter.power) + \
            float(transmitter.gain) - \
            float(transmitter.losses)

        received_power = eirp - \
            path_loss - \
            receiver.misc_losses + \
            receiver.gain - \
            receiver.losses 
        # print('received power is {}'.format(received_power))
        return received_power

    def calculate_interference(
        self, closest_transmitters, receiver, frequency, environment):
        """
        Calculate interference from other cells.

        closest_transmitters contains all transmitters, ranked based
        on distance, meaning we need to select cells 1-3 (as cell 0
        is the actual cell in use)

        """
        three_closest_transmitters = closest_transmitters[1:4]

        interference = []

        x1_receiver, y1_receiver = transform_coordinates(
            Proj(init='epsg:27700'),
            Proj(init='epsg:4326'),
            receiver.coordinates[0],
            receiver.coordinates[1]
            )

        #calculate interference from other power sources
        for interference_transmitter in three_closest_transmitters:

            #get distance
            x2_interference = interference_transmitter.coordinates[0]
            y2_interference = interference_transmitter.coordinates[1]

            x2_interference, y2_interference = transform_coordinates(
                Proj(init='epsg:27700'),
                Proj(init='epsg:4326'),
                interference_transmitter.coordinates[0],
                interference_transmitter.coordinates[1]
                )

            Geo = Geodesic.WGS84

            i_strt_distance = Geo.Inverse(
                y2_interference,
                x2_interference,
                y1_receiver,
                x1_receiver,
                )

            interference_strt_distance = int(
                round(i_strt_distance['s12'], 0)
                )

            ant_height = 20
            ant_type =  'macro'
            building_height = 20
            street_width = 20
            type_of_sight = randomly_select_los()
            above_roof = 0
            indoor = receiver.indoor

            path_loss = path_loss_calculator(
                frequency,
                interference_strt_distance,
                ant_height,
                ant_type,
                building_height,
                street_width,
                environment,
                type_of_sight,
                receiver.ue_height,
                above_roof,
                indoor,
                )
            #print('path loss of {} is {}'.format(interference_transmitter.id, path_loss))
            #calc interference from other cells
            received_interference = self.calc_received_power(
                interference_transmitter,
                receiver,
                path_loss
                )

            #add cell interference to list
            interference.append(received_interference)

        return interference

    def calculate_noise(self, bandwidth):
        #TODO
        """
        Terminal noise can be calculated as:

        “K (Boltzmann constant) x T (290K) x bandwidth”.

        The bandwidth depends on bit rate, which defines the number of resource blocks.
        We assume 50 resource blocks, equal 9 MHz, transmission for 1 Mbps downlink.

        Thermal noise (dBm) -118.4 = k(Boltzmann) * T(290K)* B(360kHz)

        """
        k = 1
        T = 15
        B = bandwidth

        resource_blocks = [
            # Bandwidth (MHz), Resource Blocks, Subcarriers (downlink), Subcarriers (uplink)
            (1.4, 6, 73, 72),
            (3, 15,	181, 180),
            (5, 25,	301, 300),
            (10, 50, 601, 600),
            (15, 75, 901, 900),
            (20, 100, 1201, 1200),
        ]
        #fake_noise = k*T*B

        noise = -104.5

        return noise

    def calculate_sinr(self, received_power, interference, noise):
        """
        Calculate the Signal-to-Interference-plus-Noise-Ration (SINR).

        TODO: convert interference values into Watts, then sum, then
        convert into dBm.

        """
        # sum_of_interference = sum(interference)

        interference_values = []
        for value in interference:
            interim_value = value/10
            output_value = 10**interim_value            
            interference_values.append(output_value)

        sum_of_interference = 10*np.log10(sum(interference_values))

        sinr = received_power / (sum_of_interference + noise)
        # print('received power is {}'.format(received_power))
        # print('interference is {}'.format(sum(interference)))
        # print('noise is {}'.format(noise))

        # print(sinr)
        return round(sinr, 2)

    def modulation_scheme_and_coding_rate(
        self, sinr, modulation_and_coding_lut):
        """
        Uses the SINR to allocate a modulation scheme and affliated
        coding rate.

        """
        spectral_efficiency = 0

        for lower, upper in pairwise(modulation_and_coding_lut):
            lower_sinr = lower[4]
            upper_sinr = upper[4]

            if sinr >= lower_sinr and sinr < upper_sinr:
                spectral_efficiency = lower[3]
                break

        return spectral_efficiency

    def link_budget_capacity(self, bandwidth, spectral_efficiency):
        """
        Estimate wireless link capacity (Mbps) based on bandwidth and
        receiver signal.

        capacity (Mbps) = bandwidth (MHz) + log2*(1+SINR[dB])

        """
        #estimated_capacity = round(bandwidth*np.log2(1+sinr), 2)
        bandwidth_in_hertz = bandwidth*1000000
        
        link_budget_capacity = bandwidth_in_hertz*spectral_efficiency
        link_budget_capacity_mbps = link_budget_capacity / 1000000 
        
        return link_budget_capacity_mbps

    def transmitter_density(self):
        """
        Calculate transmitter density per square kilometer (km^2)

        Returns
        -------
        obj
            Sum of transmitters

        Notes
        -----
        Function returns `0` when no transmitters are configered to the area.

        """
        if not self.transmitters:
            return 0

        area_geometry = ([(d.geometry) for d in self.area.values()][0])

        idx = index.Index()

        for transmitter in self.transmitters.values():
            idx.insert(0, Point(transmitter.coordinates).bounds, transmitter)

        transmitters_in_area = []

        for n in idx.intersection(shape(area_geometry).bounds, objects=True):
            point = Point(n.object.coordinates)
            if shape(area_geometry).contains(point):
                transmitters_in_area.append(n.object)

        postcode_sector_area = (
            [round(a.area) for a in self.area.values()]
            )[0]

        transmitter_density = (
            len(transmitters_in_area) / (postcode_sector_area/1000000)
            )

        return transmitter_density

    def average_link_budget_capacity(self):
        """
        Estimate the average receiver capacity.

        """



    def receiver_density(self):
        """Calculate receiver density per square kilometer (km^2)

        Returns
        -------
        obj
            Sum of receiver

        Notes
        -----
        Function returns `0` when no receivers are configered to the area.
        """
        if not self.receivers:
            return 0

        postcode_sector_area = (
            [round(a.area) for a in self.area.values()]
            )[0]

        receiver_density = (
            len(self.receivers) / (postcode_sector_area/1000000)
            )

        return receiver_density

class Area(object):

    def __init__(self, data):
        #id and geographic info
        self.id = data['properties']['postcode']
        self.local_authority_ids =  data['properties']['local_authority_ids']
        self.geometry = data['geometry']
        self.coordinates = data['geometry']['coordinates']
        self.area = self._calculate_area(data)
        #connections
        self._transmitters = {}
        self._receivers = {}

    def _calculate_area(self, data):
        polygon = shape(data['geometry'])
        area = polygon.area
        return area

    def add_transmitter(self, transmitter):
        self._transmitters[transmitter.id] = transmitter

    def add_receiver(self, receiver):
        self._receivers[receiver.id] = receiver

class Transmitter(object):

    def __init__(self, data):
        #id and geographic info
        self.id = data['properties']['sitengr']
        self.coordinates = data['geometry']['coordinates']
        self.geometry = data['geometry']
        #antenna properties
        self.ant_type = 'macro'
        self.ant_height = 20
        self.power = 40
        self.gain = 20
        self.losses = 2

    def __repr__(self):
        return "<Transmitter id:{}>".format(self.id)

class Receiver(object):

    def __init__(self, data):
        #id and geographic info
        self.id = data['properties']['ue_id']
        #self.transmitter_id = data['properties']['sitengr']
        self.coordinates = data['geometry']["coordinates"]
        #parameters
        self.misc_losses = data['properties']['misc_losses']
        self.gain = data['properties']['gain']
        self.losses = data['properties']['losses']
        self.ue_height = 1.5
        self.indoor = data['properties']['indoor']

    def __repr__(self):
        return "<Receiver id:{}>".format(self.id)

def randomly_select_los():

    np.random.seed(42)
    number = round(np.random.rand(1,1)[0][0], 2)
    if number > 0.5:
        los = 'los'
    else:
        los = 'nlos'

    return los

def transform_coordinates(old_proj, new_proj, x, y):

    new_x, new_y = transform(old_proj, new_proj, x, y)

    return new_x, new_y

def obtain_thresholdold_value(results, percentile):
    """Get the threshold capacity based on a given percentile.
    """
    threshold_capacity_value = []

    for capacity_value in results:
        threshold_capacity_value.append(capacity_value['capacity_mbps'])

    return np.percentile(threshold_capacity_value, percentile)

def pairwise(iterable):
    """Return iterable of 2-tuples in a sliding window

    Parameters
    ----------
    iterable: list
        Sliding window

    Returns
    -------
    list of tuple
        Iterable of 2-tuples

    Example
    -------
        >>> list(pairwise([1,2,3,4]))
            [(1,2),(2,3),(3,4)]
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

def write_results(results, frequency, bandwidth, t_density,
    r_density, postcode_sector_name):

    suffix = 'freq_{}_bandwidth_{}_density_{}'.format(
        frequency, bandwidth, t_density
        )

    directory = os.path.join(DATA_RESULTS, postcode_sector_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = '{}.csv'.format(suffix)
    directory = os.path.join(directory, filename)

    if not os.path.exists(directory):
        results_file = open(directory, 'w', newline='')
        results_writer = csv.writer(results_file)
        results_writer.writerow(
            ('frequency','bandwidth','t_density','r_density',
            'sinr','throughput')
            )
    else:
        results_file = open(directory, 'a', newline='')
        results_writer = csv.writer(results_file)

    # output and report results for this timestep
    for result in results:
        # Output metrics
        results_writer.writerow(
            (frequency,
            bandwidth,
            t_density,
            r_density,
            result['sinr'],
            result['estimated_capacity'])
            )

    results_file.close()

def write_lookup_table(threshold_value, operator, technology, frequency,
    bandwidth, t_density, postcode_sector_name):

    suffix = 'lookup_table_{}'.format(postcode_sector_name)

    directory = os.path.join(DATA_RESULTS, postcode_sector_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = '{}.csv'.format(suffix)
    directory = os.path.join(directory, filename)

    if not os.path.exists(directory):
        lut_file = open(directory, 'w', newline='')
        lut_writer = csv.writer(lut_file)
        lut_writer.writerow(
            ('environment', 'operator', 'technology', 'frequency',
            'bandwidth','t_density','throughput'))
    else:
        lut_file = open(directory, 'a', newline='')
        lut_writer = csv.writer(lut_file)

    environment = 'urban'
    # output and report results for this timestep
    lut_writer.writerow(
        (environment,
        operator,
        technology,
        frequency,
        bandwidth,
        t_density,
        threshold_value)
        )

    lut_file.close()

def write_shapefile(data, postcode_sector_name, filename):

    # Translate props to Fiona sink schema
    prop_schema = []
    for name, value in data[0]['properties'].items():
        fiona_prop_type = next((
            fiona_type for fiona_type, python_type in \
                fiona.FIELD_TYPES_MAP.items() if \
                python_type == type(value)), None
            )

        prop_schema.append((name, fiona_prop_type))

    sink_driver = 'ESRI Shapefile'
    sink_crs = {'init': 'epsg:27700'}
    sink_schema = {
        'geometry': data[0]['geometry']['type'],
        'properties': OrderedDict(prop_schema)
    }

    # Create path
    directory = os.path.join(DATA_RESULTS, postcode_sector_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    print(os.path.join(directory, filename))
    # Write all elements to output file
    with fiona.open(
        os.path.join(directory, filename), 'w',
        driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        for feature in data:
            sink.write(feature)

def format_data(existing_data, new_data, frequency, bandwidth,
    postcode_sector_name):

    for datum in new_data:
        existing_data.append({
            'frequency': frequency,
            'bandwidth': bandwidth,
            'sinr': datum['sinr'],
            'capacity': datum['estimated_capacity']
        })

    return existing_data

#####################################
# VISUALISE NETWORK STATS
#####################################

def plot_data(data, frequency, bandwidth, postcode_sector_name):

    sinr = []
    capacity = []

    for datum in data:
        sinr.append(datum['sinr'])
        capacity.append(datum['estimated_capacity'])

    plt.figure()
    plt.scatter(sinr, capacity)

    plt.xlabel("SINR")
    plt.ylabel("Capacity (Mbps)")
    plt.legend(loc='upper left')

    plt.axis((0,30,0,150))

    # Create path
    directory = os.path.join(DATA_RESULTS, postcode_sector_name, 'plots')
    if not os.path.exists(directory):
        os.makedirs(directory)

    plt.savefig(os.path.join(
        directory, 'freq_{}_bw_{}.png'.format(frequency, bandwidth)
        ))

def joint_plot(data, postcode_sector_name):

    sinr_700_10 = []
    sinr_800_10 = []
    sinr_900_10 = []
    sinr_1800_10 = []
    sinr_2100_10 = []
    sinr_2600_10 = []
    capacity_700_10 = []
    capacity_800_10 = []
    capacity_900_10 = []
    capacity_1800_10 = []
    capacity_2100_10 = []
    capacity_2600_10 = []

    for datum in data:
        if datum['frequency'] == 0.7 and datum['bandwidth'] == 10:
            sinr_700_10.append(datum['sinr'])
            capacity_700_10.append(datum['capacity'])
        if datum['frequency'] == 0.8 and datum['bandwidth'] == 10:
            sinr_800_10.append(datum['sinr'])
            capacity_800_10.append(datum['capacity'])
        if datum['frequency'] == 0.9 and datum['bandwidth'] == 10:
            sinr_900_10.append(datum['sinr'])
            capacity_900_10.append(datum['capacity'])
        if datum['frequency'] == 1.8 and datum['bandwidth'] == 10:
            sinr_1800_10.append(datum['sinr'])
            capacity_1800_10.append(datum['capacity'])
        if datum['frequency'] == 2.1 and datum['bandwidth'] == 10:
            sinr_2100_10.append(datum['sinr'])
            capacity_2100_10.append(datum['capacity'])
        if datum['frequency'] == 2.6 and datum['bandwidth'] == 10:
            sinr_2600_10.append(datum['sinr'])
            capacity_2600_10.append(datum['capacity'])

    #setup and plot
    plt.scatter(sinr_700_10, capacity_700_10, label='10@700GHz ')
    plt.scatter(sinr_800_10, capacity_800_10, label='10@800GHz')
    plt.scatter(sinr_900_10, capacity_900_10, label='10@900GHz')
    plt.scatter(sinr_1800_10, capacity_1800_10, label='10@1800GHz')
    plt.scatter(sinr_2100_10, capacity_2100_10, label='10@2100GHz')
    plt.scatter(sinr_2600_10, capacity_2600_10, label='10@2600GHz')

    plt.xlabel("SINR")
    plt.ylabel("Capacity (Mbps)")
    plt.legend(loc='upper left')

    # Create path
    directory = os.path.join(DATA_RESULTS, postcode_sector_name, 'plots')
    if not os.path.exists(directory):
        os.makedirs(directory)

    plt.savefig(os.path.join(directory, 'panel_plot.png'))

#####################################
# APPLY METHODS
#####################################

SPECTRUM_PORTFOLIO = [
    ('O2 Telefonica', 'FDD DL', 0.7, 10),
    ('O2 Telefonica', 'FDD DL', 0.8, 10),
    ('O2 Telefonica', 'FDD DL', 0.9, 17.4),
    ('O2 Telefonica', 'FDD DL', 1.8, 5.8),
    ('O2 Telefonica', 'FDD DL', 2.1, 10),
    ('O2 Telefonica', 'FDD DL', 3.5, 100),
    ('Vodafone', 'FDD DL', 0.7, 10),
    ('Vodafone', 'FDD DL', 0.8, 10),
    ('Vodafone', 'FDD DL', 0.9, 17.4),
    ('Vodafone', 'FDD DL', 1.5, 20),
    ('Vodafone', 'FDD DL', 1.8, 5.8),
    ('Vodafone', 'FDD DL', 2.1, 14.8),
    ('Vodafone', 'FDD DL', 2.6, 20),
    ('Vodafone', 'FDD DL', 3.5, 100),
]

MODULATION_AND_CODING_LUT =[
    # CQI Index	Modulation	Coding rate
    # Spectral efficiency (bps/Hz) SINR estimate (dB)
    (1,	'QPSK',	0.0762,	0.1523, -6.7),
    (2,	'QPSK',	0.1172,	0.2344, -4.7),
    (3,	'QPSK',	0.1885,	0.377, -2.3),
    (4,	'QPSK',	0.3008,	0.6016, 0.2),
    (5,	'QPSK',	0.4385,	0.877, 2.4),
    (6,	'QPSK',	0.5879,	1.1758,	4.3),
    (7,	'16QAM', 0.3691, 1.4766, 5.9),
    (8,	'16QAM', 0.4785, 1.9141, 8.1),
    (9,	'16QAM', 0.6016, 2.4063, 10.3),
    (10, '64QAM', 0.4551, 2.7305, 11.7),
    (11, '64QAM', 0.5537, 3.3223, 14.1),
    (12, '64QAM', 0.6504, 3.9023, 16.3),
    (13, '64QAM', 0.7539, 4.5234, 18.7),
    (14, '64QAM', 0.8525, 5.1152, 21),
    (15, '64QAM', 0.9258, 5.5547, 22.7),
]

if __name__ == "__main__":

    SYSTEM_INPUT = os.path.join('data', 'raw')

    if len(sys.argv) != 2:
        print("Error: no postcode sector provided")
        #print("Usage: {} <postcode>".format(os.path.basename(__file__)))
        exit(-1)

    print('Process ' + sys.argv[1])
    postcode_sector_name = sys.argv[1]
    postcode_sector_abbr = sys.argv[1].replace('postcode_sector_', '')

    #get postcode sector
    geojson_postcode_sector = read_postcode_sector(postcode_sector_name)

    #get local authority district
    local_authority_ids = get_local_authority_ids(geojson_postcode_sector)

    #add lad information to postcode sectors
    geojson_postcode_sector['properties']['local_authority_ids'] = local_authority_ids

    #get the probability for inside versus outside calls
    postcode_sector_lut = import_area_lut(
        postcode_sector_name, local_authority_ids
        )

    #get propagation environment (urban, suburban or rural)
    environment = determine_environment(postcode_sector_lut)

    #get list of transmitters
    TRANSMITTERS = get_transmitters(geojson_postcode_sector)
    # {'operator': 'O2', 'sitengr': 'TL4491058710', 'ant_height': '5',
    # 'tech': 'GSM', 'freq': '900', 'type': '3.2', 'power': 30,
    # 'gain': 18, 'losses': 2}

    #generate receivers
    RECEIVERS = generate_receivers(
        geojson_postcode_sector, postcode_sector_lut, 1000
        )

    joint_plot_data = []

    idx = 0
    t_density = 0
    percentile = 95

    for operator, technology, frequency, bandwidth in SPECTRUM_PORTFOLIO:

        while t_density < 100:

            print("Running {} GHz with {} MHz bandwidth".format(
                frequency, bandwidth
                ))

            if idx == 0:

                #load system model with data
                MANAGER = NetworkManager(
                    geojson_postcode_sector, TRANSMITTERS, RECEIVERS
                    )

                #calculate transmitter density
                t_density = MANAGER.transmitter_density()

            else:

                NEW_TRANSMITTERS = find_and_deploy_new_transmitter(
                    MANAGER.transmitters, idx, geojson_postcode_sector
                    )

                MANAGER.build_new_assets(
                    NEW_TRANSMITTERS, geojson_postcode_sector
                    )

            results = MANAGER.estimate_link_budget(
                frequency, bandwidth, environment, MODULATION_AND_CODING_LUT
                )

            #calculate transmitter density
            t_density = MANAGER.transmitter_density()
            print('t_density is {}'.format(t_density))

            #calculate transmitter density
            r_density = MANAGER.receiver_density()

            # write_results(results, frequency, bandwidth, t_density,
            #     r_density, postcode_sector_name
            #     )

            #find percentile values
            threshold_value = obtain_threshold_value(results, percentile)
            print(lookup_table_results)
            #env, frequency, bandwidth, site_density, capacity
            write_lookup_table(
                threshold_value, operator, technology, frequency,
                bandwidth, t_density, postcode_sector_name
                )

            # format_data(
            # joint_plot_data, results, frequency,
            # bandwidth, postcode_sector_name
            # )

            idx += 1

#     # print('write buildings')
#     # write_shapefile(buildings,  postcode_sector_name, 'buildings.shp')

#     # print('write receivers')
#     # write_shapefile(RECEIVERS,  postcode_sector_name, 'receivers.shp')

#     print('write transmitters')
#     write_shapefile(TRANSMITTERS,  postcode_sector_name, 'transmitters.shp')

#     print('write boundary')
#     geojson_postcode_sector_list = []
#     geojson_postcode_sector_list.append(geojson_postcode_sector)
#     write_shapefile(
#         geojson_postcode_sector_list,  postcode_sector_name, '_boundary.shp'
#         )