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

from collections import OrderedDict

from digital_comms.mobile_network.path_loss_module import path_loss_calculator

# from built_env_module import find_line_of_sight

CONFIG = configparser.ConfigParser()
CONFIG.read(
    os.path.join(os.path.dirname(__file__), '..',  '..', 'scripts','script_config.ini')
)
BASE_PATH = CONFIG['file_locations']['base_path']

#data locations
DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_RESULTS = os.path.join(BASE_PATH, '..' ,'results', 'system_simulator')

def read_postcode_sector(postcode_sector):
    postcode_area = ''.join([i for i in postcode_sector[:2] if not i.isdigit()])
    with fiona.open(
        os.path.join(DATA_RAW, 'd_shapes', 'postcode_sectors', postcode_area + '.shp'), 'r') \
        as source:

        return [
            sector for sector in source \
            if sector['properties']['postcode'].replace(" ", "") == postcode_sector \
        ][0]

def get_local_authority_ids(postcode_sector):

    with fiona.open(os.path.join(
        DATA_RAW, 'd_shapes','lad_uk_2016-12', 'lad_uk_2016-12.shp'), 'r') as source:
        postcode_sector_geom = shape(postcode_sector['geometry'])
        return [
            lad['properties']['name'] for lad in source \
            if postcode_sector_geom.intersection(shape(lad['geometry']))
            ]

def read_building_polygons(postcode_sector, lad_ids):
    """
    This function imports the building polygons from
    the relevant local authority lookup tables.

    """
    prepared_area = prep(shape(postcode_sector['geometry']))

    def premises():
        i = 0
        for lad_id in lad_ids:
            directory = os.path.join(DATA_RAW, 'e_dem_and_buildings', 'prems_by_lad', lad_id)
            pathlist = glob.iglob(directory + '/*.csv', recursive=True)
            for path in pathlist:
                with open(path, 'r') as system_file:
                    reader = csv.DictReader(system_file)
                    next(reader)
                    for line in reader:
                        geom = loads(line['geom'])
                        geom_point = geom.representative_point()
                        feature = {
                            'type': 'Feature',
                            'geometry': mapping(geom),
                            'representative_point': geom_point,
                            'properties':{
                                'floor_area': line['floor_area'],
                                'height_toroofbase': line['height_toroofbase'],
                                'height_torooftop': line['height_torooftop'],
                                'number_of_floors': line['number_of_floors'],
                                'footprint_area': line['footprint_area'],
                            }
                        }
                        yield (i, geom_point.bounds, feature)

    idx = index.Index(premises())

    output = []

    for n in idx.intersection((shape(postcode_sector['geometry']).bounds), objects=True):
        point = n.object['representative_point']
        if prepared_area.contains(point):
            #del n.object['representative_point']
            output.append(n.object)

    return output

def calculate_indoor_outdoor_ratio(postcode_sector, buildings):
    """
    Gets the percentage probability of a user being either indoor or outdoor.

    Note: the sum of total_inside_floor_area and total_outside_area will not sum up to
    the postcode_sector_area, as total_inside_floor_area takes into account all floors
    in a building, not just the building footprint.

    Parameters
    ----------
    footprint_area : float
        Estimate of a building's geographical area.
    floor_area : float
        Estimate of a building's indoor area across all floors.

    """
    #start with total building footprint area
    building_footprint = 0
    for building in buildings:
        building_footprint += building['properties']['footprint_area']

    #start with gross indoor area
    total_inside_floor_area = 0
    for building in buildings:
        total_inside_floor_area += building['properties']['floor_area']

    #now calculate gross outside area
    geom = shape(postcode_sector['geometry'])
    postcode_sector_area = geom.area
    total_outside_area = postcode_sector_area - building_footprint

    #get total potential usage area (note: greater than postcode sector area)
    total_usage_area = total_outside_area + total_inside_floor_area

    #calculate percentage probability between indoor/outdoor
    indoor_probability = total_inside_floor_area/total_usage_area*100
    outdoor_probability = total_outside_area/total_usage_area*100

    return (indoor_probability, outdoor_probability)

