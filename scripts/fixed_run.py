from digital_comms.fixed_network import model, interventions
import fiona
from operator import attrgetter
import os
import configparser
import csv

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
ANNUAL_BUDGET = 100000

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
                #system.coverage()

            # Decide interventions
            intervention_decisions, budget, spend = interventions.decide_interventions(intervention_strategy, budget, service_obligation_capacity, system, year)

            #print(intervention_decisions[0])

            # Upgrade
            system.upgrade(intervention_decisions)

            write_decisions(intervention_decisions, year, intervention_strategy)

            #write_spend(intervention_strategy, interventions, spend, year)

            #write_pcd_results(system, year, pop_scenario, throughput_scenario,intervention_strategy, cost_by_pcd)


    # print('Initialise model')
    # my_fixed_model = model.ICTManager(assets, links, parameters)

    # print('--Statistics--')
    # print('<assets>')
    # print('Number of premises: ' + str(my_fixed_model.number_of_assets['premises']))
    # print('Number of distributions: ' + str(my_fixed_model.number_of_assets['distributions']))
    # print('Number of cabinets: ' + str(my_fixed_model.number_of_assets['cabinets']))
    # print('Number of exchanges: ' + str(my_fixed_model.number_of_assets['exchanges']))

    # print('<links>')
    # print('Number of premises links: ' + str(my_fixed_model.number_of_links['premises']))
    # print('Number of distributions links: ' + str(my_fixed_model.number_of_links['distributions']))
    # print('Number of cabinets links: ' + str(my_fixed_model.number_of_links['cabinets']))
    # print('Number of exchanges links: ' + str(my_fixed_model.number_of_links['exchanges']))

    # print('--Analysis example--')
    # print('<costs>')
    # max_exchange_rollout_costs_fttp = max(my_fixed_model.assets['exchanges'], key=lambda x:x.rollout_costs['fttp'])

    # max_exchange_rollout_costs_fttp = max(my_fixed_model.assets['exchanges'], key=lambda x:x.rollout_costs['fttp'])

    # print('Most expensive exchange for FTTP rollout: ' + max_exchange_rollout_costs_fttp.id)
    # max_cabinet_rollout_costs_fttp = max(my_fixed_model.assets['cabinets'], key=lambda x:x.rollout_costs['fttp'])
    # print('Most expensive cabinet for FTTP rollout: ' + max_cabinet_rollout_costs_fttp.id)
    # max_distribution_rollout_costs_fttp = max(my_fixed_model.assets['distributions'], key=lambda x:x.rollout_costs['fttp'])
    # print('Most expensive distribution for FTTP rollout: ' + max_distribution_rollout_costs_fttp.id)
    # max_premise_rollout_costs_fttp = max(my_fixed_model.assets['premises'], key=lambda x:x.rollout_costs['fttp'])
    # print('Most expensive premise for FTTP rollout: ' + max_premise_rollout_costs_fttp.id)

    # print('<benefits>')
    # max_exchange_rollout_benefits_fttp = max(my_fixed_model.assets['exchanges'], key=lambda x:x.rollout_benefits['fttp'])
    # print('Most benefitial exchange for FTTP rollout: ' + max_exchange_rollout_benefits_fttp.id)
    # max_cabinet_rollout_benefits_fttp = max(my_fixed_model.assets['cabinets'], key=lambda x:x.rollout_benefits['fttp'])
    # print('Most benefitial cabinet for FTTP rollout: ' + max_cabinet_rollout_benefits_fttp.id)
    # max_distribution_rollout_benefits_fttp = max(my_fixed_model.assets['distributions'], key=lambda x:x.rollout_benefits['fttp'])
    # print('Most benefitial distribution for FTTP rollout: ' + max_distribution_rollout_benefits_fttp.id)
    # max_premise_rollout_benefits_fttp = max(my_fixed_model.assets['premises'], key=lambda x:x.rollout_benefits['fttp'])
    # print('Most benefitial premise for FTTP rollout: ' + max_premise_rollout_benefits_fttp.id)

    # print('<benefit-costs-ratio>')
    # max_exchange_rollout_bcr_fttp = max(my_fixed_model.assets['exchanges'], key=lambda x:x.rollout_bcr['fttp'])
    # print('Best benefit-costs-ratio exchange for FTTP rollout: ' + max_exchange_rollout_bcr_fttp.id)
    # max_cabinet_rollout_bcr_fttp = max(my_fixed_model.assets['cabinets'], key=lambda x:x.rollout_bcr['fttp'])
    # print('Best benefit-costs-ratio cabinet for FTTP rollout: ' + max_cabinet_rollout_bcr_fttp.id)
    # max_distribution_rollout_bcr_fttp = max(my_fixed_model.assets['distributions'], key=lambda x:x.rollout_bcr['fttp'])
    # print('Best benefit-costs-ratio distribution for FTTP rollout: ' + max_distribution_rollout_bcr_fttp.id)
    # max_premise_rollout_bcr_fttp = max(my_fixed_model.assets['premises'], key=lambda x:x.rollout_bcr['fttp'])
    # print('Best benefit-costs-ratio premise for FTTP rollout: ' + max_premise_rollout_bcr_fttp.id)






























