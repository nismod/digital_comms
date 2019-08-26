import configparser
import csv
import glob
import itertools
import logging
import os
import fiona
from rtree import index

from shapely.geometry import shape

from digital_comms.fixed_network.model import NetworkManager
from digital_comms.fixed_network.interventions import decide_interventions

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

SCENARIO_DATA = os.path.join(BASE_PATH, 'scenarios')
DATA_PROCESSED_INPUTS = os.path.join(BASE_PATH, 'processed')
RESULTS_DIRECTORY = os.path.join(BASE_PATH, '..', 'results')


def read_data(path):
    """
    Read in a .csv file. Convert each line to single dict, and then append to a list.

    Parameters
    ----------
    filepath : string
        This is a directory string to point to the desired file from the BASE_PATH.

    Returns
    -------
    list_of_dicts
        Returns a list of dicts, with each line [an asset or link] in the .csv forming its own
        dict

    """
    with open(path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for item in reader:
            yield {
                'timestep': item['timestep'],
                'dwellings': item['dwellings'],
                'lad16nm': item['lad16nm'],
                'lad_uk_2016': item['lad_uk_2016'],
            }


def load_local_authority_districts(path):
    """
    Load in Local Authority District (LAD) shapes and extract id information.

    """
    lads = []

    with fiona.open(path, 'r') as lad_shape:
        for lad in lad_shape:
            if not lad['properties']['name'].startswith((
                'E06000053',
                'S12000027',
                'N09000001',
                'N09000002',
                'N09000003',
                'N09000004',
                'N09000005',
                'N09000006',
                'N09000007',
                'N09000008',
                'N09000009',
                'N09000010',
                'N09000011',
                )):
                geom_area = round(shape(lad['geometry']).area / 1e6, 1)
                lads.append({
                    'id': lad['properties']['name'],
                    'name': lad['properties']['desc'],
                    'area': geom_area
                })

    return lads


def read_existing_coverage(path, lads):

    existing_system = []

    with open(path, 'r') as system_file:
        reader = csv.DictReader(system_file)
        for line in reader:
            existing_system.append({
                'lad': line['laua'],
                'lad_name': line['laua_name'],
                'premises': line['All Premises'],
                'fttc_availability': line['SFBB availability (% premises)'],
                'gfast_availability': line['UFBB availability (% premises)'],
                'fttp_availability': line['Full Fibre availability (% premises)'],
            })

    output = []

    for lad in lads:
        # {'id': 'E06000001', 'name': 'Hartlepool', 'area': 98.4}
        for datum in existing_system:
            #{'lad': 'S12000033', 'lad_name': 'Aberdeen City',
            # 'premises': '111307', 'sfbb_availability': '85.3',
            # 'ufbb_availability': '8.2', 'fttp_availability': '4.6'}
            if lad['id'] == datum['lad']:
                output.append({
                    'id': lad['id'],
                    'name': lad['name'],
                    'area': lad['area'],
                    'ofcom_premises': datum['premises'],
                    'fttc_availability': datum['fttc_availability'],
                    'gfast_availability': datum['gfast_availability'],
                    'fttp_availability': datum['fttp_availability'],
                })

    return output


def dwelling_density_by_lad(lads, dwellings, year):

    dwelling_data = []

    for dwelling_datum in dwellings:
        if int(dwelling_datum['timestep']) == year:
            dwelling_data.append(dwelling_datum)

    output = []

    for lad in lads:
        #{'id': 'S12000039', 'name': 'West Dunbartonshire', 'area': 182.8}
        for dwelling_datum in dwelling_data:
            #{'timestep': '2015', 'dwellings': '61070', 'lad16nm': 'Cherwell',
            # 'lad_uk_2016': 'E07000177'}
            if lad['id'] == dwelling_datum['lad_uk_2016']:
                output.append({
                    'id': lad['id'],
                    'name': lad['name'],
                    'area': lad['area'],
                    'timestep': year,
                    'dwellings': int(dwelling_datum['dwellings']),
                    'premises_density_km2': (
                        round(int(dwelling_datum['dwellings']) / float(lad['area']), 1)
                    ),
                    # 'premises accuracy': (
                    #     int(dwelling_datum['dwellings']) -
                    #     int(lad['ofcom_premises'])
                    # ),
                    'fttc_availability': (
                        int(dwelling_datum['dwellings']) *
                        float(lad['fttc_availability']) / 100
                    ),
                    'gfast_availability': (
                        int(dwelling_datum['dwellings']) *
                        float(lad['gfast_availability']) / 100
                    ),
                    'fttdp_availability': 0,
                    'fttp_availability': (
                        int(dwelling_datum['dwellings']) *
                        float(lad['fttp_availability']) / 100
                    ),
                })

    return output


def read_exchange_areas(path):
    """
    Read all exchange area shapes

    Data Schema
    -----------
    * id: 'string'
        Unique exchange id
    """
    with fiona.open(path, 'r') as reader:
        for item in reader:
            geom_area = shape(item['geometry']).area / 1e6
            yield {
                'id': item['id'],
                'area': geom_area,
                }


def estimate_dwelling_density(exchanges, lads):

    output = []

    for lad in lads:
        #{'id': 'E07000156', 'name': 'Wellingborough', 'area': 163.0,
        # 'timestep': 2015, 'dwellings': '33970', 'premises_density_km2': 208.4}
        lad_area = lad['area']
        for exchange in exchanges:
            #{'id': '1434', 'area': 97.92134575221058}
            exchange_area = exchange['area']
            # print(exchange_area / lad_area, int(lad['dwellings']),
            # exchange_area / lad_area * int(lad['dwellings']))
            output.append({
                'exchange_id': exchange['id'],
                'exchange_area': exchange['area'],
                'proportion_of_lad_area': exchange_area / lad_area,
                'lad_id': lad['id'],
                'lad_name': lad['name'],
                # 'lad_area': lad['area'],
                'timestep': lad['timestep'],
                # 'lad_dwellings': lad['dwellings'],
                # 'lad_premises_density_km2': lad['premises_density_km2'],
                'exchange_dwellings': (
                    exchange_area / lad_area * int(lad['dwellings'])
                ),
                'exchange_dwellings_density_km2': (
                    exchange_area / lad_area * int(lad['dwellings'] / exchange['area'])
                ),
                'fttp_availability': exchange_area / lad_area * int(lad['fttp_availability']),
                'fttdp_availability': exchange_area / lad_area * int(lad['fttdp_availability']),
                'gfast_availability': exchange_area / lad_area * int(lad['gfast_availability']),
                'fttc_availability': exchange_area / lad_area * int(lad['fttc_availability']),
            })

    return output


def write_decisions(decisions, path, year, technology, policy):
    """

    Write out the infrastructure decisions made annually for each technology and policy.

    Parameters
    ----------
    decisions : list_of_tuples
        Contains the upgraded assets with the deployed technology and affliated costs
    year : int
        The year of deployment.
    technology : string
        The new technology deployed.
    policy : string
        The policy used to encourage deployment.

    """
    decisions_filename = os.path.join(path,'decisions_{}_{}.csv'.format(technology, policy))

    if year == BASE_YEAR:
        decisions_file = open(decisions_filename, 'w', newline='')
        decisions_writer = csv.writer(decisions_file)
        decisions_writer.writerow(
            ('year', 'asset_id', 'technology', 'policy', 'capital_investment_type'))
    else:
        decisions_file = open(decisions_filename, 'a', newline='')
        decisions_writer = csv.writer(decisions_file)

    # output and report results for this timestep
    for intervention in decisions:
        # Output decisions
        year = year
        asset_id = intervention[0]
        technology = intervention[1]
        policy = intervention[2]
        capital_investment_type = intervention[3]

        decisions_writer.writerow(
            (
                year, asset_id, technology, policy, capital_investment_type
            )
        )

    decisions_file.close()


def write_spend(decisions, path, year, technology, policy):
    """Write out spending decisions made annually for each technology and policy.

    Parameters
    ----------
    decisions : list_of_tuples
        Contains the upgraded assets with the deployed technology and affliated costs
    year : int
        The year of deployment.
    technology : string
        The new technology deployed.
    policy : string
        The policy used to encourage deployment.
    spend_type : string
        Whether the spent capital was purely market delivered, or subsidised.
    spend : int
        The amount of capital spent (£).

    """
    decisions_filename = os.path.join(
        path, 'spend_{}_{}.csv'.format(technology, policy))

    if year == BASE_YEAR:
        decisions_file = open(decisions_filename, 'w', newline='')
        decisions_writer = csv.writer(decisions_file)
        decisions_writer.writerow(
            ('year', 'asset_id', 'technology', 'policy', 'capital_investment_type',
            'total_upgrade_cost', 'total_private_investment', 'total_subsidy')
        )

    else:
        decisions_file = open(decisions_filename, 'a', newline='')
        decisions_writer = csv.writer(decisions_file)

    # output and report results for this timestep
    for intervention in decisions:
        # Output decisions
        year = year
        asset_id = intervention[0]
        technology = intervention[1]
        policy = intervention[2]
        capital_investment_type = intervention[3]
        total_upgrade_cost = intervention[4]
        total_private_investment = intervention[5]
        total_subsidy = intervention[6]

        decisions_writer.writerow(
            (
                asset_id, year, technology, policy, capital_investment_type,
                total_upgrade_cost, total_private_investment, total_subsidy
            )
        )

    decisions_file.close()


def write_exchange_results(system, path, year, technology, policy):

    results_filename = os.path.join(
        path, 'exchange_{}_{}.csv'.format(technology, policy))

    if year == BASE_YEAR:
        results_file = open(results_filename, 'w', newline='')
        results_writer = csv.writer(results_file)
        results_writer.writerow(
            (
                'exchange', 'year', 'technology', 'policy',
                'average_capacity', 'fttp', 'fttdp', 'fttc',
                'total_prems'
            )
        )

    else:
        results_file = open(results_filename, 'a', newline='')
        results_writer = csv.writer(results_file)

    coverage = system.coverage()
    #{'id': '5393', 'percentage_of_premises_with_fttp': 9,
    # 'percentage_of_premises_with_fttdp': 9,
    # 'percentage_of_premises_with_fttc': 9,
    # 'sum_of_premises': 8924}
    capacity = system.capacity()
    # {'id': '5390', 'average_capacity': 331},

    for area_dict in coverage:
        for area_dict_2 in capacity:
            if area_dict['id'] == area_dict_2['id']:
                results_writer.writerow(
                    (
                        area_dict['id'],
                        year,
                        technology,
                        policy,
                        area_dict_2['average_capacity'],
                        area_dict['percentage_of_premises_with_fttp'],
                        area_dict['percentage_of_premises_with_fttdp'],
                        area_dict['percentage_of_premises_with_fttc'],
                        # area_dict['percentage_of_premises_with_docsis3'],
                        # area_dict['percentage_of_premises_with_adsl'],
                        area_dict['sum_of_premises'],
                    )
                )

    results_file.close()


def write_lad_results(system, exchange_to_lad_lut, path, year, technology, policy):

    results_filename = os.path.join(
        path, 'lad_{}_{}.csv'.format(technology, policy))

    if year == BASE_YEAR:
        results_file = open(results_filename, 'w', newline='')
        results_writer = csv.writer(results_file)
        results_writer.writerow(
            (
                'lad', 'year', 'technology', 'policy', 'average_capacity',
                'fttp', 'fttdp', 'fttc', 'total_prems'
            )
        ) #'docsis3', 'adsl',

    else:
        results_file = open(results_filename, 'a', newline='')
        results_writer = csv.writer(results_file)

    coverage = system.coverage()
    #{'id': '5393', 'percentage_of_premises_with_fttp': 9,
    # 'percentage_of_premises_with_fttdp': 9,
    # 'percentage_of_premises_with_fttc': 9,
    # 'sum_of_premises': 8924}
    capacity = system.capacity()
    # {'id': '5390', 'average_capacity': 331},

    # exchange_to_lad_lut
    # {'exchange_id': '0', 'exchange_area': 6.033454232191916,
    # 'proportion_of_lad_area': 0.01756975606345928,
    # 'lad_id': 'E06000031', 'lad_name': 'Peterborough'}
    unique_lads = set()
    print(len(exchange_to_lad_lut))
    for item in exchange_to_lad_lut:
        print(item['lad_id'])
        unique_lads.add(item['lad_id'])
    print(unique_lads)

    for area_dict in coverage:
        for area_dict_2 in capacity:
            if area_dict['id'] == area_dict_2['id']:
                results_writer.writerow(
                    (
                        area_dict['id'],
                        year,
                        technology,
                        policy,
                        area_dict_2['average_capacity'],
                        area_dict['percentage_of_premises_with_fttp'],
                        area_dict['percentage_of_premises_with_fttdp'],
                        area_dict['percentage_of_premises_with_fttc'],
                        area_dict['percentage_of_premises_with_docsis3'],
                        area_dict['percentage_of_premises_with_adsl'],
                        area_dict['sum_of_premises'],
                    )
                )

    results_file.close()


if __name__ == "__main__":

    print("Running fixed broadband runner.py")

    TIMESTEPS = [2015, 2020]
    BASE_YEAR = TIMESTEPS[0]

    parameters = {
        'annual_budget': 1e7,
        'max_market_investment_per_dwelling': 1000,
        'annual_subsidy': 1e7,
        'subsidy_rural_percentile': 0.66,
        'subsidy_outsidein_percentile': 0.0,
        'market_match_funding': 1e7,
    }

    lad_shapes = os.path.join('data', 'raw', 'd_shapes', 'lad_uk_2016-12', 'lad_uk_2016-12.shp')
    #[{'id': }, {'name': }, {'area': }]
    lads = load_local_authority_districts(lad_shapes)

    path = os.path.join('data', 'raw', 'a_fixed_model', 'ofcom_initial_system', 'fixed-laua-data_2019.csv')
    # [{'id': ,'name': ,'area': , 'ofcom_premises': , 'sfbb_availability': ,
    # 'ufbb_availability': , 'fttp_availability': }]
    lads = read_existing_coverage(path, lads)

    path = os.path.join('data', 'raw', 'd_shapes', 'all_exchange_areas', '_exchange_areas_fixed.shp')
    # {'id': , 'area': , }
    exchanges = read_exchange_areas(path)

    for scenario, technology, policy in [
        # ('baseline', 'fttdp', 'market_insideout'),
        # ('baseline', 'fttdp', 'subsidy_rural'),
        ('baseline', 'fttdp', 'subsidy_outsidein'),
        # ('baseline', 'fttp', 'market_insideout'),
        # ('baseline', 'fttp', 'subsidy_rural'),
        # ('baseline', 'fttp', 'subsidy_outsidein'),

        # ('0-unplanned', 'fttdp', 'market_insideout'),
        # ('0-unplanned', 'fttdp', 'subsidy_rural'),
        # ('0-unplanned', 'fttdp', 'subsidy_outsidein'),
        # ('0-unplanned', 'fttp', 'market_insideout'),
        # ('0-unplanned', 'fttp', 'subsidy_rural'),
        # ('0-unplanned', 'fttp', 'subsidy'_outsidein'),

        # ('1-new-cities', 'fttdp', 'market_insideout'),
        # ('1-new-cities', 'fttdp', 'subsidy_rural'),
        # ('1-new-cities', 'fttdp', 'subsidy_outsidein'),
        # ('1-new-cities', 'fttp', 'market_insideout'),
        # ('1-new-cities', 'fttp', 'subsidy_rural'),
        # ('1-new-cities', 'fttp', 'subsidy_outsidein'),

        # ('2-expansion', 'fttdp', 'market_insideout'),
        # ('2-expansion', 'fttdp', 'subsidy_rural'),
        # ('2-expansion', 'fttdp', 'subsidy_outsidein'),
        # ('2-expansion', 'fttp', 'market_insideout'),
        # ('2-expansion', 'fttp', 'subsidy_rural'),
        # ('2-expansion', 'fttp', 'subsidy_outsidein'),

        ]:

        print('Working on {}, {} and {}'.format(scenario, technology, policy))

        data_path = os.path.join('data','raw','e_dem_and_buildings','arc_dwellings','arc_dwellings__{}.csv'.format(scenario))

        dwellings = read_data(data_path)

        for year in TIMESTEPS:

            print('Processing {}'.format(year))

            lads = dwelling_density_by_lad(lads, dwellings, year)

            #THIS DOES NOT CORRECTLY ALLOCATE - NEED TO GENERATE EX TO LAD LUT
            exchanges = estimate_dwelling_density(exchanges, lads)

            # Simulate first year
            if year == BASE_YEAR:
                system = NetworkManager(exchanges, parameters)

            # actually decide which interventions to build
            built_interventions = decide_interventions(system, year, technology, policy, parameters)

            # give the interventions to the system model
            system.upgrade(built_interventions)

            # write out the decisions
            path = os.path.join(RESULTS_DIRECTORY, 'fixed_outputs')
            write_decisions(built_interventions, path, year, technology, policy)

            write_spend(built_interventions, path, year, technology, policy)

            write_exchange_results(system, path, year, technology, policy)

            # # write_lad_results(system, exchange_to_lad_lut, path, year, technology, policy, roll_out)

            print('Completed {} for {}, {} and {}'.format(year, scenario, technology, policy))