def get_transmitters(postcode_sector):

    transmitters = []

    geom = shape(postcode_sector['geometry'])
    geom_length = geom.length
    geom_buffer = geom.buffer(geom_length/10)
    geom_box = geom_buffer.bounds

    with open(
        os.path.join(DATA_RAW, 'b_mobile_model', 'sitefinder', 'sitefinder.csv'), 'r'
        ) as system_file:
            reader = csv.reader(system_file)
            next(reader)
            for line in reader:
                if (
                    geom_box[0] <= float(line[0]) and
                    geom_box[1] <= float(line[1]) and
                    geom_box[2] >= float(line[0]) and
                    geom_box[3] >= float(line[1])
                    ):
                    transmitters.append({
                        'type': "Feature",
                        'geometry': {
                            "type": "Point",
                            "coordinates": [float(line[0]), float(line[1])]
                        },
                        'properties': {
                            "operator": line[2],
                            "sitengr": line[4],
                            "ant_height": line[5],
                            "tech": line[6],
                            "freq": line[7],
                            "type": line[9],
                            "power": 30,
                            "gain": 18,
                            "losses": 2,
                        }
                    })

    return transmitters

def generate_receivers(postcode_sector, quantity):

    coordinates = []

    geom = shape(postcode_sector['geometry'])
    geom_box = geom.bounds

    minx = geom_box[0]
    miny = geom_box[1]
    maxx = geom_box[2]
    maxy = geom_box[3]

    receivers = []

    id_number = 0
    np.random.seed(42)

    while len(receivers) < quantity:

        x_coord = np.random.uniform(low=minx, high=maxx, size=1)
        y_coord = np.random.uniform(low=miny, high=maxy, size=1)

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
                }
            })
            id_number += 1
        else:
            pass

    return receivers

