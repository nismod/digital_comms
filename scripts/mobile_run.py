"""
Model runner to use in place of smif for standalone modelruns
- run over multiple years
- make rule-based intervention decisions at each timestep

"""
import configparser
import csv
import itertools
import os
import pprint
import glob

import fiona
from collections import defaultdict

from digital_comms.mobile_network.model import NetworkManager
from digital_comms.mobile_network.interventions import decide_interventions

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')
SHAPES_INPUT_PATH = os.path.join(BASE_PATH, 'raw', 'd_shapes')
SYSTEM_OUTPUT_PATH = os.path.join(BASE_PATH, '..','results')


def load_local_authority_districts():
    """
    Load in Local Authority District (LAD) shapes and extract id information.

    """
    lads = []

    lad_shapes = os.path.join(
        SHAPES_INPUT_PATH, 'lad_uk_2016-12', 'lad_uk_2016-12.shp'
        )

    with fiona.open(lad_shapes, 'r') as lad_shape:
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
                lads.append({
                    "id": lad['properties']['name'],
                    "name": lad['properties']['desc'],
                })
    return lads


def load_postcode_sectors():
    """
    Load in postcode sector information.

    """
    pcd_sectors = []
    PCD_SECTOR_FILENAME = os.path.join(INTERMEDIATE, 'mobile_model_inputs',
        '_processed_postcode_sectors.csv'
    )

    with open(PCD_SECTOR_FILENAME, 'r') as source:
        reader = csv.DictReader(source)
        for pcd_sector in reader:
            pcd_sectors.append({
                "id": pcd_sector['id'].replace(" ", ""),
                "lad_id": pcd_sector['lad'],
                "area_km2": float(pcd_sector['area_km2'])
                })

    return pcd_sectors


def load_population_scenario_data():
    """
    Load in population scenario data.

    """
    scenario_files = {
        scenario: os.path.join(BASE_PATH, 'raw', 'b_mobile_model',
        'mobile_model_1.0', 'scenario_data',
        'population_{}_pcd.csv'.format(scenario))
        for scenario in POPULATION_SCENARIOS
    }

    population_by_scenario_year_pcd = {
        scenario: {
            year: {} for year in TIMESTEPS
        }
        for scenario in POPULATION_SCENARIOS
    }

    for scenario, filename in scenario_files.items():
        with open(filename, 'r') as scenario_file:
            scenario_reader = csv.reader(scenario_file)
            for year, pcd_sector, population in scenario_reader:
                year = int(year)
                if year in TIMESTEPS:
                    population_by_scenario_year_pcd[scenario][year][pcd_sector] = (
                        int(population)
                    )

    return population_by_scenario_year_pcd


def load_user_throughput_scenarios():
    """
    Load in user throughput scenario data.

    """
    user_throughput_by_scenario_year = {
        scenario: {} for scenario in THROUGHPUT_SCENARIOS
    }

    THROUGHPUT_FILENAME = os.path.join(BASE_PATH, 'raw', 'b_mobile_model',
        'mobile_model_1.0', 'scenario_data', 'monthly_data_growth_scenarios.csv'
    )

    with open(THROUGHPUT_FILENAME, 'r') as throughput_file:
        reader = csv.reader(throughput_file)
        next(reader)
        for year, low, base, high in reader:
            year = int(year)
            if "high" in THROUGHPUT_SCENARIOS:
                user_throughput_by_scenario_year["high"][year] = float(high)
            if "baseline" in THROUGHPUT_SCENARIOS:
                user_throughput_by_scenario_year["baseline"][year] = float(base)
            if "low" in THROUGHPUT_SCENARIOS:
                user_throughput_by_scenario_year["low"][year] = float(low)

    return user_throughput_by_scenario_year


def load_initial_system():
    """
    Load in initial system of mobile sites.

    """
    SYSTEM_FILENAME = os.path.join(INTERMEDIATE, 'mobile_model_inputs',
        'final_processed_sites.csv'
    )

    initial_system = []

    with open(SYSTEM_FILENAME, 'r') as system_file:
        reader = csv.DictReader(system_file)
        for pcd_sector in reader:
            if int(pcd_sector['lte_4G']):
                frequency = ['800', '1800', '2600']
                technology = 'LTE'
            else:
                frequency = []
                technology = ''
            initial_system.append({
                'pcd_sector': pcd_sector['id'].replace(' ', ''),
                'site_ngr': pcd_sector['name'],
                'build_date': 2016,
                'technology': technology,
                'frequency': frequency,
                'type': 'macrocell_site',
                'capex': 0,
                'opex': 20000
            })

    return initial_system


