"""
Model runner to use in place of smif for standalone modelruns
- run over multiple years
- make rule-based intervention decisions at each timestep
"""
# pylint: disable=C0103
import configparser
import csv
import itertools
import os
import pprint
import glob

import fiona

from collections import defaultdict
import sys
sys.path.append("..")

from digital_comms.mobile_network.model import NetworkManager
from digital_comms.mobile_network.interventions import decide_interventions

################################################################
# SETUP MODEL RUN CONFIGURATION
# - timesteps, scenarios, strategies
# - data files base path
################################################################

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

SYSTEM_INPUT_PATH = os.path.join(
    BASE_PATH, 'raw', 'b_mobile_model','mobile_model_1.0'
    )
INTERMEDIATE_PATH = os.path.join(BASE_PATH, 'intermediate')
SHAPES_INPUT_PATH = os.path.join(BASE_PATH, 'raw', 'd_shapes')
SYSTEM_OUTPUT_PATH = os.path.join(BASE_PATH, '..','results')

TIMESTEPS = [2015, 2020, 2030, 2050]
BASE_YEAR = TIMESTEPS[0]

POPULATION_SCENARIOS = [
    "baseline",
    "0-unplanned",
    "1-new-cities",
    "2-expansion",
]

THROUGHPUT_SCENARIOS = [
    "high",
    "baseline",
    "low",
]
INTERVENTION_STRATEGIES = [
    "minimal",
    "macrocell-700-3500",
    "sectorisation",
    "macro_densification",
    "small-cell",
    "small-cell-and-spectrum",
    # "neutral-hosting",
    # "deregulation",
    # "cloud-ran",
]

MARKET_SHARE = 0.25
ANNUAL_BUDGET = (2 * 10 ** 9) * MARKET_SHARE
SERVICE_OBLIGATION_CAPACITY = 1000
PERCENTAGE_OF_TRAFFIC_IN_BUSY_HOUR = 0.15

################################################################
# LOAD REGIONS
# - LADs
# - Postcode Sectors
################################################################
print('Loading regions')

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

postcode_sectors = []
PCD_SECTOR_FILENAME = os.path.join(
    BASE_PATH, 'processed', '_processed_postcode_sectors.csv'
    )

with open(PCD_SECTOR_FILENAME, 'r') as source:
    reader = csv.DictReader(source)
    for pcd_sector in reader:
        postcode_sectors.append({
            "id": pcd_sector['postcode'].replace(" ", ""),
            "lad_id": pcd_sector['lad'],
            "area": float(pcd_sector['area']) / 1e6
        })

################################################################
# LOAD SCENARIO DATA
# - population by scenario: year, pcd_sector, population
# - user throughput demand by scenario: year, demand per capita (GB/month?)
################################################################
print('Loading scenario data')

#for arc
scenario_files = {
    scenario: os.path.join(
        SYSTEM_INPUT_PATH, 'scenario_data',
        'pcd_arc_population__{}.csv'.format(scenario))
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
        scenario_reader = csv.DictReader(scenario_file)

        for row in scenario_reader:
            year = int(row['year'])
            if year in TIMESTEPS:
                population = row['population']
                pcd_sector = row['postcode_sector']
                population_by_scenario_year_pcd[scenario][year][pcd_sector] \
                    = int(population)

user_throughput_by_scenario_year = {
    scenario: {} for scenario in THROUGHPUT_SCENARIOS
}

THROUGHPUT_FILENAME = os.path.join(
    SYSTEM_INPUT_PATH, 'scenario_data', 'monthly_data_growth_scenarios.csv'
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

################################################################
# LOAD INITIAL SYSTEM ASSETS/SITES
################################################################
print('Loading initial system')

SYSTEM_FILENAME = os.path.join(
    BASE_PATH, 'processed', 'final_processed_sites.csv'
    )

initial_system = []
#pcd_sector_ids = {pcd_sector["id"]: True for pcd_sector in postcode_sectors}
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
            'pcd_sector': pcd_sector['pcd_sector'].replace(' ', ''),
            'site_ngr': pcd_sector['id'],
            'type': pcd_sector['Anttype'],
            'build_date': 2016,
            'technology': technology,
            'frequency': frequency,
            'sectors': 3,
            # 'bandwidth': pcd_sector['id'],
        })