def find_and_deploy_new_transmitter(
    existing_transmitters, iteration_number, geojson_postcode_sector):

    existing_transmitter_coordinates = []
    for existing_transmitter in existing_transmitters.values():
        existing_transmitter_coordinates.append(existing_transmitter.coordinates)

    #convert to numpy array
    existing_transmitter_coordinates = np.array(existing_transmitter_coordinates)

    #get delaunay grid
    tri = Delaunay(existing_transmitter_coordinates)

    #get coordinates from gri
    coord_groups = [tri.points[x] for x in tri.simplices]

    #convert coordinate groups to polygons
    polygons = [Polygon(x) for x in coord_groups]

    #sort based on area
    polygons = sorted(polygons, key=lambda x: x.area, reverse=True)

    geom = shape(geojson_postcode_sector['geometry'])

    for new_site_area in polygons:

        #get the centroid from the largest area
        centroid = new_site_area.centroid

        if geom.contains(centroid):
            break
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

    def estimate_link_budget(self, frequency, bandwidth):
        """
        Takes propagation parameters and calculates capacity.

        """
        results = []

        for receiver in self.receivers.values():

            closest_transmitters = self.find_closest_available_transmitters(
                receiver
            )

            path_loss = self.calculate_path_loss(
                closest_transmitters[0], receiver, frequency
            )

            received_power = self.calc_received_power(
                closest_transmitters[0], receiver, path_loss
            )

            interference = self.calculate_interference(
                closest_transmitters, receiver, frequency)

            noise = self.calculate_noise(
                bandwidth
            )

            sinr = self.calculate_sinr(
                received_power, interference, noise
            )

            estimated_capacity = self.estimate_capacity(
                bandwidth, sinr
            )

            data = {'sinr': sinr, 'estimated_capacity': estimated_capacity}

            results.append(data)

        return results

    def find_closest_available_transmitters(self, receiver):
        """
        Returns a list of all transmitters, ranked based on proximity to the receiver.

        """
        idx = index.Index()

        for transmitter in self.transmitters.values():
            idx.insert(0, Point(transmitter.coordinates).bounds, transmitter)

        number_of_transmitters = len(self.transmitters.values())

        all_closest_transmitters =  list(
            idx.nearest(
                Point(receiver.coordinates).bounds, number_of_transmitters, objects='raw'))

        return all_closest_transmitters

    def calculate_path_loss(self, closest_transmitters, receiver, frequency):

        x2_receiver = receiver.coordinates[0]
        y2_receiver = receiver.coordinates[1]

        x1_transmitter, y1_transmitter = transform_coordinates(
            Proj(init='epsg:27700'), Proj(init='epsg:4326'),
            closest_transmitters.coordinates[0],
            closest_transmitters.coordinates[1],
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

        ant_height = 20
        ant_type =  'macro'
        settlement_type = 'urban'

        #type_of_sight, building_height, street_width = built_environment_module(
        # transmitter_geom, receiver_geom
        # )
        #type_of_sight = find_line_of_sight(
        # x1_transmitter, y1_transmitter, x2_receiver, y2_receiver
        # )

        type_of_sight = randomly_select_los()

        building_height = 20
        street_width = 20
        above_roof = 0

        path_loss = path_loss_calculator(
            frequency,
            interference_strt_distance,
            ant_height,
            ant_type,
            building_height,
            street_width,
            settlement_type,
            type_of_sight,
            receiver.ue_height,
            above_roof
            )

        return path_loss

    def calc_received_power(self, transmitter, receiver, path_loss):
        """
        Calculate received power based on transmitter and receiver characteristcs,
        and path loss.

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
            receiver.losses \

        return received_power

    def calculate_interference(self, closest_transmitters, receiver, frequency):

        """
        calculate interference from other cells.

        closest_transmitters contains all transmitters, ranked based on distance, meaning
        we need to select cells 1-3 (as cell 0 is the actual cell in use)
        """

        three_closest_transmitters = closest_transmitters[1:4]

        interference = []

        x1_receiver, y1_receiver = transform_coordinates(Proj(init='epsg:27700'),
                                                        Proj(init='epsg:4326'),
                                                        receiver.coordinates[0],
                                                        receiver.coordinates[1])

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

            interference_strt_distance = int(round(i_strt_distance['s12'], 0))

            ant_height = 20
            ant_type =  'macro'
            building_height = 20
            street_width = 20
            settlement_type = 'urban'
            type_of_sight = randomly_select_los()
            above_roof = 0

            path_loss = path_loss_calculator(
                frequency,
                interference_strt_distance,
                ant_height,
                ant_type,
                building_height,
                street_width,
                settlement_type,
                type_of_sight,
                receiver.ue_height,
                above_roof
                )

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
        Calculate receiver noise (N  = k T B), where k is Boltzmann's constant,
        T is temperatrue in K and B is bandwidth in use.
        """
        k = 1
        T = 15
        B = bandwidth

        #fake_noise = k*T*B

        noise = 5

        return noise

    def calculate_sinr(self, received_power, interference, noise):
        """
        Calculate the Signal-to-Interference-plus-Noise-Ration (SINR).
        """
        sinr = round(received_power / sum(interference) + noise, 1)

        return sinr

    def estimate_capacity(self,bandwidth, sinr):
        """
        Estimate wireless link capacity (Mbps) based on bandwidth and receiver signal.
        capacity (Mbps) = bandwidth (MHz) + log2*(1+SINR[dB])
        """
        estimated_capacity = round(bandwidth*np.log2(1+sinr), 2)

        return estimated_capacity

    def transmitter_density(self):
        """Calculate transmitter density per square kilometer (km^2)

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

        postcode_sector_area = ([round(a.area) for a in self.area.values()])[0]

        transmitter_density = float(round(
            len(self.transmitters) / (postcode_sector_area/1000000), 5
        ))

        # summed_transmitters = len(
        #     self.transmitters / postcode_sector_area
        # )

        return transmitter_density

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

        summed_receivers = len(
            self.receivers
        )

        return summed_receivers

class Area(object):

    def __init__(self, data):
        #id and geographic info
        self.id = data['properties']["postcode"]
        self.coordinates = data['geometry']["coordinates"]
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
        self.id = data['properties']["sitengr"]
        self.coordinates = data['geometry']["coordinates"]
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

def generate_lut_results(results, percentile):
    """Get the threshold capacity based on a given percentile.
    """
    threshold_capacity_value = []

    for capacity_value in results:
        threshold_capacity_value.append(capacity_value['estimated_capacity'])

    return np.percentile(threshold_capacity_value, percentile)

def write_results(results, frequency, bandwidth, t_density, r_density, postcode_sector_name):

    suffix = 'freq_{}_bandwidth_{}_density_{}'.format(frequency, bandwidth, t_density)

    directory = os.path.join(DATA_RESULTS, postcode_sector_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = '{}.csv'.format(suffix)
    directory = os.path.join(directory, filename)

    if not os.path.exists(directory):
        results_file = open(directory, 'w', newline='')
        results_writer = csv.writer(results_file)
        results_writer.writerow(
            ('frequency','bandwidth','t_density','r_density','sinr','throughput'))
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
            fiona_type for fiona_type, python_type in fiona.FIELD_TYPES_MAP.items() if \
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
        [sink.write(feature) for feature in data]

def format_data(existing_data, new_data, frequency, bandwidth, postcode_sector_name):

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

    plt.savefig(os.path.join(directory, 'freq_{}_bw_{}.png'.format(frequency, bandwidth)))

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

    #import buildings in postcode sector
    buildings = read_building_polygons(geojson_postcode_sector, local_authority_ids)

    #get the probability for inside versus outside calls
    indoor_outdoor_probability = calculate_indoor_outdoor_ratio(geojson_postcode_sector, buildings)

    #get list of transmitters
    TRANSMITTERS = get_transmitters(geojson_postcode_sector)
    #{'operator': 'O2', 'sitengr': 'TL4491058710', 'ant_height': '5', 'tech': 'GSM',
    # 'freq': '900', 'type': '3.2', 'power': 30, 'gain': 18, 'losses': 2}

    #generate receivers
    RECEIVERS = generate_receivers(geojson_postcode_sector, 1000)

    joint_plot_data = []

    idx = 0
    t_density = 0
    percentile = 95

    for operator, technology, frequency, bandwidth in SPECTRUM_PORTFOLIO:

        while t_density < 100:

            print("Running {} GHz with {} MHz bandwidth".format(frequency, bandwidth))
            if idx == 0:

                #load system model with data
                MANAGER = NetworkManager(geojson_postcode_sector, TRANSMITTERS, RECEIVERS)

                #calculate transmitter density
                t_density = MANAGER.transmitter_density()

            else:
                NEW_TRANSMITTERS = find_and_deploy_new_transmitter(
                    MANAGER.transmitters, idx, geojson_postcode_sector
                    )
                MANAGER.build_new_assets(NEW_TRANSMITTERS, geojson_postcode_sector)

            results = MANAGER.estimate_link_budget(frequency, bandwidth)

            #calculate transmitter density
            t_density = MANAGER.transmitter_density()
            print('t_density is {}'.format(t_density))

            #calculate transmitter density
            r_density = MANAGER.receiver_density()

            # write_results(results, frequency, bandwidth, t_density,
            #     r_density, postcode_sector_name
            #     )

            #find percentile values
            lookup_table_results = generate_lut_results(results, percentile)
            print(lookup_table_results)
            #env, frequency, bandwidth, site_density, capacity
            write_lookup_table(
                lookup_table_results, operator, technology, frequency,
                bandwidth, t_density, postcode_sector_name
                )

            # format_data(joint_plot_data, results, frequency, bandwidth, postcode_sector_name)

            idx += 1

    print('write buildings')
    write_shapefile(buildings,  postcode_sector_name, 'buildings.shp')

    print('write receivers')
    write_shapefile(RECEIVERS,  postcode_sector_name, 'receivers.shp')

    print('write transmitters')
    write_shapefile(TRANSMITTERS,  postcode_sector_name, 'transmitters.shp')

    print('write boundary')
    geojson_postcode_sector_list = []
    geojson_postcode_sector_list.append(geojson_postcode_sector)
    write_shapefile(geojson_postcode_sector_list,  postcode_sector_name, '_boundary.shp')

#####################################
# UK Spectrum Portfolio dict
#####################################

# SPECTRUM_PORTFOLIO_DICT = {
#     'O2 Telefonica': {
#         'FDD DL': {
#             '800': 10,
#             '900': 17.4,
#             '1800': 5.8,
#             '2100': 10,
#             },
#         'FDD UL': {
#             '800': 10,
#             '900': 17.4,
#             '1800': 5.8,
#             '2100': 10,
#             },
#         'TDD': {
#             '1900': 5,
#             '2300': 40,
#             '3500': 40,
#             },
#         },
#     'Vodafone': {
#         'FDD DL': {
#             '800': 10,
#             '900': 17.4,
#             '1500': 20,
#             '1800': 5.8,
#             '2100': 14.8,
#             '2600': 20,
#             },
#         'FDD UL': {
#             '800': 10,
#             '900': 17.4,
#             '1800': 5.8,
#             '2100': 14.8,
#             '2600': 20,
#             },
#         'TDD': {
#             '2600': 25,
#             '3500': 50,
#             },
#         },
#     'EE (BT)': {
#         'FDD DL': {
#             '800': 5,
#             '1800': 45,
#             '2100': 20,
#             '2600': 35,
#             },
#         'FDD UL': {
#             '800': 5,
#             '1800': 45,
#             '2100': 20,
#             '2600': 35,
#             },
#         'TDD': {
#             '1900': 10,
#             '3500': 40,
#             },
#         },
#     '3 UK (H3G)': {
#         'FDD DL': {
#             '800': 5,
#             '1500': 20,
#             '1800': 15,
#             '2100': 14.6,
#             },
#         'FDD UL': {
#             '800': 5,
#             '1800': 15,
#             '2100': 14.6,
#             },
#         'TDD': {
#             '1900': 5.4,
#             '3500': 40,
#             '3700': 80,
#             },
#         },
#     'BT': {
#         'FDD DL': {
#             '2600': 15,
#             },
#         'FDD UL': {
#             '2600': 15,
#             },
#         'TDD': {
#             '2600': 25,
#             },
#         },
# }
