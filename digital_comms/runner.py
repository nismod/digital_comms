import fiona
from operator import attrgetter
import os
import configparser
import csv

from digital_comms.fixed_network.model import ICTManager
from digital_comms.fixed_network.interventions import decide_interventions
from digital_comms.fixed_network.adoption import update_adoption_desirability

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# SETUP FILE LOCATIONS 
#####################################

#DEMOGRAPHICS_INPUT_FIXED = os.path.join(BASE_PATH, 'raw', 'demographic_scenario_data')
RESULTS_OUTPUT_FIXED = os.path.join(BASE_PATH, '..', 'results')
SCENARIO_DATA = os.path.join(BASE_PATH,'..', 'scenarios')
DATA_PROCESSED_INPUTS = os.path.join(BASE_PATH, 'processed')

#####################################
# SETUP MODEL PARAMETERS
#####################################

BASE_YEAR = 2016
END_YEAR = 2030
TIMESTEP_INCREMENT = 1
TIMESTEPS = range(BASE_YEAR, END_YEAR + 1, TIMESTEP_INCREMENT)

ADOPTION_SCENARIOS = [
    "high",
    "baseline",
    "low",
]

INTERVENTION_STRATEGIES = [
    "fttp",
    "fttdp",
]

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
    assets['premises'] = read_shapefile(os.path.join(DATA_PROCESSED_INPUTS, 'assets_layer5_premises.shp'))
    assets['distributions'] = read_shapefile(os.path.join(DATA_PROCESSED_INPUTS, 'assets_layer4_distributions.shp'))
    assets['cabinets'] = read_shapefile(os.path.join(DATA_PROCESSED_INPUTS, 'assets_layer3_cabinets.shp'))
    assets['exchanges'] = read_shapefile(os.path.join(DATA_PROCESSED_INPUTS, 'assets_layer2_exchanges.shp'))

    return assets
    
def read_links():
    links = []
    links.extend(read_shapefile(os.path.join(DATA_PROCESSED_INPUTS, 'links_layer5_premises.shp')))
    links.extend(read_shapefile(os.path.join(DATA_PROCESSED_INPUTS, 'links_layer4_distributions.shp')))
    links.extend(read_shapefile(os.path.join(DATA_PROCESSED_INPUTS, 'links_layer3_cabinets.shp')))

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
        'costs_assets_upgrade_cabinet_fttp': 2000,
        'costs_assets_upgrade_cabinet_fttdp': 4000,
        'costs_assets_cabinet_fttdp': 4000,
        'costs_assets_cabinet_fttc': 3000,
        'costs_assets_cabinet_adsl': 2000,
        'costs_assets_distribution_fttp_32_ports': 10,
        'costs_assets_distribution_fttdp_8_ports': 1500,
        'costs_assets_distribution_fttc': 300,
        'costs_assets_distribution_adsl': 200,
        'costs_assets_premise_fttp_modem': 20,
        'costs_assets_premise_fttp_optical_network_terminator': 10,
        'costs_assets_premise_fttp_optical_connection_point': 37,
        'costs_assets_premise_fttdp_modem': 20,
        'costs_assets_premise_fttc_modem': 15,
        'costs_assets_premise_adsl_modem': 10,
        'benefits_assets_premise_fttp': 50,
        'benefits_assets_premise_gfast': 40,
        'benefits_assets_premise_fttc': 30,
        'benefits_assets_premise_adsl': 20,
        'planning_administration_cost': 200
    }

def _get_suffix(intervention_strategy):
    suffix = '{}_strategy'.format(
        intervention_strategy)
    # for length, use 'base' for baseline scenarios
    suffix = suffix.replace('baseline', 'base')
    return suffix

################################################################
# LOAD SCENARIO DATA
################################################################
#print('Loading scenario data')


################################################################
# WRITE RESULTS DATA
################################################################

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

    for adoption_scenario, intervention_strategy in [
            ('low','fttdp'), #rollout_fttp_per_distribution
            ('baseline','fttdp'), #rollout_fttp_per_cabinet
            ('high','fttdp'),
        
            ('low','fttp'), #rollout_fttp_per_distribution
            ('baseline','fttp'), #rollout_fttp_per_cabinet
            ('high','fttp')
        ]:

        print("Running:", adoption_scenario, intervention_strategy)

        assets = read_assets()
        links = read_links()
        parameters = read_parameters()

        for year in TIMESTEPS:
            print("-", year)

            budget = ANNUAL_BUDGET

            # Simulate first
            if year == BASE_YEAR:
                system = ICTManager(assets, links, parameters)
                #system.coverage()

            print(adoption_scenario, intervention_strategy)
            print("use dummy adoption rate for now of 10%")
            annual_adoption_rate = 10
            adoption_desirability = [premise for premise in system._premises if premise.adoption_desirability is True]
            total_premises = [premise for premise in system._premises]
            adoption_desirability_percentage = (len(adoption_desirability) / len(total_premises) * 100)
            percentage_annual_increase = annual_adoption_rate - adoption_desirability_percentage
            percentage_annual_increase = round(float(percentage_annual_increase), 1)

            system.update_adoption_desirability = update_adoption_desirability(system, percentage_annual_increase)
            premises_adoption_desirability_ids = system.update_adoption_desirability
            
            MAXIMUM_ADOPTION = len(premises_adoption_desirability_ids) + sum(getattr(premise, intervention_strategy) for premise in system._premises)

            interventions, budget, spend, match_funding_spend, subsidised_spend = decide_interventions(
                STRATEGY, data_handle.get_parameter('annual_budget'), data_handle.get_parameter('service_obligation_capacity'), 
                system, now, MAXIMUM_ADOPTION, data_handle.get_parameter('telco_match_funding'), 
                data_handle.get_parameter('subsidy'))

            system.upgrade(interventions)

            # Decide interventions
            interventions, budget, spend = decide_interventions(intervention_strategy, budget, service_obligation_capacity, system, year)

            #print(intervention_decisions[0])

            # Upgrade
            system.upgrade(intervention_decisions)

            write_decisions(intervention_decisions, year, intervention_strategy)

            #write_spend(intervention_strategy, interventions, spend, year)

            #write_pcd_results(system, year, pop_scenario, throughput_scenario,intervention_strategy, cost_by_pcd)


