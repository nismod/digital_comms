from digital_comms.fixed_network import model, interventions
import fiona
from operator import attrgetter
import os
import configparser
import csv
import pprint

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# SETUP FILE LOCATIONS 
#####################################

#DEMOGRAPHICS_INPUT_FIXED = os.path.join(BASE_PATH, 'raw', 'demographic_scenario_data')
RESULTS_OUTPUT_FIXED = os.path.join(BASE_PATH, '..', 'results')

#####################################
# SETUP MODEL PARAMETERS
#####################################

BASE_YEAR = 2016
END_YEAR = 2030
TIMESTEP_INCREMENT = 1
TIMESTEPS = range(BASE_YEAR, END_YEAR + 1, TIMESTEP_INCREMENT)

MARKET_SHARE = 0.3

# Annual capital budget constraint for the whole industry, GBP * market share
# ANNUAL_BUDGET = (2 * 10 ** 9) * MARKET_SHARE
ANNUAL_BUDGET = 1000000

# Target threshold for universal mobile service, in Mbps/user
SERVICE_OBLIGATION_CAPACITY = 10

#####################################
# READ SHAPES
#####################################

def read_shapefile(file):
    with fiona.open(file, 'r') as source:
        return [f['properties'] for f in source]

def read_assets():
    assets = {}
    assets['premises'] = read_shapefile(os.path.join('data', 'processed', 'assets_layer5_premises.shp'))
    assets['distributions'] = read_shapefile(os.path.join('data', 'processed', 'assets_layer4_distributions.shp'))
    assets['cabinets'] = read_shapefile(os.path.join('data', 'processed', 'assets_layer3_cabinets.shp'))
    assets['exchanges'] = read_shapefile(os.path.join('data', 'processed', 'assets_layer2_exchanges.shp'))

    return assets
    
def read_links():
    links = []
    links.extend(read_shapefile(os.path.join('data', 'processed', 'links_layer5_premises.shp')))
    links.extend(read_shapefile(os.path.join('data', 'processed', 'links_layer4_distributions.shp')))
    links.extend(read_shapefile(os.path.join('data', 'processed', 'links_layer3_cabinets.shp')))

    return links

def read_parameters():
    return {
        'costs_links_fiber_meter': 5,
        'costs_links_copper_meter': 3,
        'costs_assets_exchange_fttp': 50000,
        'costs_assets_exchange_gfast': 40000,
        'costs_assets_exchange_fttc': 30000,
        'costs_assets_exchange_adsl': 20000,
        'costs_assets_cabinet_fttp_32_ports': 10,
        'costs_assets_cabinet_gfast': 4000,
        'costs_assets_cabinet_fttc': 3000,
        'costs_assets_cabinet_adsl': 2000,
        'costs_assets_distribution_fttp_32_ports': 10,
        'costs_assets_distribution_gfast_4_ports': 1500,
        'costs_assets_distribution_fttc': 300,
        'costs_assets_distribution_adsl': 200,
        'costs_assets_premise_fttp_modem': 20,
        'costs_assets_premise_fttp_optical_network_terminator': 10,
        'costs_assets_premise_gfast_modem': 20,
        'costs_assets_premise_fttc_modem': 15,
        'costs_assets_premise_adsl_modem': 10,
        'benefits_assets_premise_fttp': 50,
        'benefits_assets_premise_gfast': 40,
        'benefits_assets_premise_fttc': 30,
        'benefits_assets_premise_adsl': 20,
    }

def _get_suffix(intervention_strategy):
    suffix = '{}_strategy'.format(
        intervention_strategy)
    # for length, use 'base' for baseline scenarios
    suffix = suffix.replace('baseline', 'base')
    return suffix

def write_decisions(decisions, year, intervention_strategy):
    suffix = _get_suffix(intervention_strategy)
    decisions_filename = os.path.join(RESULTS_OUTPUT_FIXED,  'decisions_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        decisions_file = open(decisions_filename, 'w', newline='')
        decisions_writer = csv.writer(decisions_file)
        decisions_writer.writerow(
            ('asset_id', 'year', 'strategy', 'cost'))
    else:
        decisions_file = open(decisions_filename, 'a', newline='')
        decisions_writer = csv.writer(decisions_file) 

    # output and report results for this timestep
    for intervention in decisions:
        # Output decisions
        asset_id = intervention[0]
        strategy = intervention[1]
        cost = intervention[2]
        year = year

        decisions_writer.writerow(
            (asset_id, year, strategy, cost))

    decisions_file.close()


def write_technologies(ict_manager, year, intervention_strategy):
    suffix = _get_suffix(intervention_strategy)
    technologies_filename = os.path.join(RESULTS_OUTPUT_FIXED,  'technologies_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        technologies_file = open(technologies_filename, 'w', newline='')
        technologies_writer = csv.writer(technologies_file)
        technologies_writer.writerow(
            ('year','strategy','lad_id','fttp','gfast','fttc','adsl'))
    else:
        technologies_file = open(technologies_filename, 'a', newline='')
        technologies_writer = csv.writer(technologies_file) 
    
    my_data = ict_manager.coverage()

    # output and report results for this timestep
    for lad in my_data.items():
        # Output decisions
        lad_id = lad[0],
        fttp = lad[1]['percentage_of_premises_with_fttp']
        gfast = lad[1]['percentage_of_premises_with_gfast']
        fttc = lad[1]['percentage_of_premises_with_fttc']
        adsl = lad[1]['percentage_of_premises_with_adsl']

        technologies_writer.writerow(
            (year, intervention_strategy, lad_id, fttp, gfast, fttc, adsl))

    technologies_file.close()

def write_lad_results(ict_manager, year, intervention_strategy):
    suffix = _get_suffix(intervention_strategy)
    lad_results_filename = os.path.join(RESULTS_OUTPUT_FIXED,  'lad_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        lad_results_file = open(lad_results_filename, 'w', newline='')
        lad_results_writer = csv.writer(lad_results_file)
        lad_results_writer.writerow(
            ('year','strategy','lad_id','mean_capacity'))
    else:
        lad_results_file = open(lad_results_filename, 'a', newline='')
        lad_results_writer = csv.writer(lad_results_file) 
    
    my_data = ict_manager.capacity()

    # output and report results for this timestep
    for lad in my_data.items():
        # Output decisions
        lad_id = lad[0],
        mean_capacity = lad[1]['average_capacity']

        lad_results_writer.writerow(
            (year, intervention_strategy, lad_id, mean_capacity))

    lad_results_file.close()

if __name__ == "__main__": # allow the module to be executed directly 

    for intervention_strategy in [
            ('rollout_fttp_per_distribution'),
            ('rollout_fttp_per_cabinet'),
        ]:

        print("Running:", intervention_strategy)

        assets = read_assets()
        links = read_links()
        parameters = read_parameters()

        for year in TIMESTEPS:
            print("-", year)

            budget = ANNUAL_BUDGET
            service_obligation_capacity = SERVICE_OBLIGATION_CAPACITY

            # Simulate first
            if year == BASE_YEAR:
                system = model.ICTManager(assets, links, parameters)

            # Decide interventions
            intervention_decisions, budget, spend = interventions.decide_interventions(intervention_strategy, budget, service_obligation_capacity, system, year)

            # Upgrade
            system.upgrade(intervention_decisions)

            write_decisions(intervention_decisions, year, intervention_strategy)

            write_technologies(system, year, intervention_strategy)

            write_lad_results(system, year, intervention_strategy)

