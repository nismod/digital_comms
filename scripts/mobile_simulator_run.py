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
from shapely.geometry import shape, Point, Polygon, mapping
import numpy as np
from geographiclib.geodesic import Geodesic
from scipy.spatial import Delaunay, Voronoi, voronoi_plot_2d
from random import shuffle
from rtree import index

from itertools import tee
from collections import OrderedDict

from digital_comms.mobile_network.system_simulator import SimulationManager
from digital_comms.mobile_network.system_simulator_deployment_module import find_and_deploy_new_site

np.random.seed(42)

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')


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
                        # 'residential_count': line['residential_count'],
                        # 'non_residential_count': line['non_residential_count'],
                        # 'estimated_population': int(float(line['residential_count'])*2.5),
                        # 'area': line['area'],
                    }

    return lut


def import_population_data(geojson_postcode_sector, postcode_sector_lut):

    postcode_sector_name = geojson_postcode_sector['properties']['RMSect'].replace(' ', '')

    path = os.path.join(
        DATA_RAW, 'b_mobile_model', 'arc_scenarios',
        'pcd_arc_population__baseline.csv'
        )

    with open(path, 'r') as system_file:
        reader = csv.DictReader(system_file)
        for line in reader:
            if line['postcode_sector'].replace(' ', '') == postcode_sector_name:
                if line['year'] == '2020':
                    return int(line['population']) / postcode_sector_lut['area_km2']


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
                                "freq": 'lte bands',#line['Freqband'],
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
                        "freq": 'lte bands',#[800, 1800, 2600],
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

            postcode_sector_centroid = shape(postcode_sector['geometry']).centroid

            sites.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [postcode_sector_centroid.x, postcode_sector_centroid.y],
                },
                'properties': {
                    "sitengr": 'site_id_{}'.format(id_number),
                    "ant_height": 30,
                    "tech": '4G',
                    "freq": 'lte bands',#[800, 1800, 2600],
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


def generate_receivers(postcode_sector, site_areas,
    postcode_sector_lut, simulation_parameters):
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
    postcode_sector_geom = shape(postcode_sector['geometry'])

    intersecting_site_areas = []

    idx = index.Index(
        (i, shape(site_area['geometry']).bounds, site_area)
        for i, site_area in enumerate(site_areas)
    )

    for n in idx.intersection((postcode_sector_geom.bounds), objects=True):
        site_area = shape(n.object['geometry'])
        if postcode_sector_geom.intersects(site_area):
            intersecting_site_areas.append(n.object)

    indoor_probability = postcode_sector_lut['indoor_probability']

    pop_density = postcode_sector_lut['pop_density_km2']

    id_number = 0

    all_receivers = []

    for site_area in intersecting_site_areas:

        site_receivers = []
        site_area_geom = shape(site_area['geometry'])
        site_area_km2 = site_area_geom.area / 1e6

        num_receivers = (
            (pop_density * site_area_km2) #/ 100
            (simulation_parameters['overbooking_factor'])
            )

        geom_box = site_area_geom.bounds

        minx = geom_box[0]
        miny = geom_box[1]
        maxx = geom_box[2]
        maxy = geom_box[3]

        while len(site_receivers) < num_receivers:

            x_coord = np.random.uniform(low=minx, high=maxx, size=1)
            y_coord = np.random.uniform(low=miny, high=maxy, size=1)

            indoor_outdoor_probability = np.random.rand(1,1)[0][0]

            coordinates = list(zip(x_coord, y_coord))

            receiver_shape = Point((x_coord, y_coord))
            if site_area_geom.contains(receiver_shape):
                receiver = {
                    'type': "Feature",
                    'geometry': {
                        "type": "Point",
                        "coordinates": [coordinates[0][0],coordinates[0][1]],
                    },
                    'properties': {
                        'ue_id': "id_{}".format(id_number),
                        "sitengr": site_area['properties']['sitengr'],
                        "misc_losses": simulation_parameters['rx_misc_losses'],
                        "gain": simulation_parameters['rx_gain'],
                        "losses": simulation_parameters['rx_losses'],
                        "ue_height": float(simulation_parameters['rx_height']),
                        "indoor": str((True if float(indoor_outdoor_probability) < \
                            float(indoor_probability) else False)),
                    }
                }
                site_receivers.append(receiver)
                all_receivers.append(receiver)
                id_number += 1
            else:
                pass

    return all_receivers


def determine_environment(simulation_parameters):

    population_density = simulation_parameters['pop_density_km2']

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


def generate_interfering_sites(postcode_sector, simulation_parameters):
    """

    """
    coordinates = []

    geom = shape(postcode_sector['geometry'])
    geom_length = geom.length/8
    geom_buffer = geom.buffer(geom_length)
    geom_box = geom_buffer.bounds

    minx = geom_box[0]
    miny = geom_box[1]
    maxx = geom_box[2]
    maxy = geom_box[3]

    interfering_sites = []

    id_number = 0

    while len(interfering_sites) < simulation_parameters['interfering_sites']:

        x_coord = np.random.uniform(low=minx, high=maxx, size=1)
        y_coord = np.random.uniform(low=miny, high=maxy, size=1)

        coordinates = list(zip(x_coord, y_coord))

        # Join the two
        postcode_sector_shape = shape(postcode_sector['geometry'])
        interfering_site = Point((x_coord, y_coord))
        if not postcode_sector_shape.contains(interfering_site):
            interfering_sites.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [coordinates[0][0],coordinates[0][1]],
                },
                'properties': {
                    "sitengr": 'site_id_interfering_{}'.format(id_number),
                    "ant_height": 30,
                    "tech": '4G',
                    "freq": 'lte bands',#[800, 1800, 2600],
                    "type": '3 sectored macrocell',
                    "power": simulation_parameters['tx_power'],
                    "gain": simulation_parameters['tx_gain'],
                    "losses": simulation_parameters['tx_losses'],
                }
            })
            id_number += 1

        else:
            pass

    return interfering_sites


