"""
System-level wireless network simulator

Written by Edward Oughton
May 2019

"""
import os, sys, configparser
import csv

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

#Define global simulation parameters
ITERATIONS = 100
TX_HEIGHT_BASE = 30
TX_HEIGHT_HIGH = 40
TX_POWER = 40
TX_GAIN = 20
TX_LOSSES = 2
RX_GAIN = 4
RX_LOSSES = 4
RX_MISC_LOSSES = 4
RX_HEIGHT = 1.5
NETWORK_LOAD = 50
PERCENTILE = 95
DESIRED_TRANSMITTER_DENSITY = 10 #per km^2
SECTORISATION = 3
SYSTEM_INPUT = os.path.join('data', 'raw')

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

#set numpy seed
np.random.seed(42)


def read_postcode_sector(postcode_sector):

    with fiona.open(
        os.path.join(
            DATA_RAW, 'd_shapes', 'datashare_pcd_sectors', 'PostalSector.shp')
            , 'r') as source:

        return [
            sector for sector in source \
            if (sector['properties']['RMSect'].replace(' ', '') ==
                postcode_sector.replace(' ', ''))][0]


def get_local_authority_ids(postcode_sector):

    postcode_sector_geom = shape(postcode_sector['geometry'])

    with fiona.open(os.path.join(
        DATA_RAW, 'd_shapes','lad_uk_2016-12', 'lad_uk_2016-12.shp'),
        'r') as source:
        return [
            lad['properties']['name'] for lad in source \
            if postcode_sector_geom.intersection(shape(lad['geometry']))
            ]


def import_area_lut(postcode_sector_name, lad_ids):

    postcode_sector_name = postcode_sector_name.replace(' ', '')

    for lad in lad_ids:
        path = os.path.join(
            DATA_RAW, '..', 'intermediate', 'mobile_geotype_lut',
            lad, lad + '.csv'
            )
        with open(path, 'r') as system_file:
            reader = csv.DictReader(system_file)
            for line in reader:
                if line['postcode_sector'].replace(' ', '') == postcode_sector_name:
                    lut = {
                        'postcode_sector': line['postcode_sector'],
                        'indoor_probability': line['indoor_probability'],
                        'outdoor_probability': line['outdoor_probability'],
                        'residential_count': line['residential_count'],
                        'non_residential_count': line['non_residential_count'],
                        'estimated_population': int(float(line['residential_count'])*2.5),
                        'area': line['area'],
                    }

    return lut


