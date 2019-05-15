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
SHAPES_INPUT_PATH = os.path.join(BASE_PATH, 'raw', 'd_shapes')
SYSTEM_OUTPUT_PATH = os.path.join(BASE_PATH, '..','results')

BASE_YEAR = 2016
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
    "small_cell_and_spectrum",
    "sectorisation",
    "neutral_hosting",
    "deregulation",
    "cloud_ran",
]

MARKET_SHARE = 0.25
ANNUAL_BUDGET = (2 * 10 ** 9) * MARKET_SHARE
SERVICE_OBLIGATION_CAPACITY = 2
PERCENTAGE_OF_TRAFFIC_IN_BUSY_HOUR = 0.15
NETWORKS_TO_INCLUDE = ('A',)

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
        lads.append({
            "id": lad['properties']['name'],
            "name": lad['properties']['desc'],
        })

postcode_sectors = []
PCD_SECTOR_FILENAME = os.path.join(
    SYSTEM_INPUT_PATH, 'initial_system', 'pcd_sectors.csv'
    )

with open(PCD_SECTOR_FILENAME, 'r') as pcd_sector_file:
   reader = csv.reader(pcd_sector_file)
   next(reader)
   for lad_id, pcd_sector, _, area in reader:
       postcode_sectors.append({
           "id": pcd_sector.replace(" ", ""),
           "lad_id": lad_id,
           "area": float(area)
       })

################################################################
# LOAD SCENARIO DATA
# - population by scenario: year, pcd_sector, population
# - user throughput demand by scenario: year, demand per capita (GB/month?)
################################################################
print('Loading scenario data')

scenario_files = {
    scenario: os.path.join(
        SYSTEM_INPUT_PATH, 'scenario_data',
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
        if "static2017" in THROUGHPUT_SCENARIOS:
            user_throughput_by_scenario_year["baseline"][year] = float(base)

################################################################
# LOAD INITIAL SYSTEM ASSETS/SITES
################################################################
print('Loading initial system')

SYSTEM_FILENAME = os.path.join(
    SYSTEM_INPUT_PATH, 'initial_system', 'initial_system_with_4G.csv'
    )

initial_system = []
pcd_sector_ids = {pcd_sector["id"]: True for pcd_sector in postcode_sectors}
with open(SYSTEM_FILENAME, 'r') as system_file:
    reader = csv.reader(system_file)
    next(reader)
    for pcd_sector, site_ngr, build_date, site_type, tech, \
        freq, bandwidth, network in reader:
        if pcd_sector in pcd_sector_ids and network in NETWORKS_TO_INCLUDE:
            initial_system.append({
                'pcd_sector': pcd_sector,
                'site_ngr': site_ngr,
                'type': site_type,
                'build_date': int(build_date),
                'technology': tech,
                'frequency': freq,
                'bandwidth': bandwidth,
            })

################################################################
# IMPORT LOOKUP TABLES
# - mobile capacity, by environment, frequency, bandwidth and site density
# - clutter environment geotype, by population density
################################################################
print('Loading lookup tables')

CAPACITY_LOOKUP_FILENAME = os.path.join(
    SYSTEM_INPUT_PATH, 'lookup_tables', 'lookup_table_long.csv'
    )

capacity_lookup_table = {}

with open(CAPACITY_LOOKUP_FILENAME, 'r') as capacity_lookup_file:
    reader = csv.DictReader(capacity_lookup_file)
    for row in reader:
        environment = row["type"]
        frequency = row["frequency"].replace(' MHz', '')
        bandwidth = row["bandwidth"].replace(' ', '')
        density = float(row["site_density"])
        capacity = float(row["capacity"])

        if (environment, frequency, bandwidth) not in capacity_lookup_table:
            capacity_lookup_table[(environment, frequency, bandwidth)] = []

        capacity_lookup_table[(
            environment, frequency, bandwidth)].append((density, capacity))

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

def write_lad_results(ict_manager, year, pop_scenario, throughput_scenario,
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
            'capacity', 'capacity_deficit', 'population', 'pop_density')
            )
    else:
        metrics_file = open(metrics_filename, 'a', newline='')
        metrics_writer = csv.writer(metrics_file)

    for lad in ict_manager.lads.values():
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
            capacity_deficit, pop, pop_d)
            )

    metrics_file.close()