def load_capacity_lookup_table():
    """
    Load in capacity density lookup table.

    """
    PATH_LIST = glob.iglob(os.path.join(INTERMEDIATE,
        'system_simulator', '*capacity_lookup_table*.csv'), recursive=True
    )

    capacity_lookup_table = {}

    for path in PATH_LIST:
        with open(path, 'r') as capacity_lookup_file:
            reader = csv.DictReader(capacity_lookup_file)
            for row in reader:

                environment = row["environment"].lower()
                frequency = str(int(float(row["frequency_GHz"]) * 1e3))
                bandwidth = str(row["bandwidth_MHz"])
                density = float(row["sites_per_km2"])
                capacity = float(row["capacity_mbps_km2"])

                if (environment, frequency, bandwidth) \
                    not in capacity_lookup_table:
                    capacity_lookup_table[(
                        environment, frequency, bandwidth)
                        ] = []

                capacity_lookup_table[(
                    environment, frequency, bandwidth
                    )].append((
                        density, capacity
                    ))

            for key, value_list in capacity_lookup_table.items():
                value_list.sort(key=lambda tup: tup[0])

    return capacity_lookup_table


def load_clutter_geotype_lookup_table():
    """
    Load in clutter geotype lookup table.

    """
    CLUTTER_GEOTYPE_FILENAME = os.path.join(INTERMEDIATE, 'mobile_model_inputs',
        'lookup_table_geotype.csv'
    )

    clutter_lookup = []

    with open(CLUTTER_GEOTYPE_FILENAME, 'r') as clutter_geotype_file:
        reader = csv.DictReader(clutter_geotype_file)
        for row in reader:
            geotype = row['geotype'].lower()
            population_density = float(row['population_density'])
            clutter_lookup.append((population_density, geotype))

        clutter_lookup.sort(key=lambda tup: tup[0])

    return clutter_lookup


