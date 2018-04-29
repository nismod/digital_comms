from digital_comms.fixed_model import fixed_model, fixed_interventions
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
        'costs': {
            'links': {
                'fiber': {
                    'meter': 5
                },
                'copper': {
                    'meter': 3
                }
            },
            'assets': {
                'exchange': {
                    'fttp': 50000,
                    'gfast': 40000,
                    'fttc': 30000,
                    'adsl': 20000
                },
                'cabinet': {
                    'fttp':{
                        '32_ports': 10
                    },
                    'gfast': 4000,
                    'fttc': 3000,
                    'adsl': 2000
                },
                'distribution': {
                    'fttp':  {
                        '32_ports': 10
                    },
                    'gfast': {
                        '4_ports': 1500
                    },
                    'fttc': 300,
                    'adsl': 200
                },
                'premise': {
                    'fttp': {
                        'modem': 20,
                        'optical_network_terminator': 10
                    },
                    'gfast': {
                        'modem': 20,
                    },
                    'fttc': {
                        'modem': 15,
                    },
                    'adsl': {
                        'modem': 10
                    }
                }
            }
        },
        'benefits': {
            'assets': {
                'premise': {
                    'fttp': 50,
                    'gfast': 40,
                    'fttc': 30,
                    'adsl': 20
                }
            }
        }
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
            ('year' 'asset_id', 'strategy', 'cost'))
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
            (asset_id, strategy, cost, year))

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
                system = fixed_model.ICTManager(assets, links, parameters)

            # Decide interventions
            interventions, budget, spend = fixed_interventions.decide_interventions(intervention_strategy, budget, service_obligation_capacity, system, year)

            # Upgrade
            system.upgrade(interventions)

            write_decisions(interventions, year, intervention_strategy)

            #write_spend(intervention_strategy, interventions, spend, year)

            #write_pcd_results(system, year, pop_scenario, throughput_scenario,intervention_strategy, cost_by_pcd)

