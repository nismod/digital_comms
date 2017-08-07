"""Model runner to use in place of smif for standalone modelruns
- run over multiple years
- make rule-based intervention decisions at each timestep
"""
# pylint: disable=C0103
import configparser
import csv
import itertools
import os
import pprint

from digital_comms.ccam import ICTManager
from digital_comms.interventions import decide_interventions

################################################################
# SETUP MODEL RUN CONFIGURATION
# - timesteps, scenarios, strategies
# - data files base path
################################################################

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

BASE_YEAR = 2017
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
    "small_cell",
]

# Annual capital budget constraint, GBP
ANNUAL_BUDGET = 2 * 10^9

# Target threshold for universal mobile service, in Mbps/km^2
SERVICE_OBLIGATION_CAPACITY = 0.2

################################################################
# LOAD REGIONS
# - LADs
# - Postcode Sectors
################################################################
print('Loading regions')

# lads = [
# 	{
# 		"id": 1,
# 		"name": "Cambridge"
# 	},
# ]
lads = []
LAD_FILENAME = os.path.join(BASE_PATH, 'initial_system', 'lads.csv')

with open(LAD_FILENAME, 'r') as lad_file:
    reader = csv.reader(lad_file)
    next(reader)  # skip header
    for lad_id, name in reader:
        lads.append({
            "id": lad_id,
            "name": name
        })