def determine_environment(postcode_sector_lut):

    population_density = (
        postcode_sector_lut['estimated_population'] / float(postcode_sector_lut['area'])
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


def get_sites(postcode_sector, transmitter_type):
    """
    This function either reads in existing site data, or generates it
    from scratch.

    Parameters
    ----------
    postcode_sector : geojson
        Shape file for the postcode sector being assessed
    transmitter_type : string
        Inidcates whether 'real' or 'synthetic' data should be used.

    """
    id_number = 0

    if transmitter_type == 'real':

        sites = []

        geom = shape(postcode_sector['geometry'])
        geom_length = geom.length
        geom_buffer = geom.buffer(geom_length)
        geom_box = geom_buffer.bounds

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
                        sites.append({
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
                                "power": TX_POWER,
                                # "power_dbw": line['Powerdbw'],
                                # "max_power_dbw": line['Maxpwrdbw'],
                                # "max_power_dbm": line['Maxpwrdbm'],
                                "gain": TX_GAIN,
                                "losses": TX_LOSSES,
                            }
                        })

                        id_number += 1
                    else:
                        pass

    elif transmitter_type == 'synthetic':

        sites = []

        geom = shape(postcode_sector['geometry'])
        geom_box = geom.bounds

        minx = geom_box[0]
        miny = geom_box[1]
        maxx = geom_box[2]
        maxy = geom_box[3]


        while len(sites) < 2:

            x_coord = np.random.uniform(low=minx, high=maxx, size=1)
            y_coord = np.random.uniform(low=miny, high=maxy, size=1)

            coordinates = list(zip(x_coord, y_coord))

            postcode_sector_shape = shape(postcode_sector['geometry'])
            site = Point((x_coord, y_coord))
            if not postcode_sector_shape.contains(site):
                sites.append({
                    'type': "Feature",
                    'geometry': {
                        "type": "Point",
                        "coordinates": [coordinates[0][0],coordinates[0][1]],
                    },
                    'properties': {
                        "sitengr": 'site_id_{}'.format(id_number),
                        "ant_height": 30,
                        "tech": '4G',
                        "freq": [800, 1800, 2600],
                        "type": '3 sectored macrocell',
                        "power": TX_POWER,
                        "gain": TX_GAIN,
                        "losses": TX_LOSSES,
                    }
                })
                id_number += 1

        else:
            pass

        while len(sites) < 3:

            x_coord = np.random.uniform(low=minx, high=maxx, size=1)
            y_coord = np.random.uniform(low=miny, high=maxy, size=1)

            coordinates = list(zip(x_coord, y_coord))

            postcode_sector_shape = shape(postcode_sector['geometry'])
            site = Point((x_coord, y_coord))
            if postcode_sector_shape.contains(site):
                sites.append({
                    'type': "Feature",
                    'geometry': {
                        "type": "Point",
                        "coordinates": [coordinates[0][0],coordinates[0][1]],
                    },
                    'properties': {
                        "sitengr": 'site_id_{}'.format(id_number),
                        "ant_height": 30,
                        "tech": '4G',
                        "freq": [800, 1800, 2600],
                        "type": '3 sectored macrocell',
                        "power": TX_POWER,
                        "gain": TX_GAIN,
                        "losses": TX_LOSSES,
                    }
                })
                id_number += 1

        else:
            pass
    else:
        print('Error: Did you type an incorrect site type?')
        print('Site types must either be "real" or "synthetic"')

    return sites


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
                    "misc_losses": RX_MISC_LOSSES,
                    "gain": RX_GAIN,
                    "losses": RX_LOSSES,
                    "ue_height": float(RX_HEIGHT),
                    "indoor": (True if float(indoor_outdoor_probability) < \
                        float(indoor_probability) else False),
                }
            })
            id_number += 1

        else:
            pass

    return receivers


def find_and_deploy_new_site(
    existing_sites, new_sites, geojson_postcode_sector, idx):
    """
    Given existing site locations, try deploy a new one in the area
    which has the largest existing gap between sites.

    Parameters
    ----------
    existing_sites : List of objects
        Contains existing sites
    iteration_number : int
        The loop index, used for the providing the id for a new asset
    geojson_postcode_sector : GeoJson
        The postcode sector boundary in GeoJson format.

    """
    NEW_TRANSMITTERS = []

    for n in range(0, new_sites):

        existing_site_coordinates = []
        for existing_site in existing_sites.values():
            existing_site_coordinates.append(
                existing_site.coordinates
                )

        #convert to numpy array
        existing_site_coordinates = np.array(
            existing_site_coordinates
            )

        #get delaunay grid
        tri = Delaunay(existing_site_coordinates)

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

            random_site_location = []

            while len(random_site_location) == 0:

                x_coord = np.random.uniform(low=minx, high=maxx, size=1)
                y_coord = np.random.uniform(low=miny, high=maxy, size=1)

                receiver = Point((x_coord, y_coord))

                if geom.contains(receiver):
                    centroid = receiver.centroid
                    random_site_location.append(receiver)

                else:

                    continue

        NEW_TRANSMITTERS.append({
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [centroid.x, centroid.y]
            },
            'properties': {
                    "operator": 'unknown',
                    "sitengr": "{" + 'new' + "}{GEN" + str(idx) + '.' + str(n+1) + '}',
                    "ant_height": TX_HEIGHT_BASE,
                    "tech": 'LTE',
                    "freq": 700,
                    "type": 17,
                    "power": TX_POWER,
                    "gain": TX_GAIN,
                    "losses": TX_LOSSES,
                }
            })

    return NEW_TRANSMITTERS