################################################################
# IMPORT LOOKUP TABLES
# - mobile capacity, by environment, frequency, bandwidth and site density
# - clutter environment geotype, by population density
################################################################
print('Loading lookup tables')

CAPACITY_LOOKUP_FILENAME = os.path.join(
    INTERMEDIATE_PATH, 'system_simulator'
    )
PATH_LIST = glob.iglob(os.path.join(
    INTERMEDIATE_PATH, 'system_simulator', '**/*.csv'), recursive=True)

capacity_lookup_table = {}

for path in PATH_LIST:
    with open(path, 'r') as capacity_lookup_file:
        reader = csv.DictReader(capacity_lookup_file)
        for row in reader:
            environment = row["environment"]
            frequency = row["frequency"].replace(' MHz', '')
            bandwidth = row["bandwidth"].replace(' ', '')
            mast_height = int(row['mast_height'])
            density = float(row["area_site_density"])
            capacity = float(row["area_capacity_mbps"])
            cell_edge_spectral_efficency = float(
                row['cell_edge_spectral_efficency']
                )
            network_efficiency = float(row['network_efficiency'])

            if (environment, frequency, bandwidth, mast_height) \
                not in capacity_lookup_table:
                capacity_lookup_table[(
                    environment, frequency, bandwidth, mast_height)
                    ] = []

            capacity_lookup_table[(
                environment, frequency, bandwidth, mast_height
                )].append((
                    density, capacity
                ))

        for key, value_list in capacity_lookup_table.items():
            value_list.sort(key=lambda tup: tup[0])


CLUTTER_GEOTYPE_FILENAME = os.path.join(
    SYSTEM_INPUT_PATH, 'lookup_tables', 'lookup_table_geotype.csv'
    )

clutter_lookup = []

with open(CLUTTER_GEOTYPE_FILENAME, 'r') as clutter_geotype_file:
    reader = csv.DictReader(clutter_geotype_file)
    for row in reader:
        geotype = row['geotype']
        population_density = float(row['population_density'])
        clutter_lookup.append((population_density, geotype))

    clutter_lookup.sort(key=lambda tup: tup[0])

def write_lad_results(network_manager, year, pop_scenario, throughput_scenario,
                      intervention_strategy, cost_by_lad):
    suffix = _get_suffix(
        pop_scenario, throughput_scenario, intervention_strategy
        )
    directory = os.path.join(SYSTEM_OUTPUT_PATH, 'mobile_outputs')
    metrics_filename = os.path.join(
        directory, 'metrics_{}.csv'.format(suffix)
        )

    if year == BASE_YEAR:
        if not os.path.exists(directory):
            os.makedirs(directory)
        metrics_file = open(metrics_filename, 'w', newline='')
        metrics_writer = csv.writer(metrics_file)
        metrics_writer.writerow(
            ('year', 'area_id', 'area_name', 'cost', 'demand',
            'capacity', 'capacity_deficit', 'population', 'area',
            'pop_density')
            )
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
        area = lad.area
        pop_d = lad.population_density

        metrics_writer.writerow(
            (year, area_id, area_name, cost, demand, capacity,
            capacity_deficit, pop, area, pop_d)
            )

    metrics_file.close()

