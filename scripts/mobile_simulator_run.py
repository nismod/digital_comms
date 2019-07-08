"""
Runner for system_simulator.py

Written by Edward Oughton
May 2019

"""
import os
import sys
import configparser
import csv

import math
import fiona
from shapely.geometry import shape, Point
import numpy as np
from random import choice
from rtree import index

from collections import OrderedDict

from digital_comms.mobile_network.generate_hex import produce_sites_and_cell_areas
from digital_comms.mobile_network.system_simulator import SimulationManager

np.random.seed(42)

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')


def generate_receivers(cell_area, inter_site_distance, simulation_parameters):
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
    geom = shape(cell_area[0]['geometry'])
    geom_box = geom.bounds

    minx = geom_box[0]
    miny = geom_box[1]
    maxx = geom_box[2]
    maxy = geom_box[3]

    receivers = []

    id_number = 0

    x_axis = np.linspace(
        minx, maxx, num=(int(math.sqrt(geom.area) / (math.sqrt(geom.area)/20)))
        )
    y_axis = np.linspace(
        miny, maxy, num=(int(math.sqrt(geom.area) / (math.sqrt(geom.area)/20)))
        )

    xv, yv = np.meshgrid(x_axis, y_axis, sparse=False, indexing='ij')
    for i in range(len(x_axis)):
        for j in range(len(y_axis)):
            receiver = Point((xv[i,j], yv[i,j]))
            if geom.contains(receiver):
                receivers.append({
                    'type': "Feature",
                    'geometry': {
                        "type": "Point",
                        "coordinates": [xv[i,j], yv[i,j]],
                    },
                    'properties': {
                        'ue_id': "id_{}".format(id_number),
                        "misc_losses": simulation_parameters['rx_misc_losses'],
                        "gain": simulation_parameters['rx_gain'],
                        "losses": simulation_parameters['rx_losses'],
                        "ue_height": float(simulation_parameters['rx_height']),
                        "indoor": False,
                    }
                })
                id_number += 1

            else:
                pass

    iterations = simulation_parameters['iterations']
    output = []

    for receiver in receivers:
        for i in range(1, (iterations + 1)):
            output.append({
                'type': receiver['type'],
                'geometry': receiver['geometry'],
                'properties': {
                    'ue_id': str(receiver['properties']['ue_id'] + str(i)),
                    "misc_losses": receiver['properties']['misc_losses'],
                    "gain": receiver['properties']['gain'],
                    "losses": receiver['properties']['losses'],
                    "ue_height": receiver['properties']['ue_height'],
                    "indoor": receiver['properties']['indoor'],
                }
            })

    return output


def obtain_threshold_values(results, simulation_parameters):
    """
    Get the threshold capacity based on a given percentile.
    """

    sinr_values = []

    percentile = simulation_parameters['percentile']

    for result in results:

        sinr = result['sinr']

        if sinr == None:
            pass
        else:
            sinr_values.append(sinr)

    sinr = np.percentile(sinr_values, percentile, interpolation='nearest')

    matching_result = []

    for result in results:
        if float(result['sinr']) == float(sinr):
            matching_result.append(result)

    return choice(matching_result)


def convert_shape_to_projected_crs(line, original_crs, new_crs):
    """
    Existing elevation path needs to be converted from WGS84 to projected
    coordinates.
    """
    # Geometry transform function based on pyproj.transform
    project = partial(
        pyproj.transform,
        pyproj.Proj(init = original_crs),
        pyproj.Proj(init = new_crs)
        )

    new_geom = transform(project, LineString(line['geometry']['coordinates']))

    output = {
        'type': 'Feature',
        'geometry': mapping(new_geom),
        'properties': line['properties']
        }

    return output


def convert_results_geojson(data):

    output = []

    for datum in data:
        output.append({
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [datum['receiver_x'], datum['receiver_y']]
                },
            'properties': {
                'path_loss': float(datum['path_loss']),
                'received_power': float(datum['received_power']),
                'interference': float(datum['interference']),
                'noise': float(datum['noise']),
                'sinr': float(datum['sinr']),
                'spectral_efficiency': float(datum['spectral_efficiency']),
                'estimated_capacity': float(datum['estimated_capacity']),
                },
            })

    return output