def write_lad_results(network_manager, folder, year, pop_scenario,
    throughput_scenario, intervention_strategy, cost_by_lad):
    """
    Write LAD results to .csv file.

    """
    suffix = _get_suffix(pop_scenario, throughput_scenario, intervention_strategy)
    if not os.path.exists(folder):
        os.mkdir(folder)
    metrics_filename = os.path.join(folder, 'metrics_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        metrics_file = open(metrics_filename, 'w', newline='')
        metrics_writer = csv.writer(metrics_file)
        metrics_writer.writerow(
            ('year', 'area_id', 'area_name', 'cost', 'demand', 'capacity',
            'capacity_deficit', 'population', 'pop_density'))
    else:
        metrics_file = open(metrics_filename, 'a', newline='')
        metrics_writer = csv.writer(metrics_file)

    for lad in network_manager.lads.values():
        area_id = lad.id
        area_name = lad.name
        cost = cost_by_lad[lad.id]
        demand = lad.demand()
        capacity = lad.capacity()
        capacity_deficit = capacity - demand
        pop = lad.population
        pop_d = lad.population_density

        metrics_writer.writerow(
            (year, area_id, area_name, cost, demand, capacity,
            capacity_deficit, pop, pop_d))

    metrics_file.close()


def write_pcd_results(network_manager, folder, year, pop_scenario,
    throughput_scenario, intervention_strategy, cost_by_pcd):
    """
    Write postcode sector results to .csv file.

    """
    suffix = _get_suffix(pop_scenario, throughput_scenario, intervention_strategy)
    if not os.path.exists(folder):
        os.mkdir(folder)
    metrics_filename = os.path.join(folder,
        'pcd_metrics_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        metrics_file = open(metrics_filename, 'w', newline='')
        metrics_writer = csv.writer(metrics_file)
        metrics_writer.writerow(
            ('year', 'postcode', 'cost', 'demand', 'capacity',
            'capacity_deficit', 'population', 'pop_density'))
    else:
        metrics_file = open(metrics_filename, 'a', newline='')
        metrics_writer = csv.writer(metrics_file)

    for pcd in network_manager.postcode_sectors.values():
        demand = pcd.demand
        capacity = pcd.capacity
        capacity_deficit = capacity - demand
        pop = pcd.population
        pop_d = pcd.population_density
        cost = cost_by_pcd[pcd.id]

        metrics_writer.writerow(
            (year, pcd.id, cost, demand, capacity,
            capacity_deficit, pop, pop_d))

    metrics_file.close()


def write_decisions(decisions, folder, year, pop_scenario,
    throughput_scenario, intervention_strategy):
    """
    Write decisions to .csv file.

    """
    suffix = _get_suffix(pop_scenario, throughput_scenario, intervention_strategy)
    # folder = os.path.join(BASE_PATH, '..', 'results')
    if not os.path.exists(folder):
        os.mkdir(folder)
        # os.mkdir(os.path.join(folder, 'mobile_model_1.0'))
    decisions_filename =  os.path.join(folder, 'decisions_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        decisions_file = open(decisions_filename, 'w', newline='')
        decisions_writer = csv.writer(decisions_file)
        decisions_writer.writerow(
            ('year', 'pcd_sector', 'site_ngr', 'build_date',
            'type', 'technology', 'frequency', 'bandwidth'))
    else:
        decisions_file = open(decisions_filename, 'a', newline='')
        decisions_writer = csv.writer(decisions_file)

    for intervention in decisions:
        pcd_sector = intervention['pcd_sector']
        site_ngr = intervention['site_ngr']
        build_date = intervention['build_date']
        intervention_type = intervention['type']
        technology = intervention['technology']
        frequency = intervention['frequency']
        bandwidth = intervention['bandwidth']

        decisions_writer.writerow(
            (year, pcd_sector, site_ngr, build_date, intervention_type,
            technology, frequency, bandwidth))

    decisions_file.close()


def write_spend(spend, folder, year, pop_scenario,
    throughput_scenario, intervention_strategy):
    """
    Write asset spending results to .csv file.

    """
    suffix = _get_suffix(pop_scenario, throughput_scenario, intervention_strategy)
    if not os.path.exists(folder):
        os.mkdir(folder)
    spend_filename = os.path.join(folder, 'spend_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        spend_file = open(spend_filename, 'w', newline='')
        spend_writer = csv.writer(spend_file)
        spend_writer.writerow(
            ('year', 'pcd_sector', 'lad', 'item', 'cost'))
    else:
        spend_file = open(spend_filename, 'a', newline='')
        spend_writer = csv.writer(spend_file)

    for pcd_sector, lad, item, cost in spend:
        spend_writer.writerow(
            (year, pcd_sector, lad, item, cost))

    spend_file.close()


def _get_suffix(pop_scenario, throughput_scenario, intervention_strategy):
    """
    Get the filename suffix for each scenario and strategy variant.

    """
    suffix = 'pop_{}_throughput_{}_strategy_{}'.format(
        pop_scenario, throughput_scenario, intervention_strategy)

    suffix = suffix.replace('baseline', 'base')

    return suffix


if __name__ == '__main__':

    ################################################################
    # START RUNNING MODEL
    # - run from BASE_YEAR to END_YEAR in TIMESTEP_INCREMENT steps
    # - run over population scenario / demand scenario / intervention
    #  strategy combinations
    # - output demand, capacity, opex, energy demand, built interventions,
    #   build costs per year
    ################################################################

    folder = os.path.join(BASE_PATH, '..', 'results', 'mobile_outputs')

    BASE_YEAR = 2020
    END_YEAR = 2030
    TIMESTEP_INCREMENT = 1
    TIMESTEPS = range(BASE_YEAR, END_YEAR + 1, TIMESTEP_INCREMENT)

    POPULATION_SCENARIOS = [
        "high",
        "baseline",
        "low",
    ]
    THROUGHPUT_SCENARIOS = [
        "high",
        "baseline",
        "low",
    ]
    INTERVENTION_STRATEGIES = [
        "minimal",
        "macrocell",
        "macrocell_700",
        "small_cell",
        "small_cell_and_spectrum"
    ]

    MARKET_SHARE = 0.25
    ANNUAL_BUDGET = (2 * 10 ** 9) * MARKET_SHARE
    SERVICE_OBLIGATION_CAPACITY = 0
    BUSY_HOUR_TRAFFIC_PERCENTAGE = 15
    COVERAGE_THRESHOLD = 2

    simulation_parameters = {
        'market_share': MARKET_SHARE,
        'annual_budget': ANNUAL_BUDGET,
        'service_obligation_capacity': SERVICE_OBLIGATION_CAPACITY,
        'busy_hour_traffic_percentage': BUSY_HOUR_TRAFFIC_PERCENTAGE,
        'coverage_threshold': COVERAGE_THRESHOLD,
        'penetration': 80,
        'channel_bandwidth_700': '10',
        'channel_bandwidth_800': '10',
        'channel_bandwidth_1800': '10',
        'channel_bandwidth_2600': '10',
        'channel_bandwidth_3500': '40',
        'macro_sectors': 3,
        'small_cell_sectors': 1,
        'mast_height': 30,
    }

    print('Loading local authority districts')
    lads = load_local_authority_districts()

    print('Loading postcode sectors')
    pcd_sectors = load_postcode_sectors()

    print('Loading population scenario data')
    population_by_scenario_year_pcd = load_population_scenario_data()

    print('Loading user throughput scenario data')
    user_throughput_by_scenario_year = load_user_throughput_scenarios()

    print('Loading initial system')
    initial_system = load_initial_system()

    print('Loading lookup table')
    capacity_lookup_table = load_capacity_lookup_table()

    print('Loading lookup table')
    clutter_lookup = load_clutter_geotype_lookup_table()

    for pop_scenario, throughput_scenario, intervention_strategy in [
            # ('low', 'low', 'minimal'),
            # ('baseline', 'baseline', 'minimal'),
            # ('high', 'high', 'minimal'),

            # ('low', 'low', 'macrocell'),
            # ('baseline', 'baseline', 'macrocell'),
            ('high', 'high', 'macrocell'),

            # ('low', 'low', 'small_cell'),
            # ('baseline', 'baseline', 'small_cell'),
            # ('high', 'high', 'small_cell'),

            # ('low', 'low', 'small_cell_and_spectrum'),
            # ('baseline', 'baseline', 'small_cell_and_spectrum'),
            # ('high', 'high', 'small_cell_and_spectrum'),
        ]:
        print("Running:", pop_scenario, throughput_scenario,
            intervention_strategy)

        assets = initial_system[:]
        for year in TIMESTEPS:
            print("-", year)

            for pcd_sector in pcd_sectors:
                try:
                    pcd_sector_id = pcd_sector["id"]
                    pcd_sector["population"] = (
                        population_by_scenario_year_pcd \
                            [pop_scenario][year][pcd_sector_id])
                    pcd_sector["user_throughput"] = (
                        user_throughput_by_scenario_year \
                            [throughput_scenario][year])
                except:
                    pass

            budget = simulation_parameters['annual_budget']
            service_obligation_capacity = (
                simulation_parameters['service_obligation_capacity'])

            if year == BASE_YEAR:
                system = NetworkManager(lads, pcd_sectors, assets,
                    capacity_lookup_table, clutter_lookup,
                    simulation_parameters)

            interventions_built, budget, spend = decide_interventions(
                intervention_strategy, budget, service_obligation_capacity,
                system, year, simulation_parameters)

            assets += interventions_built

            system = NetworkManager(lads, pcd_sectors, assets,
                capacity_lookup_table, clutter_lookup,
                simulation_parameters)

            cost_by_lad = defaultdict(int)
            cost_by_pcd = defaultdict(int)
            for pcd, lad, item, cost in spend:
                cost_by_lad[lad] += cost
                cost_by_pcd[pcd] += cost

            write_lad_results(system, folder, year, pop_scenario, throughput_scenario,
                intervention_strategy, cost_by_lad)
            write_pcd_results(system, folder, year, pop_scenario, throughput_scenario,
                intervention_strategy, cost_by_pcd)
            write_decisions(interventions_built, folder, year, pop_scenario,
                throughput_scenario, intervention_strategy)
            write_spend(spend, folder, year, pop_scenario, throughput_scenario,
                intervention_strategy)