def write_pcd_results(network_manager, year, pop_scenario, throughput_scenario,
                      intervention_strategy, cost_by_pcd):

    suffix = _get_suffix(
        pop_scenario, throughput_scenario, intervention_strategy
        )
    directory = os.path.join(SYSTEM_OUTPUT_PATH, 'mobile_outputs')
    metrics_filename = os.path.join(
        directory, 'pcd_metrics_{}.csv'.format(suffix)
        )

    if year == BASE_YEAR:
        if not os.path.exists(directory):
            os.makedirs(directory)
        metrics_file = open(metrics_filename, 'w', newline='')
        metrics_writer = csv.writer(metrics_file)
        metrics_writer.writerow(
            ('year', 'postcode', 'cost', 'demand', 'capacity',
            'capacity_deficit', 'population', 'pop_density', 'environment'))
    else:
        metrics_file = open(metrics_filename, 'a', newline='')
        metrics_writer = csv.writer(metrics_file)

    for pcd in network_manager.postcode_sectors.values():
        demand = pcd.demand
        capacity = pcd.capacity
        capacity_deficit = capacity - demand
        pop = pcd.population
        pop_d = pcd.population_density
        environment = pcd.clutter_environment
        cost = cost_by_pcd[pcd.id]

        metrics_writer.writerow(
            (year, pcd.id, cost, demand, capacity,
            capacity_deficit, pop, pop_d, environment)
            )

    metrics_file.close()

def write_decisions(decisions, year, pop_scenario,
    throughput_scenario, intervention_strategy):

    suffix = _get_suffix(pop_scenario, throughput_scenario, intervention_strategy)
    directory = os.path.join(SYSTEM_OUTPUT_PATH, 'mobile_outputs')
    decisions_filename = os.path.join(
        directory, 'decisions_{}.csv'.format(suffix)
        )

    if year == BASE_YEAR:
        if not os.path.exists(directory):
            os.makedirs(directory)
        decisions_file = open(decisions_filename, 'w', newline='')
        decisions_writer = csv.writer(decisions_file)
        decisions_writer.writerow((
            'year', 'pcd_sector', 'site_ngr', 'build_date',
            'type', 'technology', 'frequency', 'bandwidth',
            'sectors'))
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
        sectors = intervention['sectors']

        decisions_writer.writerow((
            year, pcd_sector, site_ngr, build_date,
            intervention_type, technology, frequency,
            bandwidth, sectors
            ))

    decisions_file.close()

def write_spend(interventions_built, year, pop_scenario,
    throughput_scenario, intervention_strategy):

    suffix = _get_suffix(
        pop_scenario, throughput_scenario, intervention_strategy
        )
    directory = os.path.join(SYSTEM_OUTPUT_PATH, 'mobile_outputs')
    spend_filename = os.path.join(
        directory, 'spend_{}.csv'.format(suffix)
        )

    if year == BASE_YEAR:
        if not os.path.exists(directory):
            os.makedirs(directory)
        spend_file = open(spend_filename, 'w', newline='')
        spend_writer = csv.writer(spend_file)
        spend_writer.writerow(
            ('year', 'pcd_sector', 'lad', 'item', 'cost'))
    else:
        spend_file = open(spend_filename, 'a', newline='')
        spend_writer = csv.writer(spend_file)

    for row in interventions_built:
        spend_writer.writerow(
            (row['year'], row['pcd_sector'], row['lad'], row['item'], row['cost']))

    spend_file.close()

def _get_suffix(pop_scenario, throughput_scenario,
    intervention_strategy):

    suffix = 'pop-{}_throughput-{}_strategy-{}'.format(
        pop_scenario, throughput_scenario, intervention_strategy)
    # for length, use 'base' for baseline scenarios
    suffix = suffix.replace('baseline', 'base')
    return suffix

################################################################
# START RUNNING MODEL
# - run from BASE_YEAR to END_YEAR in TIMESTEP_INCREMENT steps
# - run over population scenario / demand scenario / intervention
# strategy combinations
# - output demand, capacity, opex, energy demand, built interventions,
# build costs per year
################################################################