def write_full_results(data, environment, cell_radius, frequency,
    bandwidth, generation, mast_height, directory, filename):
    """
    Write data to a CSV file path

    """
    inter_site_distance = cell_radius * 2
    cell_area_km2 = math.sqrt(3) / 2 * inter_site_distance ** 2 / 1e6
    cells_per_km2 = 1 / cell_area_km2

    if not os.path.exists(directory):
        os.makedirs(directory)

    full_path = os.path.join(directory, filename)

    results_file = open(full_path, 'w', newline='')
    results_writer = csv.writer(results_file)
    results_writer.writerow(
        ('environment', 'inter_site_distance', 'sites_per_km2', 'frequency',
        'bandwidth', 'generation', 'mast_height', 'receiver_x',
        'receiver_y', 'path_loss', 'received_power', 'interference',
        'noise', 'sinr', 'spectral_efficiency', 'estimated_capacity'))

    for row in data:
        results_writer.writerow((
            environment,
            inter_site_distance,
            cells_per_km2,
            frequency,
            bandwidth,
            generation,
            mast_height,
            row['receiver_x'],
            row['receiver_y'],
            row['path_loss'],
            row['received_power'],
            row['interference'],
            row['noise'],
            row['sinr'],
            row['spectral_efficiency'],
            row['estimated_capacity'],
            ))


def write_lookup_table(cell_edge_result, environment, cell_radius,
    frequency, bandwidth, generation, mast_height, directory, filename):
    """
    Write the main lookup table focusing on the cell edge rate.

    """
    inter_site_distance = cell_radius * 2
    cell_area_km2 = math.sqrt(3) / 2 * inter_site_distance ** 2 / 1e6
    cells_per_km2 = 1 / cell_area_km2

    directory = os.path.join(DATA_INTERMEDIATE, 'system_simulator')
    if not os.path.exists(directory):
        os.makedirs(directory)

    directory = os.path.join(directory, filename)

    if not os.path.exists(directory):
        lut_file = open(directory, 'w', newline='')
        lut_writer = csv.writer(lut_file)
        lut_writer.writerow(
            ('environment', 'inter_site_distance', 'sites_per_km2', 'frequency_GHz',
            'bandwidth_MHz', 'generation', 'mast_height_m', 'path_loss_dB',
            'received_power_dBm', 'interference_dBm', 'network_load',
            'noise_dBm', 'i_plus_n_dBm', 'sinr', 'spectral_efficiency_bps_hz',
            'single_sector_capacity_mbps_km2',
            'three_sector_capacity_mbps_km2')
            )
    else:
        lut_file = open(directory, 'a', newline='')
        lut_writer = csv.writer(lut_file)

    # output and report results for this timestep
    lut_writer.writerow(
        (environment,
        inter_site_distance,
        cells_per_km2,
        frequency,
        bandwidth,
        generation,
        mast_height,
        cell_edge_result['path_loss'],
        cell_edge_result['received_power'],
        cell_edge_result['interference'],
        cell_edge_result['network_load'],
        cell_edge_result['noise'],
        cell_edge_result['i_plus_n'],
        cell_edge_result['sinr'],
        cell_edge_result['spectral_efficiency'],
        cell_edge_result['estimated_capacity'],
        cell_edge_result['estimated_capacity'] * 3,
        ))

    lut_file.close()