# Read in postcode sectors (without population)
# pcd_sectors = [
# 	{
# 		"id": "CB1G",
# 		"lad_id": 1,
# 		"population": 50000,  # to be loaded from scenario data
# 		"area": 2,
# 	},
# ]
pcd_sectors = []
PCD_SECTOR_FILENAME = os.path.join(BASE_PATH, 'initial_system', 'pcd_sectors.csv')
with open(PCD_SECTOR_FILENAME, 'r') as pcd_sector_file:
    reader = csv.reader(pcd_sector_file)
    next(reader)  # skip header
    for lad_id, pcd_sector, _, area in reader:
        pcd_sectors.append({
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
    scenario: os.path.join(BASE_PATH, 'scenario_data', 'population_{}_pcd.csv'.format(scenario))
    for scenario in POPULATION_SCENARIOS
}
population_by_scenario_year_pcd = {
    scenario: {
        year: {} for year in TIMESTEPS
    }
    for scenario in POPULATION_SCENARIOS
}

for scenario, filename in scenario_files.items():
    # Open file
    with open(filename, 'r') as scenario_file:
        scenario_reader = csv.reader(scenario_file)

        # Put the values in the population dict
        for year, pcd_sector, population in scenario_reader:
            year = int(year)
            if year in TIMESTEPS:
                population_by_scenario_year_pcd[scenario][year][pcd_sector] = int(population)

user_throughput_by_scenario_year = {
    scenario: {} for scenario in THROUGHPUT_SCENARIOS
}
THROUGHPUT_FILENAME = os.path.join(BASE_PATH, 'scenario_data', 'data_growth_scenarios.csv')
with open(THROUGHPUT_FILENAME, 'r') as throughput_file:
    reader = csv.reader(throughput_file)
    next(reader)  # skip header
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

# Read in assets (for initial timestep)
# assets = [
# 	{
#       'pcd_sector': 'CB12',
#       'site_ngr': 'EF006234',
#       'build_date': 2015,
#       'technology': 'LTE',
#       'frequency': '800',
#       'bandwidth': '2x10MHz',
# 	}
# ]
SYSTEM_FILENAME = os.path.join(BASE_PATH, 'initial_system', 'initial_system_with_4G.csv')

initial_system = []
pcd_sector_ids = {pcd_sector["id"]: True for pcd_sector in pcd_sectors}
with open(SYSTEM_FILENAME, 'r') as system_file:
    reader = csv.reader(system_file)
    next(reader)  # skip header
    for pcd_sector, site_ngr, build_date, tech, freq, bandwidth in reader:
        # If asset is in a known postcode, go ahead
        if pcd_sector in pcd_sector_ids:
            initial_system.append({
                'pcd_sector': pcd_sector,
                'site_ngr': site_ngr,
                'type': 'macrocell_site',
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

CAPACITY_LOOKUP_FILENAME = os.path.join(BASE_PATH, 'lookup_tables', 'lookup_table_long.csv')

# create empty dictionary for capacity lookup
capacity_lookup_table = {}

with open(CAPACITY_LOOKUP_FILENAME, 'r') as capacity_lookup_file:
    # set DictReader with file name for 4G rollout data
    reader = csv.DictReader(capacity_lookup_file)

        # populate dictionary - this gives a dict for each row, with each heading as a key
    for row in reader:
        environment = row["type"]
        frequency = row["frequency"].replace(' MHz', '')
        bandwidth = row["bandwidth"].replace(' ', '')
        density = float(row["site_density"])
        capacity = float(row["capacity"])

        if (environment, frequency, bandwidth) not in capacity_lookup_table:
            capacity_lookup_table[(environment, frequency, bandwidth)] = []

        capacity_lookup_table[(environment, frequency, bandwidth)].append((density, capacity, ))

    for key, value_list in capacity_lookup_table.items():
        # sort each environment/frequency/bandwith list by site density
        value_list.sort(key=lambda tup: tup[0])


CLUTTER_GEOTYPE_FILENAME = os.path.join(BASE_PATH, 'lookup_tables', 'lookup_table_geotype.csv')

# Create empty list for clutter geotype lookup
clutter_lookup = []

with open(CLUTTER_GEOTYPE_FILENAME, 'r') as clutter_geotype_file:
    # set DictReader with file name for 4G rollout data
    reader = csv.DictReader(clutter_geotype_file)
    for row in reader:
        geotype = row['geotype']
        population_density = float(row['population_density'])
        clutter_lookup.append((population_density, geotype))

    # sort list by population density (first entry in each tuple)
    clutter_lookup.sort(key=lambda tup: tup[0])

def write_results(ict_manager, year, pop_scenario, throughput_scenario, intervention_strategy):
    suffix = 'pop_{}_throughput_{}_strategy_{}'.format(
        pop_scenario, throughput_scenario, intervention_strategy)
    suffix = suffix.replace('baseline', 'base')  # for length, use 'base' for baseline scenarios
    metrics_filename = os.path.join(BASE_PATH, 'outputs', 'metrics_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        metrics_file = open(metrics_filename, 'w')
        metrics_writer = csv.writer(metrics_file)
        metrics_writer.writerow(
            ('year', 'area_id', 'area_name', 'cost', 'coverage', 'demand', 'capacity', 'energy_demand'))
    else:
        metrics_file = open(metrics_filename, 'a')
        metrics_writer = csv.writer(metrics_file)

    # output and report results for this timestep
    results = ict_manager.results()

    for lad in ict_manager.lads.values():
        area_id = lad.id
        area_name = lad.name

        # Output metrics
        # year,area,cost,coverage,demand,capacity,energy_demand
        cost = results["cost"][area_name]
        coverage = results["coverage"][area_name]
        demand = results["demand"][area_name]
        capacity = results["capacity"][area_name]
        energy_demand = results["energy_demand"][area_name]

        metrics_writer.writerow(
            (year, area_id, area_name, cost, coverage, demand, capacity, energy_demand))

    metrics_file.close()

def write_decisions(decisions, year, pop_scenario, throughput_scenario, intervention_strategy):
    suffix = 'pop_{}_throughput_{}_strategy_{}'.format(
        pop_scenario, throughput_scenario, intervention_strategy)
    decisions_filename = os.path.join(BASE_PATH, 'outputs', 'decisions_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        decisions_file = open(decisions_filename, 'w')
        metrics_writer = csv.writer(decisions_file)
        metrics_writer.writerow(
            ('year', 'pcd_sector', 'site_ngr', 'build_date', 'type', 'technology', 'frequency', 'bandwidth',))
    else:
        decisions_file = open(decisions_filename, 'a')
        decisions_writer = csv.writer(decisions_file)

    # output and report results for this timestep
    for intervention in decisions:
        # Output decisions
        pcd_sector = intervention['pcd_sector']
        site_ngr = intervention['site_ngr']
        build_date = intervention['build_date']
        intervention_type = intervention['type']
        technology = intervention['technology']
        frequency = intervention['frequency']
        bandwidth = intervention['bandwidth']

        decisions_writer.writerow(
            (year, pcd_sector, site_ngr, build_date, intervention_type, technology, frequency, bandwidth,))

    decisions_file.close()


################################################################
# START RUNNING MODEL
# - run from BASE_YEAR to END_YEAR in TIMESTEP_INCREMENT steps
# - run over population scenario / demand scenario / intervention strategy combinations
# - output demand, capacity, opex, energy demand, built interventions, build costs per year
################################################################

for pop_scenario, throughput_scenario, intervention_strategy in itertools.product(
        POPULATION_SCENARIOS,
        THROUGHPUT_SCENARIOS,
        INTERVENTION_STRATEGIES):
    print("Running:", pop_scenario, throughput_scenario, intervention_strategy)

    assets = initial_system
    for year in TIMESTEPS:
        print("-", year)

        # Update population from scenario values
        for pcd_sector in pcd_sectors:
            pcd_sector_id = pcd_sector["id"]
            pcd_sector["population"] = population_by_scenario_year_pcd[pop_scenario][year][pcd_sector_id]
            pcd_sector["user_throughput"] = user_throughput_by_scenario_year[throughput_scenario][year]

        # Decommission assets
        asset_lifetime = 10
        decommissioned = [asset for asset in assets if asset["build_date"] <= year - asset_lifetime]
        assets = [asset for asset in assets if asset["build_date"] > year - asset_lifetime]

        # Decide on new interventions
        budget = ANNUAL_BUDGET
        service_obligation_capacity = SERVICE_OBLIGATION_CAPACITY
        timestep_interventions = []
        while True:
            # simulate
            system = ICTManager(lads, pcd_sectors, assets, capacity_lookup_table, clutter_lookup)
            # decide
            interventions_built, budget = decide_interventions(intervention_strategy, budget, service_obligation_capacity, decommissioned, system)

            if not interventions_built:
                # no more decisions (feasible or desirable)
                break
            else:
                # accumulate decisions
                timestep_interventions += interventions_built
                assets += interventions_built

        write_decisions(timestep_interventions, year, pop_scenario, throughput_scenario, intervention_strategy)
        write_results(system, year, pop_scenario, throughput_scenario, intervention_strategy)
