"""
Runner for system_simulator.py

Written by Edward Oughton
May 2019

"""
import os
import sys
import configparser
import csv

import fiona
from shapely.geometry import shape, Point, Polygon
import numpy as np
from geographiclib.geodesic import Geodesic
from scipy.spatial import Delaunay

from itertools import tee
from collections import OrderedDict

from digital_comms.mobile_network.system_simulator import NetworkManager

np.random.seed(42)

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')

SIMULATION_PARAMETERS = {
    'iterations': 5,
    'tx_baseline_height': 30,
    'tx_upper_height': 40,
    'tx_power': 40,
    'tx_gain': 16,
    'tx_losses': 1,
    'rx_gain': 4,
    'rx_losses': 4,
    'rx_misc_losses': 4,
    'rx_height': 1.5,
    'network_load': 50,
    'percentile': 90,
    'desired_transmitter_density': 10,
    'sectorisation': 3,
}


def read_postcode_sector(postcode_sector, path):

    with fiona.open(path, 'r') as source:

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


def get_sites(postcode_sector, transmitter_type, simulation_parameters):
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
                                "power": simulation_parameters['tx_power'],
                                # "power_dbw": line['Powerdbw'],
                                # "max_power_dbw": line['Maxpwrdbw'],
                                # "max_power_dbm": line['Maxpwrdbm'],
                                "gain": simulation_parameters['tx_gain'],
                                "losses": simulation_parameters['tx_losses'],
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
                        "power": simulation_parameters['tx_power'],
                        "gain": simulation_parameters['tx_gain'],
                        "losses": simulation_parameters['tx_losses'],
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
                        "power": simulation_parameters['tx_power'],
                        "gain": simulation_parameters['tx_gain'],
                        "losses": simulation_parameters['tx_losses'],
                    }
                })
                id_number += 1

        else:
            pass
    else:
        print('Error: Did you type an incorrect site type?')
        print('Site types must either be "real" or "synthetic"')

    return sites


def generate_receivers(postcode_sector, postcode_sector_lut, simulation_parameters):
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
    simulation_parameters : dict
        Contains all necessary simulation parameters.

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

    while len(receivers) < simulation_parameters['iterations']:

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
                    "misc_losses": simulation_parameters['rx_misc_losses'],
                    "gain": simulation_parameters['rx_gain'],
                    "losses": simulation_parameters['rx_losses'],
                    "ue_height": float(simulation_parameters['rx_height']),
                    "indoor": (True if float(indoor_outdoor_probability) < \
                        float(indoor_probability) else False),
                }
            })
            id_number += 1

        else:
            pass

    return receivers


def find_and_deploy_new_site(existing_sites, new_sites,
    geojson_postcode_sector, idx, simulation_parameters):
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
                    "ant_height": simulation_parameters['tx_baseline_height'],
                    "tech": 'LTE',
                    "freq": 700,
                    "type": 17,
                    "power": simulation_parameters['tx_power'],
                    "gain": simulation_parameters['tx_gain'],
                    "losses": simulation_parameters['tx_losses'],
                }
            })

    return NEW_TRANSMITTERS


def obtain_threshold_values(results, simulation_parameters):
    """
    Get the threshold capacity based on a given percentile.

    """
    spectral_efficency = []
    sinr = []
    threshold_capacity_value = []

    percentile = simulation_parameters['percentile']

    for result in results:

        spectral_efficency.append(result['spectral_efficiency'])
        sinr.append(result['sinr'])
        threshold_capacity_value.append(result['capacity_mbps'])

    spectral_efficency = np.percentile(spectral_efficency, percentile)
    sinr = np.percentile(sinr, percentile)
    capacity_mbps = np.percentile(threshold_capacity_value, percentile)

    return spectral_efficency, sinr, capacity_mbps


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


def run_transmitter_module(postcode_sector_name, transmitter_type, simulation_parameters):

        #get postcode sector
        path = os.path.join(DATA_RAW, 'd_shapes', 'datashare_pcd_sectors', 'PostalSector.shp')
        geojson_postcode_sector = read_postcode_sector(postcode_sector_name, path)

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
        TRANSMITTERS = get_sites(
            geojson_postcode_sector, transmitter_type, simulation_parameters
            )

        #generate receivers
        RECEIVERS = generate_receivers(
            geojson_postcode_sector,
            postcode_sector_lut,
            simulation_parameters
            )

        idx = 0

        for mast_height in MAST_HEIGHT:
            for operator, technology, frequency, bandwidth, generation in SPECTRUM_PORTFOLIO:

                MANAGER = NetworkManager(
                    geojson_postcode_sector, TRANSMITTERS, RECEIVERS, simulation_parameters
                    )

                # # calculate site density
                current_site_density = MANAGER.site_density()

                # site_densities = [starting_site_density, 2, 4, 6, 8]

                postcode_sector_object = [a for a in MANAGER.area.values()][0]

                postcode_sector_area = postcode_sector_object.area/1e6

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
                        geojson_postcode_sector, idx,
                        simulation_parameters
                        )

                    MANAGER.build_new_assets(
                        NEW_TRANSMITTERS, geojson_postcode_sector,
                        simulation_parameters
                        )

                    results = MANAGER.estimate_link_budget(
                        frequency, bandwidth, generation, mast_height,
                        environment, MODULATION_AND_CODING_LUT,
                        simulation_parameters
                        )

                    #find percentile values
                    spectral_efficency, sinr, capacity_mbps = (
                        obtain_threshold_values(results, simulation_parameters)
                        )

                    network_efficiency = calculate_network_efficiency(
                        spectral_efficency,
                        MANAGER.energy_consumption(simulation_parameters)
                        )

                    area_capacity_mbps = (
                        capacity_mbps * simulation_parameters['sectorisation']
                        )

                    current_site_density = MANAGER.site_density()

                    r_density = MANAGER.receiver_density()

                    write_results(results, frequency, bandwidth, current_site_density,
                        environment, technology, generation, mast_height,
                        r_density, postcode_sector_name
                        )

                    write_lookup_table(
                        spectral_efficency, sinr, area_capacity_mbps,
                        network_efficiency, environment, operator, technology,
                        frequency, bandwidth, mast_height, current_site_density, generation,
                        postcode_sector_name
                        )

                    idx += 1


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
    run_transmitter_module(postcode_sector_name, sys.argv[2], SIMULATION_PARAMETERS)