for pop_scenario, throughput_scenario, intervention_strategy, mast_height in [
        # ('baseline', 'baseline', 'minimal'),
        # ('0-unplanned', 'baseline', 'minimal'),
        # ('1-new-cities', 'baseline', 'minimal'),
        # ('2-expansion', 'baseline', 'minimal'),

        ('baseline', 'baseline', 'macrocell-700-3500', 30),
        # ('0-unplanned', 'baseline', 'macrocell-700-3500'),
        # ('1-new-cities', 'baseline', 'macrocell-700-3500'),
        # ('2-expansion', 'baseline', 'macrocell-700-3500'),

        # ('baseline', 'baseline', 'sectorisation'),
        # ('0-unplanned', 'baseline', 'sectorisation'),
        # ('1-new-cities', 'baseline', 'sectorisation'),
        # ('2-expansion', 'baseline', 'sectorisation'),

        # ('baseline', 'baseline', 'macro-densification', 30),
        # ('0-unplanned', 'baseline', 'macro-densification'),
        # ('1-new-cities', 'baseline', 'macro-densification'),
        # ('2-expansion', 'baseline', 'macro-densification'),

        # ('baseline', 'baseline', 'small-cell'),
        # ('0-unplanned', 'baseline', 'small-cell'),
        # ('1-new-cities', 'baseline', 'small-cell'),
        # ('2-expansion', 'baseline', 'small-cell'),

        # ('baseline', 'baseline', 'small-cell-and-spectrum'),
        # ('0-unplanned', 'baseline', 'small-cell-and-spectrum'),
        # ('1-new-cities', 'baseline', 'small-cell-and-spectrum'),
        # ('2-expansion', 'baseline', 'small-cell-and-spectrum'),
    ]:
    print("Running:", pop_scenario, throughput_scenario, \
        intervention_strategy)

    #copy initial system list using '[:]'
    assets = initial_system[:]
    for year in TIMESTEPS:
        print("-", year)

        # Update population from scenario values
        for pcd_sector in postcode_sectors:
            try:
                pcd_sector_id = pcd_sector["id"]
                pcd_sector["population"] = \
                    population_by_scenario_year_pcd\
                    [pop_scenario][year][pcd_sector_id]
                pcd_sector["user_throughput"] = \
                    user_throughput_by_scenario_year \
                        [throughput_scenario][year]
            except:
                 pass

        # Decide on new interventions
        budget = ANNUAL_BUDGET
        service_obligation_capacity = SERVICE_OBLIGATION_CAPACITY
        traffic = PERCENTAGE_OF_TRAFFIC_IN_BUSY_HOUR
        market_share = MARKET_SHARE

        # simulate first
        if year == BASE_YEAR:
            system = NetworkManager(
                lads, postcode_sectors, assets,
                capacity_lookup_table, clutter_lookup,
                service_obligation_capacity, traffic,
                market_share, mast_height
                )

        # decide
        interventions_built, budget = decide_interventions(
            intervention_strategy, budget, service_obligation_capacity,
            system, year, traffic, market_share, mast_height
            )
        print('interventions built {}'.format(len(interventions_built)))
        # accumulate decisions
        assets += interventions_built

        # simulate with decisions
        system = NetworkManager(
            lads, postcode_sectors, assets,
            capacity_lookup_table, clutter_lookup,
            service_obligation_capacity, traffic,
            market_share, mast_height
            )

        cost_by_lad = defaultdict(int)
        cost_by_pcd = defaultdict(int)
        for item in interventions_built:
            cost_by_lad[item['lad']] += item['cost']
            cost_by_pcd[item['pcd_sector']] += item['cost']

        write_decisions(interventions_built, year, pop_scenario,
                        throughput_scenario, intervention_strategy)
        write_spend(interventions_built, year, pop_scenario, throughput_scenario,
                    intervention_strategy)
        write_lad_results(system, year, pop_scenario, throughput_scenario,
                          intervention_strategy, cost_by_lad)
        write_pcd_results(system, year, pop_scenario, throughput_scenario,
                          intervention_strategy, cost_by_pcd)

    system = None