class NetworkManager(object):

    def __init__(self, area, sites, receivers):

        self.area = {}
        self.sites = {}
        self.receivers = {}
        area_id = area['properties']['RMSect'].replace(' ', '')
        self.area[area_id] = Area(area)

        for site in sites:
            site_id = site['properties']["sitengr"]
            site_object = Transmitter(site)
            self.sites[site_id] = site_object

            area_containing_sites = self.area[area_id]
            area_containing_sites.add_site(site_object)

        for receiver in receivers:
            receiver_id = receiver['properties']["ue_id"]
            receiver = Receiver(receiver)
            self.receivers[receiver_id] = receiver

            area_containing_receivers = self.area[area_id]
            area_containing_receivers.add_receiver(receiver)


    def build_new_assets(self, list_of_new_assets, area_id):

        for site in list_of_new_assets:
            site_id = site['properties']["sitengr"]
            site_object = Transmitter(site)

            self.sites[site_id] = site_object

            for area_containing_sites in self.area.values():
                if area_containing_sites.id == area_id:
                    area_containing_sites.add_site(site_object)


    def estimate_link_budget(
        self, frequency, bandwidth, generation, mast_height,
        environment, modulation_and_coding_lut, network_load):
        """
        Takes propagation parameters and calculates link budget capacity.

        Parameters
        ----------
        frequency : float
            The carrier frequency for the chosen spectrum band (GHz).
        bandwidth : float
            The width of the spectrum around the carrier frequency (MHz).
        environment : string
            Either urban, suburban or rural.
        modulation_and_coding_lut : list of tuples
            A lookup table containing modulation and coding rates,
            spectral efficiencies and SINR estimates.

        Returns
        -------
        sinr : float
            The signal to noise plut interference ratio (GHz).
        capacity_mbps : float
            The estimated link budget capacity.

        """
        results = []

        for receiver in self.receivers.values():
            # print(receiver.id)
            closest_site, interfering_sites = (
                self.find_closest_available_sites(receiver)
            )
            # print('closest_site is {}'.format(closest_site))
            # print('interfering_sites is {}'.format(interfering_sites))
            path_loss = self.calculate_path_loss(
                closest_site, receiver, frequency, mast_height, environment
            )

            received_power = self.calc_received_power(
                closest_site, receiver, path_loss
            )

            interference = self.calculate_interference(
                interfering_sites, receiver, frequency, environment)

            noise = self.calculate_noise(
                bandwidth
            )

            sinr = self.calculate_sinr(
                received_power, interference, noise, network_load
            )

            spectral_efficiency = self.modulation_scheme_and_coding_rate(
                sinr, generation, modulation_and_coding_lut
            )

            estimated_capacity = self.link_budget_capacity(
                bandwidth, spectral_efficiency
            )

            data = {
                'spectral_efficiency': spectral_efficiency,
                'sinr': sinr,
                'capacity_mbps': estimated_capacity
                }

            results.append(data)

            # print('received_power is {}'.format(received_power))
            # print('interference is {}'.format(interference))
            # print('noise is {}'.format(noise))
            # print('sinr is {}'.format(sinr))
            # print('spectral_efficiency is {}'.format(spectral_efficiency))
            # print('estimated_capacity is {}'.format(estimated_capacity))
            # print('path_loss is {}'.format(path_loss))
            # print('-----------------------------')

        return results


    def find_closest_available_sites(self, receiver):
        """
        Returns a list of all sites, ranked based on proximity
        to the receiver.

        """
        idx = index.Index()

        for site in self.sites.values():
            idx.insert(0, Point(site.coordinates).bounds, site)

        number_of_sites = len(self.sites.values())

        all_closest_sites =  list(
            idx.nearest(
                Point(receiver.coordinates).bounds,
                number_of_sites, objects='raw')
                )

        closest_site = all_closest_sites[0]

        interfering_sites = all_closest_sites[1:4]

        return closest_site, interfering_sites


    def calculate_path_loss(self, closest_site, receiver,
        frequency, mast_height, environment):

        # for area in self.area.values():
        #     local_authority_ids = area.local_authority_ids

        x2_receiver = receiver.coordinates[0]
        y2_receiver = receiver.coordinates[1]

        x1_site, y1_site = transform_coordinates(
            Proj(init='epsg:27700'), Proj(init='epsg:4326'),
            closest_site.coordinates[0],
            closest_site.coordinates[1],
            )

        x2_receiver, y2_receiver = transform_coordinates(
            Proj(init='epsg:27700'), Proj(init='epsg:4326'),
            receiver.coordinates[0],
            receiver.coordinates[1],
            )

        Geo = Geodesic.WGS84

        i_strt_distance = Geo.Inverse(
            y1_site, x1_site,  y2_receiver, x2_receiver
            )

        interference_strt_distance = round(i_strt_distance['s12'],0)

        ant_height = mast_height
        ant_type =  'macro'

        # type_of_sight, building_height, street_width = built_environment_module(
        # site_geom, receiver_geom

        if interference_strt_distance < 250 :
            type_of_sight = 'los'
        else:
            type_of_sight = 'nlos'

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


    def calc_received_power(self, site, receiver, path_loss):
        """
        Calculate received power based on site and receiver
        characteristcs, and path loss.

        Equivalent Isotropically Radiated Power (EIRP) = Power + Gain - Losses

        """
        #calculate Equivalent Isotropically Radiated Power (EIRP)
        eirp = float(site.power) + \
            float(site.gain) - \
            float(site.losses)

        received_power = eirp - \
            path_loss - \
            receiver.misc_losses + \
            receiver.gain - \
            receiver.losses
        # print('received power is {}'.format(received_power))
        return received_power


    def calculate_interference(
        self, closest_sites, receiver, frequency, environment):
        """
        Calculate interference from other cells.

        closest_sites contains all sites, ranked based
        on distance, meaning we need to select cells 1-3 (as cell 0
        is the actual cell in use)

        """
        interference = []

        x1_receiver, y1_receiver = transform_coordinates(
            Proj(init='epsg:27700'),
            Proj(init='epsg:4326'),
            receiver.coordinates[0],
            receiver.coordinates[1]
            )

        #calculate interference from other power sources
        for interference_site in closest_sites:

            #get distance
            x2_interference = interference_site.coordinates[0]
            y2_interference = interference_site.coordinates[1]

            x2_interference, y2_interference = transform_coordinates(
                Proj(init='epsg:27700'),
                Proj(init='epsg:4326'),
                interference_site.coordinates[0],
                interference_site.coordinates[1]
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

            print('path loss for {} to {} is {}'.format(
                receiver.id, interference_site.id, path_loss)
                )

            #calc interference from other cells
            received_interference = self.calc_received_power(
                interference_site,
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

        Required SNR (dB)
        Detection bandwidth (BW) (Hz)
        k = Boltzmann constant
        T = Temperature (kelvins) (290 kelvin = ~16 celcius)
        NF = Receiver noise figure

        NoiseFloor (dBm) = 10log10(k*T*1000)+NF+10log10BW

        NoiseFloor (dBm) = 10log10(1.38x10e-23*290*1x10e3)+1.5+10log10(10x10e6)

        """
        k = 1.38e-23
        t = 290
        BW = bandwidth*1000000

        noise = 10*np.log10(k*t*1000)+1.5+10*np.log10(BW)

        return noise


    def calculate_sinr(self, received_power, interference, noise, network_load):
        """
        Calculate the Signal-to-Interference-plus-Noise-Ration (SINR).

        """
        raw_received_power = 10**received_power

        interference_values = []
        for value in interference:
            output_value = 10**value
            interference_values.append(output_value)

        raw_sum_of_interference = sum(interference_values) * 1.5 #(1+(network_load/100))

        raw_noise = 10**noise

        sinr = np.log10(
            raw_received_power / (raw_sum_of_interference + raw_noise)
            )

        return round(sinr, 2)


    def modulation_scheme_and_coding_rate(self, sinr,
        generation, modulation_and_coding_lut):
        """
        Uses the SINR to allocate a modulation scheme and affliated
        coding rate.

        """
        spectral_efficiency = 0

        for lower, upper in pairwise(modulation_and_coding_lut):
            if lower[0] and upper[0] == generation:

                lower_sinr = lower[5]
                upper_sinr = upper[5]

                if sinr >= lower_sinr and sinr < upper_sinr:
                    spectral_efficiency = lower[4]
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


    def find_sites_in_area(self):

        if not self.sites:
            return 0

        area_geometry = ([(d.geometry) for d in self.area.values()][0])

        idx = index.Index()

        for site in self.sites.values():
            idx.insert(0, Point(site.coordinates).bounds, site)

        sites_in_area = []

        for n in idx.intersection(shape(area_geometry).bounds, objects=True):
            point = Point(n.object.coordinates)
            if shape(area_geometry).contains(point):
                sites_in_area.append(n.object)

        return sites_in_area


    def site_density(self):
        """
        Calculate site density per square kilometer (km^2)

        Returns
        -------
        obj
            Sum of sites

        Notes
        -----
        Function returns `0` when no sites are configered to the area.

        """
        if not self.sites:
            return 0

        sites_in_area = self.find_sites_in_area()

        postcode_sector_area = (
            [round(a.area) for a in self.area.values()]
            )[0]

        site_density = (
            len(sites_in_area) / (postcode_sector_area/1000000)
            )

        return site_density


    def receiver_density(self):
        """
        Calculate receiver density per square kilometer (km^2)

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


    def energy_consumption(self, cells_per_site):
        """
        Gets the energy consumption of the sites in the area.

        Parameters
        ----------
        total_power_dbm : float
            Total dbm for all sites for a single cell.
        watts_for_1_cell_per_site : float
            Total watts for all sites for a single cell.
        total_power_watts : float
            Total watts for all cells in use.

        """
        if not self.area:
            return 0

        sites_in_area = self.find_sites_in_area()
        # print('number of sites_in_area {}'.format(len(sites_in_area)))
        total_power_dbm = [round(a.power) for a in sites_in_area]

        watts_per_area = []
        for value in total_power_dbm:
            watts_for_1_cell_per_site = 1 * 10**(value / 10) / 1000
            wattsd_per_site = watts_for_1_cell_per_site * cells_per_site
            watts_per_area.append(wattsd_per_site)

        total_power_watts = sum(watts_per_area)
        # print('total_power_watts {}'.format(total_power_watts/1000000))

        return total_power_watts


class Area(object):
    """
    The geographic area which holds all sites and receivers.

    """
    def __init__(self, data):
        #id and geographic info
        self.id = data['properties']['RMSect']
        self.local_authority_ids =  data['properties']['local_authority_ids']
        self.geometry = data['geometry']
        self.coordinates = data['geometry']['coordinates']
        self.area = self._calculate_area(data)
        #connections
        self._sites = {}
        self._receivers = {}

    def _calculate_area(self, data):
        polygon = shape(data['geometry'])
        area = polygon.area
        return area

    def add_site(self, site):
        self._sites[site.id] = site

    def add_receiver(self, receiver):
        self._receivers[receiver.id] = receiver


class Transmitter(object):
    """
    A site object is specific site.

    """
    def __init__(self, data):
        #id and geographic info
        self.id = data['properties']['sitengr']
        self.coordinates = data['geometry']['coordinates']
        self.geometry = data['geometry']
        #antenna properties
        self.ant_type = 'macro'
        self.ant_height = TX_HEIGHT_BASE
        self.power = TX_POWER
        self.gain = TX_GAIN
        self.losses = TX_LOSSES

    def __repr__(self):
        return "<Transmitter id:{}>".format(self.id)


class Receiver(object):
    """
    A receiver object is a piece of user equipment which can
    connect to a site.

    """
    def __init__(self, data):
        #id and geographic info
        self.id = data['properties']['ue_id']
        #self.site_id = data['properties']['sitengr']
        self.coordinates = data['geometry']["coordinates"]
        #parameters
        self.misc_losses = data['properties']['misc_losses']
        self.gain = data['properties']['gain']
        self.losses = data['properties']['losses']
        self.ue_height = data['properties']['ue_height']
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


def obtain_threshold_values(results, percentile):
    """
    Get the threshold capacity based on a given percentile.

    """
    spectral_efficency = []
    sinr = []
    threshold_capacity_value = []

    for result in results:

        spectral_efficency.append(result['spectral_efficiency'])
        sinr.append(result['sinr'])
        threshold_capacity_value.append(result['capacity_mbps'])

    spectral_efficency = np.percentile(spectral_efficency, percentile)
    sinr = np.percentile(sinr, percentile)
    capacity_mbps = np.percentile(threshold_capacity_value, percentile)

    return spectral_efficency, sinr, capacity_mbps


def pairwise(iterable):
    """
    Return iterable of 2-tuples in a sliding window

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


def calculate_network_efficiency(spectral_efficency, energy_consumption):

    if spectral_efficency == 0 or energy_consumption == 0:
        network_efficiency = 0
    else:
        network_efficiency = (
            float(spectral_efficency) / float(energy_consumption)
        )

    return network_efficiency


def write_results(results, frequency, bandwidth, site_density, environment,
    technology, generation, mast_height, r_density, postcode_sector_name):

    suffix = 'freq_{}_bandwidth_{}_density_{}'.format(
        frequency, bandwidth, site_density
        )

    directory = os.path.join(DATA_INTERMEDIATE, 'system_simulator', postcode_sector_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = '{}.csv'.format(suffix)
    directory = os.path.join(directory, filename)

    if not os.path.exists(directory):
        results_file = open(directory, 'w', newline='')
        results_writer = csv.writer(results_file)
        results_writer.writerow((
            'environment', 'frequency','bandwidth','technology',
            'generation', 'mast_height', 'site_density','r_density',
            'spectral_efficiency', 'sinr','throughput'
            ))
    else:
        results_file = open(directory, 'a', newline='')
        results_writer = csv.writer(results_file)

    # output and report results for this timestep
    for result in results:
        # Output metrics
        results_writer.writerow(
            (environment,

            frequency,
            bandwidth,
            technology,
            generation,
            mast_height,
            site_density,
            r_density,
            result['spectral_efficiency'],
            result['sinr'],
            result['capacity_mbps'])
            )

    results_file.close()

def write_lookup_table(
    cell_edge_spectral_efficency, cell_edge_sinr, area_capacity_mbps,
    network_efficiency, environment, operator, technology, frequency,
    bandwidth, mast_height, area_site_density, generation, postcode_sector_name):

    suffix = 'lookup_table_{}'.format(postcode_sector_name)

    directory = os.path.join(DATA_INTERMEDIATE, 'system_simulator', postcode_sector_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = '{}.csv'.format(suffix)
    directory = os.path.join(directory, filename)

    if not os.path.exists(directory):
        lut_file = open(directory, 'w', newline='')
        lut_writer = csv.writer(lut_file)
        lut_writer.writerow(
            ('environment', 'operator', 'technology',
            'frequency', 'bandwidth', 'mast_height',
            'area_site_density', 'generation',
            'cell_edge_spectral_efficency', 'cell_edge_sinr',
            'area_capacity_mbps', 'network_efficiency')
            )
    else:
        lut_file = open(directory, 'a', newline='')
        lut_writer = csv.writer(lut_file)

    # output and report results for this timestep
    lut_writer.writerow(
        (environment,
        operator,
        technology,
        frequency,
        bandwidth,
        mast_height,
        area_site_density,
        generation,
        cell_edge_spectral_efficency,
        cell_edge_sinr,
        area_capacity_mbps,
        network_efficiency)
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
    directory = os.path.join(DATA_INTERMEDIATE,
        'system_simulator', postcode_sector_name)
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
    directory = os.path.join(DATA_INTERMEDIATE, postcode_sector_name, 'plots')
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
    directory = os.path.join(DATA_INTERMEDIATE, postcode_sector_name, 'plots')
    if not os.path.exists(directory):
        os.makedirs(directory)

    plt.savefig(os.path.join(directory, 'panel_plot.png'))


def run_transmitter_module(postcode_sector_name, transmitter_type):

        #get postcode sector
        geojson_postcode_sector = read_postcode_sector(postcode_sector_name)

        #get local authority district
        local_authority_ids = get_local_authority_ids(geojson_postcode_sector)

        #datashare_pcd_sectors lad information to postcode sectors
        geojson_postcode_sector['properties']['local_authority_ids'] = (
            local_authority_ids
            )

        #get the probability for inside versus outside calls
        postcode_sector_lut = import_area_lut(
            postcode_sector_name, local_authority_ids
            )

        #get propagation environment (urban, suburban or rural)
        environment = determine_environment(postcode_sector_lut)

        #get list of sites
        TRANSMITTERS = get_sites(geojson_postcode_sector, transmitter_type)

        #generate receivers
        RECEIVERS = generate_receivers(
            geojson_postcode_sector,
            postcode_sector_lut,
            ITERATIONS
            )

        idx = 0

        for mast_height in MAST_HEIGHT:
            for operator, technology, frequency, bandwidth, generation in SPECTRUM_PORTFOLIO:

                #load system model with data
                MANAGER = NetworkManager(
                    geojson_postcode_sector, TRANSMITTERS, RECEIVERS
                    )

                # # calculate site density
                current_site_density = MANAGER.site_density()

                # site_densities = [starting_site_density, 2, 4, 6, 8]

                postcode_sector_object = [a for a in MANAGER.area.values()][0]

                postcode_sector_area = postcode_sector_object.area/1e6

                # max_sites = int(round(10 * postcode_sector_area))

                # current_sites = current_site_density * postcode_sector_area

                idx = 0

                while current_site_density < 10:

                    print("{} GHz {}m Height {} Density, {}".format(
                        frequency, mast_height, round(current_site_density, 4),
                        generation
                        ))

                    # number_of_new_sites = int(
                    #     (site_density - current_site_density) * postcode_sector_area
                    # )
                    number_of_new_sites = 1

                    # print('number_of_new_sites {}'.format(1))
                    NEW_TRANSMITTERS = find_and_deploy_new_site(
                        MANAGER.sites, number_of_new_sites,
                        geojson_postcode_sector, idx
                        )

                    MANAGER.build_new_assets(
                        NEW_TRANSMITTERS, geojson_postcode_sector
                        )

                    results = MANAGER.estimate_link_budget(
                        frequency, bandwidth, generation, mast_height,
                        environment, MODULATION_AND_CODING_LUT, NETWORK_LOAD
                        )

                    #find percentile values
                    spectral_efficency, sinr, capacity_mbps = (
                        obtain_threshold_values(results, PERCENTILE)
                        )

                    network_efficiency = calculate_network_efficiency(
                        spectral_efficency,
                        MANAGER.energy_consumption(SECTORISATION)
                        )

                    area_capacity_mbps = capacity_mbps * SECTORISATION

                    current_site_density = MANAGER.site_density()

                    r_density = MANAGER.receiver_density()

                    write_results(results, frequency, bandwidth, current_site_density,
                        r_density, postcode_sector_name
                        )

                    #env, frequency, bandwidth, site_density, capacity
                    write_lookup_table(
                        spectral_efficency, sinr, area_capacity_mbps,
                        network_efficiency, environment, operator, technology,
                        frequency, bandwidth, mast_height, current_site_density, generation,
                        postcode_sector_name
                        )

                    idx += 1

                    # print('------------------------------------')

        # # print('write buildings')
        # # write_shapefile(buildings,  postcode_sector_name, 'buildings.shp')

        # print('write receivers')
        # write_shapefile(RECEIVERS,  postcode_sector_name, 'receivers.shp')

        # print('write sites')
        # write_shapefile(TRANSMITTERS,  postcode_sector_name, 'sites.shp')

        # print('write boundary')
        # geojson_postcode_sector_list = []
        # geojson_postcode_sector_list.append(geojson_postcode_sector)
        # write_shapefile(
        #     geojson_postcode_sector_list,  postcode_sector_name, '_boundary.shp'
        #     )

#####################################
# APPLY METHODS
#####################################

SPECTRUM_PORTFOLIO = [
    ('generic', 'FDD DL', 0.7, 10, '5G'),
    ('generic', 'FDD DL', 0.8, 10, '4G'),
    ('generic', 'FDD DL', 1.8, 10, '4G'),
    ('generic', 'FDD DL', 2.6, 10, '4G'),
    ('generic', 'FDD DL', 3.5, 80, '5G'),
]

MAST_HEIGHT = [
    (30),
    (40)
]

MODULATION_AND_CODING_LUT =[
    # CQI Index	Modulation	Coding rate
    # Spectral efficiency (bps/Hz) SINR estimate (dB)
    ('4G', 1, 'QPSK',	0.0762,	0.1523, -6.7),
    ('4G', 2, 'QPSK',	0.1172,	0.2344, -4.7),
    ('4G', 3, 'QPSK',	0.1885,	0.377, -2.3),
    ('4G', 4, 'QPSK',	0.3008,	0.6016, 0.2),
    ('4G', 5, 'QPSK',	0.4385,	0.877, 2.4),
    ('4G', 6, 'QPSK',	0.5879,	1.1758,	4.3),
    ('4G', 7, '16QAM', 0.3691, 1.4766, 5.9),
    ('4G', 8, '16QAM', 0.4785, 1.9141, 8.1),
    ('4G', 9, '16QAM', 0.6016, 2.4063, 10.3),
    ('4G', 10, '64QAM', 0.4551, 2.7305, 11.7),
    ('4G', 11, '64QAM', 0.5537, 3.3223, 14.1),
    ('4G', 12, '64QAM', 0.6504, 3.9023, 16.3),
    ('4G', 13, '64QAM', 0.7539, 4.5234, 18.7),
    ('4G', 14, '64QAM', 0.8525, 5.1152, 21),
    ('4G', 15, '64QAM', 0.9258, 5.5547, 22.7),
    ('5G', 1, 'QPSK', 78, 0.1523, -6.7),
    ('5G', 2, 'QPSK', 193, 0.377, -4.7),
    ('5G', 3, 'QPSK', 449, 0.877, -2.3),
    ('5G', 4, '16QAM', 378, 1.4766, 0.2),
    ('5G', 5, '16QAM', 490, 1.9141, 2.4),
    ('5G', 6, '16QAM', 616, 2.4063, 4.3),
    ('5G', 7, '64QAM', 466, 2.7305, 5.9),
    ('5G', 8, '64QAM', 567, 3.3223, 8.1),
    ('5G', 9, '64QAM', 666, 3.9023, 10.3),
    ('5G', 10, '64QAM', 772, 4.5234, 11.7),
    ('5G', 11, '64QAM', 873, 5.1152, 14.1),
    ('5G', 12, '256QAM', 711, 5.5547, 16.3),
    ('5G', 13, '256QAM', 797, 6.2266, 18.7),
    ('5G', 14, '256QAM', 885, 6.9141, 21),
    ('5G', 15, '256QAM', 948, 7.4063, 22.7),
]

site_densities = {
    'urban': [
        7.22, 3.21, 1.8, 1.15, 0.8, 0.59,
        0.45, 0.36, 0.29, 0.24, 0.2, 0.17,
        0.15, 0.13, 0.11, 0.1, 0.09, 0.08,
        0.07, 0.05, 0.03, 0.02
    ],
    'suburban': [
        0.59, 0.45, 0.36, 0.29, 0.24, 0.2,
        0.17, 0.15, 0.13, 0.09, 0.07, 0.06,
        0.05, 0.03, 0.0236, 0.018, 0.0143,
        0.0115, 0.0095, 0.008, 0.0321
    ],
    'rural': [
        0.0500, 0.0115, 0.0080, 0.0051,
        0.0040, 0.0029, 0.0024, 0.0018,
        0.0016, 0.0013, 0.0009, 0.0007,
        0.0006,
    ]
}

if __name__ == "__main__":

    if len(sys.argv) != 3:
        print("Error: no postcode sector or transmitter type argument provided")
        exit(-1)
    if sys.argv[2] != 'real' and sys.argv[2] != 'synthetic':
        print("Transmitter type error: must be either 'real' or 'synthetic'")
        exit(-1)

    print('Process ' + sys.argv[1])
    postcode_sector_name = sys.argv[1]

    print('running')
    run_transmitter_module(postcode_sector_name, sys.argv[2])