def obtain_threshold_values(manager, simulation_parameters):
    """
    Get the threshold capacity based on a given percentile.

    """
    received_power = []
    interference = []
    noise = []
    i_plus_n = []
    sinr = []
    spectral_efficency = []
    threshold_capacity_value = []

    percentile = simulation_parameters['percentile']

    for receiver in manager.find_receivers_area():

        rp = receiver.capacity_metrics['received_power']
        if rp == None:
            pass
        else:
            received_power.append(rp)

        i = receiver.capacity_metrics['interference']
        if i == None:
            pass
        else:
            interference.append(i)

        n = receiver.capacity_metrics['noise']
        if n == None:
            pass
        else:
            noise.append(n)

        i_plus_n = receiver.capacity_metrics['i_plus_n']
        if i_plus_n == None:
            pass
        else:
            noise.append(i_plus_n)

        sinr_value = receiver.capacity_metrics['sinr']
        if sinr_value == None:
            pass
        else:
            sinr.append(sinr_value)

        se = receiver.capacity_metrics['spectral_efficiency']
        if se == None:
            pass
        else:
            spectral_efficency.append(se)

        capacity_mbps = receiver.capacity_metrics['capacity_mbps_km2']
        if capacity_mbps == None:
            pass
        else:
            threshold_capacity_value.append(capacity_mbps)

    received_power = np.percentile(received_power, percentile)
    interference = np.percentile(interference, percentile)
    noise = np.percentile(noise, percentile)
    i_plus_n = np.percentile(i_plus_n, percentile)
    spectral_efficency = np.percentile(spectral_efficency, percentile)
    sinr = np.percentile(sinr, percentile)
    capacity_mbps = np.percentile(threshold_capacity_value, percentile)

    return received_power, interference, noise, i_plus_n, \
        spectral_efficency, sinr, capacity_mbps


def calculate_network_efficiency(spectral_efficency, energy_consumption):

    if spectral_efficency == 0 or energy_consumption == 0:
        network_efficiency = 0
    else:
        network_efficiency = (
            float(spectral_efficency) / float(energy_consumption)
        )

    return network_efficiency


def return_single_list(list1, list2):
    """
    Takes two list of dicts and returns a single list of dicts.

    """

    output = []

    for item in list1:
        output.append(item)

    for item in list2:
        output.append(item)

    return output


# def threshold_values_for_sites(manager, simulation_parameters):

#     percentile = simulation_parameters['percentile']

#     se_values = []
#     capacity_values_km2 = []
#     for receiver in manager.find_receivers_area():
#         # if not site.id.startswith('site_id_interfering_'):
#         # print('length of se is {}'.format(len(site.spectral_efficiency)))
#         try:
#             se_percentile = np.percentile(site.spectral_efficiency, percentile)
#             se_values.append(se_percentile)
#         except:
#             pass
#         print('length of capacity is {}'.format(len(site.capacity_km2)))
#         try:
#             capacity_perc = np.percentile(site.capacity_km2, percentile)
#             capacity_values_km2.append(capacity_perc)
#         except:
#             pass
#     print('length of capacity_values_km2 is {}'.format(len(capacity_values_km2)))
#     se = sum(se_values)/len(se_values)
#     capacity_mbps_km2 = sum(capacity_values_km2) / len(capacity_values_km2)