def write_shapefile(data, filename):

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
    directory = os.path.join(DATA_INTERMEDIATE, 'system_simulator')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # print(os.path.join(directory, filename))
    # Write all elements to output file
    with fiona.open(
        os.path.join(directory, filename), 'w',
        driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        for datum in data:
            sink.write(datum)


def run_simulator(simulation_parameters, spectrum_portfolio, mast_heights,
    cell_radii, modulation_and_coding_lut):


    # with fiona.open(
    #     os.path.join(DATA_RAW, 'crystal_palace_to_mursley.shp'), 'r') as source:
    #         unprojected_line = next(iter(source))
    #         unprojected_point = unprojected_line['geometry']['coordinates'][0]
    unprojected_point = {
        'type': 'Feature',
        'geometry': {
            'type': 'Point',
            'coordinates': (0, 51.476),
            },
        'properties': {
            'site_id': 'Crystal Palace Radio Tower'
            }
        }
    environments =[
        'urban',
        'suburban',
        'rural'
    ]
    for environment in environments:
        for cell_radius in cell_radii[environment]:

            print('--working on {}: {}'.format(environment, cell_radius))

            transmitter, interfering_transmitters, cell_area, interfering_cell_areas = \
                produce_sites_and_cell_areas(
                    unprojected_point['geometry']['coordinates'],
                    cell_radius
                    )

            receivers = generate_receivers(
                cell_area, cell_radius,
                SIMULATION_PARAMETERS
                )
            print('num receivers = {}'.format(len(receivers)))
            for frequency, bandwidth, generation in spectrum_portfolio:
                for mast_height in mast_heights:

                    MANAGER = SimulationManager(
                        transmitter, interfering_transmitters, receivers, cell_area, SIMULATION_PARAMETERS
                        )

                    results = MANAGER.estimate_link_budget(
                        frequency, bandwidth, generation, mast_height,
                        environment,
                        MODULATION_AND_CODING_LUT,
                        SIMULATION_PARAMETERS
                        )

                    write_full_results(results, environment, cell_radius, frequency,
                        bandwidth, generation, mast_height,
                        os.path.join(DATA_INTERMEDIATE, 'system_simulator', 'full_tables'),
                        'test_capacity_data_{}_{}_{}_{}.csv'.format(
                            environment, cell_radius, frequency, mast_height))


                    cell_edge_result = obtain_threshold_values(
                        results, simulation_parameters
                        )

                    write_lookup_table(cell_edge_result, environment, cell_radius,
                        frequency, bandwidth, generation, mast_height,
                        os.path.join(DATA_INTERMEDIATE, 'system_simulator'),
                        'test_lookup_table.csv')

            #         geojson_receivers = convert_results_geojson(results)

            #         write_shapefile(geojson_receivers, 'receivers_{}.shp'.format(inter_site_distance))
            #         write_shapefile(transmitter, 'transmitter_{}.shp'.format(inter_site_distance))
            #         write_shapefile(cell_area, 'cell_area_{}.shp'.format(inter_site_distance))
            #         write_shapefile(interfering_transmitters, 'interfering_transmitters_{}.shp'.format(inter_site_distance))
            #         write_shapefile(interfering_cell_areas, 'interfering_cell_areas_{}.shp'.format(inter_site_distance))

            #         average_capacity = []
            #         for result in results:
            #             average_capacity.append(result['estimated_capacity'])
            #         print('------')
            #         print_ave_capacity = round(sum(average_capacity)/len(average_capacity))
            #         print('isd: {}, {}'.format(inter_site_distance, print_ave_capacity))

            print('complete')



if __name__ == '__main__':


    SIMULATION_PARAMETERS = {
        'iterations': 1,
        'seed_value1': 1,
        'seed_value2': 2,
        'tx_baseline_height': 30,
        'tx_upper_height': 50,
        'tx_power': 40,
        'tx_gain': 16,
        'tx_losses': 1,
        'rx_gain': 4,
        'rx_losses': 4,
        'rx_misc_losses': 4,
        'rx_height': 1.5,
        'network_load': 50,
        'percentile': 50,
        'desired_transmitter_density': 10,
        'sectorisation': 3,
        # 'interfering_sites': 20,
        # 'overbooking_factor': 50,
    }

    SPECTRUM_PORTFOLIO = [
        (0.7, 10, '5G'),
        (0.8, 10, '4G'),
        (1.8, 10, '4G'),
        (2.6, 10, '4G'),
        (3.5, 40, '5G'),
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

    # CELL_RADII = {
    #     'urban': [
    #         200, 300, 400, 500, 600, 700, 800, 900, 1000,
    #         1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800,
    #         1900, 2000, 2500, 3000, 3500, 4000,
    #     ],
    #     'suburban': [
    #         700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500,
    #         1750, 2000, 2250, 2500, 3000, 3500, 4000, 4500, 5000,
    #         5500, 6000,
    #     ],
    #     'rural': [
    #         2500, 5000, 7500, 10000, 12500, 15000, 17500, 20000,
    #         22500, 25000, 27500, 30000, 32500,
    #         ]
    # }

    CELL_RADII = {
        'urban': [
            1000, 2000, 3000, 4000, 5000, 6000
        ],
        'suburban': [
            1000, 2000, 3000, 4000, 5000, 6000
        ],
        'rural': [
            5000, 10000, 15000, 20000, 25000, 30000
            ]
    }

    run_simulator(
        SIMULATION_PARAMETERS,
        SPECTRUM_PORTFOLIO,
        MAST_HEIGHT,
        CELL_RADII,
        MODULATION_AND_CODING_LUT
        )