def write_pcd_results(ict_manager, year, pop_scenario, throughput_scenario,
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
            'capacity_deficit', 'population', 'pop_density'))
    else:
        metrics_file = open(metrics_filename, 'a', newline='')
        metrics_writer = csv.writer(metrics_file)

    for pcd in ict_manager.postcode_sectors.values():
        demand = pcd.demand
        capacity = pcd.capacity
        capacity_deficit = capacity - demand
        pop = pcd.population
        pop_d = pcd.population_density
        cost = cost_by_pcd[pcd.id]

        metrics_writer.writerow(
            (year, pcd.id, cost, demand, capacity,
            capacity_deficit, pop, pop_d)
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
            (year, pcd_sector, site_ngr, build_date,
            intervention_type, technology, frequency, bandwidth)
            )

    decisions_file.close()

def write_spend(spend, year, pop_scenario,
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

    for pcd_sector, lad, item, cost in spend:
        spend_writer.writerow(
            (year, pcd_sector, lad, item, cost))

    spend_file.close()

def _get_suffix(pop_scenario, throughput_scenario,
    intervention_strategy):

    suffix = 'pop_{}_throughput_{}_strategy_{}'.format(
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

for pop_scenario, throughput_scenario, intervention_strategy in [
        ('low', 'low', 'minimal'),
        ('baseline', 'baseline', 'minimal'),
        ('high', 'high', 'minimal'),

        ('low', 'low', 'macrocell'),
        ('baseline', 'baseline', 'macrocell'),
        ('high', 'high', 'macrocell'),

        ('low', 'low', 'macrocell_700'),
        ('baseline', 'baseline', 'macrocell_700'),
        ('high', 'high', 'macrocell_700'),

        ('low', 'low', 'sectorisation'),
        ('baseline', 'baseline', 'sectorisation'),
        ('high', 'high', 'sectorisation'),

        ('low', 'low', 'macro_densification'),
        ('baseline', 'baseline', 'macro_densification'),
        ('high', 'high', 'macro_densification'),

        ('low', 'low', 'deregulation'),
        ('baseline', 'baseline', 'deregulation'),
        ('high', 'high', 'deregulation'),

        ('low', 'low', 'cloud_ran'),
        ('baseline', 'baseline', 'cloud_ran'),
        ('high', 'high', 'cloud_ran'),

        ('low', 'low', 'small_cell'),
        ('baseline', 'baseline', 'small_cell'),
        ('high', 'high', 'small_cell'),

        ('low', 'low', 'small_cell_and_spectrum'),
        ('baseline', 'baseline', 'small_cell_and_spectrum'),
        ('high', 'high', 'small_cell_and_spectrum'),

    ]:
    print("Running:", pop_scenario, throughput_scenario, \
        intervention_strategy)

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
                market_share
                )

        # decide
        interventions_built, budget, spend = decide_interventions(
            intervention_strategy, budget, service_obligation_capacity,
            system, year, traffic, market_share
            )
        # accumulate decisions
        assets += interventions_built

        # simulate with decisions
        system = NetworkManager(
            lads, postcode_sectors, assets,
            capacity_lookup_table, clutter_lookup,
            service_obligation_capacity, traffic,
            market_share
            )

        cost_by_lad = defaultdict(int)
        cost_by_pcd = defaultdict(int)
        for pcd, lad, item, cost in spend:
            cost_by_lad[lad] += cost
            cost_by_pcd[pcd] += cost

        write_decisions(interventions_built, year, pop_scenario,
                        throughput_scenario, intervention_strategy)
        write_spend(spend, year, pop_scenario, throughput_scenario,
                    intervention_strategy)
        write_lad_results(system, year, pop_scenario, throughput_scenario,
                          intervention_strategy, cost_by_lad)
        write_pcd_results(system, year, pop_scenario, throughput_scenario,
                          intervention_strategy, cost_by_pcd)