#     return capacity_mbps_km2, se


def get_results(manager):
    results = []
    for item in manager.find_receivers_area():
        results.append({
            'num_sites': item.capacity_metrics['num_sites'],
            'path_loss': item.capacity_metrics['path_loss'],
            'ave_inf_pl': item.capacity_metrics['ave_inf_pl'],
            'received_power': item.capacity_metrics['received_power'],
            'distance': item.capacity_metrics['distance'],
            'interference': item.capacity_metrics['interference'],
            'network_load': item.capacity_metrics['network_load'],
            'ave_distance': item.capacity_metrics['ave_distance'],
            'noise': item.capacity_metrics['noise'],
            'i_plus_n': item.capacity_metrics['i_plus_n'],
            'sinr': item.capacity_metrics['sinr'],
            'spectral_efficiency': item.capacity_metrics['spectral_efficiency'],
            'capacity_mbps_km2': item.capacity_metrics['capacity_mbps_km2'],
            'x': item.capacity_metrics['x'],
            'y': item.capacity_metrics['y'],
            })
    return results


def write_results(results, frequency, bandwidth, num_sites, num_receivers,
    site_density, environment, technology, generation, mast_height, r_density,
    postcode_sector_name):

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
            'environment', 'frequency_GHz','bandwidth_MHz','technology',
            'generation', 'mast_height_m', 'num_sites', 'num_receivers',
            'site_density_km2','r_density_km2',
            'received_power_dBm', 'receiver_path_loss_dB',
            'interference_dBm', 'ave_inference_pl_dB', 'inference_ave_distance',
            'network_load',  'noise_dBm', 'i_plus_n_dBm', 'sinr',
            'spectral_efficency_bps_hz', 'single_sector_capacity_mbps_km2',
            'x', 'y'
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
            num_sites,
            num_receivers,
            site_density,
            r_density,
            result['received_power'],
            result['path_loss'],
            result['interference'],
            result['ave_inf_pl'],
            result['ave_distance'],
            result['network_load'],
            result['noise'],
            result['i_plus_n'],
            result['sinr'],
            result['spectral_efficiency'],
            result['capacity_mbps_km2'],
            result['x'],
            result['y'],
            ))

    results_file.close()


def write_lookup_table(
    total_sites_required, received_power, interference, noise, i_plus_n,
    cell_edge_spectral_efficency, cell_edge_sinr, single_sector_capacity_mbps_km2,
    area_capacity_mbps_km2, network_efficiency, environment, operator, technology,
    frequency, bandwidth, mast_height, area_site_density, generation,
    postcode_sector_name):

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
            'frequency_GHz', 'bandwidth_MHz', 'mast_height_m',
            'num_sites', 'site_density_km2', 'generation',
            'received_power_dBm', 'interference_dBm', 'noise_dBm',
            'i_plus_n_dBm', 'sinr', 'spectral_efficency_bps_hz',
            'single_sector_capacity_mbps_km2',
            'area_capacity_mbps_km2')
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
        total_sites_required,
        area_site_density,
        generation,
        received_power,
        interference,
        noise,
        i_plus_n,
        cell_edge_sinr,
        cell_edge_spectral_efficency,
        single_sector_capacity_mbps_km2,
        area_capacity_mbps_km2,
        ))

    lut_file.close()


def write_shapefile(data, postcode_sector_name, filename):

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


def run_simulator(postcode_sector_name, transmitter_type, simulation_parameters,
    spectrum_portfolio, mast_heights, site_densities, modulation_and_coding_lut):

    path = os.path.join(DATA_RAW, 'd_shapes', 'datashare_pcd_sectors', 'PostalSector.shp')
    geojson_postcode_sector = read_postcode_sector(postcode_sector_name, path)

    local_authority_ids = get_local_authority_ids(geojson_postcode_sector)

    geojson_postcode_sector['properties']['local_authority_ids'] = (
        local_authority_ids
        )

    postcode_sector_lut = import_area_lut(
        postcode_sector_name, local_authority_ids
        )

    postcode_sector_lut['area_km2'] = (shape(geojson_postcode_sector['geometry'])).area/1e6

    postcode_sector_lut['pop_density_km2'] = import_population_data(
        geojson_postcode_sector, postcode_sector_lut
        )

    environment = determine_environment(postcode_sector_lut)

    interfering_sites = generate_interfering_sites(
        geojson_postcode_sector, simulation_parameters
        )

    write_shapefile(
        interfering_sites, postcode_sector_name,
        '{}_interfering_sites.shp'.format(postcode_sector_name)
        )

    densities_to_test = site_densities[environment]

    transmitters = []

    for operator, technology, frequency, bandwidth, generation in spectrum_portfolio:
        for mast_height in mast_heights:
            time_step_idx = 0
            site_numbers_tested = []
            for density in densities_to_test[::-1]:
                # print('density {}'.format(density))

                total_sites_required = math.ceil(density * postcode_sector_lut['area_km2'])

                if total_sites_required in site_numbers_tested:
                    continue

                site_numbers_tested.append(total_sites_required)
                # print('site numbers tested {}'.format(site_numbers_tested))
                # print('raw number of total sites required {}'.format(total_sites_required))
                # print('len(transmitters) {}'.format(len(transmitters)))
                total_new_sites = math.ceil(total_sites_required - len(transmitters))
                # print('total_new_sites pre {}'.format(total_new_sites))
                if total_new_sites < 1:
                    total_new_sites = 1
                # print('total_new_sites post {}'.format(total_new_sites))

                if time_step_idx == 0:
                    transmitters, site_areas = find_and_deploy_new_site(
                            transmitters,
                            1, #build 1 site to start
                            interfering_sites,
                            geojson_postcode_sector,
                            simulation_parameters,
                            )

                else:
                    while len(transmitters) < total_sites_required:
                        transmitters, site_areas = find_and_deploy_new_site(
                                transmitters,
                                total_new_sites,
                                interfering_sites,
                                geojson_postcode_sector,
                                simulation_parameters,
                                )

                all_transmitters = return_single_list(transmitters, interfering_sites)

                receivers = generate_receivers(
                    geojson_postcode_sector,
                    site_areas,
                    postcode_sector_lut,
                    simulation_parameters,
                    )

                # for site_area in site_areas:
                #     print(site_area)
                #     print((shape(site_area['geometry']).area/1e6))

                print('number of receivers is {}'.format(len(receivers)))
                manager = SimulationManager(
                    geojson_postcode_sector, all_transmitters, site_areas,
                    receivers, simulation_parameters
                    )

                current_site_density = manager.site_density()

                print("{} GHz {}m Height {} Density, {}".format(
                    frequency, mast_height, round(current_site_density, 4),
                    generation
                    ))

                time_step_idx += 1

                manager.estimate_link_budget(
                    frequency, bandwidth, generation, mast_height,
                    environment, modulation_and_coding_lut,
                    simulation_parameters
                    )

                manager.populate_site_data()

                # single_sector_capacity_mbps, spectral_efficency = threshold_values_for_sites(
                #     manager, simulation_parameters
                #     )

                received_power, interference, noise, i_plus_n, spectral_efficency, \
                    sinr, single_sector_capacity_mbps = (
                        obtain_threshold_values(manager, simulation_parameters)
                        )

                results = get_results(manager)

                network_efficiency = calculate_network_efficiency(
                    spectral_efficency,
                    manager.energy_consumption(simulation_parameters)
                    )

                area_capacity_mbps = (
                    single_sector_capacity_mbps * simulation_parameters['sectorisation']
                    )
                # print('area_capacity_mbps {}'.format(area_capacity_mbps))
                current_site_density = manager.site_density()
                # print('current_site_density {}'.format(current_site_density))
                r_density = manager.receiver_density()

                write_shapefile(
                    transmitters, postcode_sector_name,
                    '{}_transmitters_{}.shp'.format(postcode_sector_name, current_site_density)
                    )

                num_sites = len(manager.sites)
                num_receivers = len(manager.receivers)

                write_results(results, frequency, bandwidth, num_sites, num_receivers,
                    current_site_density, environment, technology, generation, mast_height,
                    r_density, postcode_sector_name
                    )

                write_lookup_table(
                    total_sites_required, received_power, interference, noise, i_plus_n,
                    spectral_efficency, sinr, single_sector_capacity_mbps,
                    area_capacity_mbps, network_efficiency, environment, operator,
                    technology, frequency, bandwidth, mast_height, current_site_density,
                    generation, postcode_sector_name
                    )

                write_shapefile(
                    site_areas, postcode_sector_name,
                    '{}_cell_areas_{}.shp'.format(postcode_sector_name, current_site_density)
                    )

                write_shapefile(
                    receivers, postcode_sector_name,
                    '{}_receivers_{}.shp'.format(postcode_sector_name, current_site_density)
                    )

                manager = []
                site_areas = []
                print('--------------------')
