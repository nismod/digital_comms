import fiona
from operator import attrgetter
import os
import configparser
import csv
import yaml
import glob 

from digital_comms.fixed_network.model import ICTManager
from digital_comms.fixed_network.interventions import decide_interventions
from digital_comms.fixed_network.adoption import update_adoption_desirability

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# SETUP FILE LOCATIONS 
#####################################

YAML_DIRECTORY = os.path.join(BASE_PATH, '..', '..','config')
SCENARIO_DATA = os.path.join(BASE_PATH,'..', 'scenarios')
DATA_PROCESSED_INPUTS = os.path.join(BASE_PATH, 'processed')
RESULTS_DIRECTORY = os.path.join(BASE_PATH, '..', '..','results')

#####################################
# SETUP MODEL PARAMETERS
#####################################

BASE_YEAR = 2019
END_YEAR = 2021
TIMESTEP_INCREMENT = 1
TIMESTEPS = range(BASE_YEAR, END_YEAR + 1, TIMESTEP_INCREMENT)

ADOPTION_SCENARIOS = [
    #"high",
    "baseline",
    #"low",
]

INTERVENTION_STRATEGIES = [
    "fttp",
    #"fttdp",
]

#load in digital_comms sector model .yml data from digital_comms/config/sector_models
path = os.path.join(YAML_DIRECTORY, 'sector_models', 'digital_comms.yml')
with open(path, 'r') as ymlfile:
    for data in yaml.load_all(ymlfile):
        parameters = data['parameters']
        for param in parameters:
            if param['name'] == 'annual_budget':
                ANNUAL_BUDGET = param['default_value'] 
                print("annual_budget is {}".format(ANNUAL_BUDGET))
            if param['name'] == 'telco_match_funding':
                TELCO_MATCH_FUNDING = param['default_value'] 
                print("telco match funding is {}".format(TELCO_MATCH_FUNDING))
            if param['name'] == 'subsidy':
                SUBSIDY = param['default_value'] 
                print("government subsidy is {}".format(SUBSIDY))
            if param['name'] == 'service_obligation_capacity':
                SERVICE_OBLIGATION_CAPACITY = param['default_value'] 
                print("USO is {}".format(SERVICE_OBLIGATION_CAPACITY))

strategies = []

#load in each model run yaml from digital_comms/config/sos_model_runs
pathlist = glob.iglob(os.path.join(YAML_DIRECTORY, 'sos_model_runs') + '/*.yml', recursive=True)
for path in pathlist:
    with open(path, 'r') as ymlfile:
        for data in yaml.load_all(ymlfile):
            narratives = data['narratives']
            strategies.append(narratives['technology_strategy'][0])
        
            # if narrative['technology_strategy'] == 'technology_strategy':
            #     ANNUAL_BUDGET = param['default_value'] 
            #     print("annual_budget is {}".format(ANNUAL_BUDGET))
            # if param['name'] == 'telco_match_funding':
            #     TELCO_MATCH_FUNDING = param['default_value'] 
            #     print("telco match funding is {}".format(TELCO_MATCH_FUNDING))
            # if param['name'] == 'subsidy':
            #     SUBSIDY = param['default_value'] 
            #     print("government subsidy is {}".format(SUBSIDY))
            # if param['name'] == 'service_obligation_capacity':
            #     SERVICE_OBLIGATION_CAPACITY = param['default_value'] 
            #     print("USO is {}".format(SERVICE_OBLIGATION_CAPACITY))

# Annual capital budget constraint for the whole industry, GBP * market share
# ANNUAL_BUDGET = (2 * 10 ** 9) * MARKET_SHARE
# ANNUAL_BUDGET = 100000000000
# TELCO_MATCH_FUNDING = 100000000
# SUBSIDY = 100000000
# SERVICE_OBLIGATION_CAPACITY = 10

# Target threshold for universal mobile service, in Mbps/user
# SERVICE_OBLIGATION_CAPACITY = 10

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
print('Loading scenario data')

adoption_data = {}

for adoption_scenario in ADOPTION_SCENARIOS:
    adoption_data[adoption_scenario] = {}
    for intervention_strategy in INTERVENTION_STRATEGIES: 
        adoption_data[adoption_scenario][intervention_strategy] = {}
        #path = os.path.join(SCENARIO_DATA, '{}_{}_adoption.csv'.format(intervention_strategy, adoption_scenario))
        path = os.path.join(SCENARIO_DATA, 'fttp_baseline_adoption_test.csv'.format(intervention_strategy, adoption_scenario))
        with open(path, 'r') as scenario_file:
            scenario_reader = csv.reader(scenario_file)
            next(scenario_reader, None)
            # Put the values in the dict
            for year, region, interval, value in scenario_reader:
                year = int(year)
                if year in TIMESTEPS:
                    adoption_data[adoption_scenario][intervention_strategy][year] = float(value)

################################################################
# WRITE RESULTS DATA
################################################################

def write_decisions(decisions, year, intervention_strategy):
    suffix = _get_suffix(intervention_strategy)
    decisions_filename = os.path.join(RESULTS_DIRECTORY,  'decisions_{}.csv'.format(suffix))

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

################################################################
# WRITE RESULTS DATA
################################################################

if __name__ == "__main__": # allow the module to be executed directly 

    for adoption_scenario, intervention_strategy, policy in [
            #('low','fttdp'), 
            #('baseline','fttdp'), 
            #('high','fttdp'),
        
            #('low','fttp'), 
            ('baseline','fttp', '_rollout_per_distribution'), 
            #('high','fttp')
        ]:

        print("Running:", adoption_scenario, intervention_strategy, policy)

        assets = read_assets()
        links = read_links()
        parameters = read_parameters()

        policy = intervention_strategy + policy

        for year in TIMESTEPS:
            print("-", year)

            budget = ANNUAL_BUDGET

            # Simulate first year
            if year == BASE_YEAR:
                system = ICTManager(assets, links, parameters)

            #get the adoption rate for each time period (by scenario and technology)
            annual_adoption_rate = adoption_data[adoption_scenario][intervention_strategy][year]
            print("Annual scenario adoption rate is {}".format(annual_adoption_rate))

            #get adoption desirability from previous timestep
            adoption_desirability = [premise for premise in system._premises if premise.adoption_desirability is True]
            total_premises = [premise for premise in system._premises]

            #get adoption desirability percentage increase for this timestep
            adoption_desirability_percentage = (len(adoption_desirability) / len(total_premises) * 100)
            percentage_annual_increase = annual_adoption_rate - adoption_desirability_percentage
            percentage_annual_increase = round(float(percentage_annual_increase), 1)

            #update the number of premises wanting to adopt (adoption_desirability)
            system.update_adoption_desirability = update_adoption_desirability(system, percentage_annual_increase)
            premises_adoption_desirability_ids = system.update_adoption_desirability

            #get total adoption desirability for this time step (has to be done after system.update_adoption_desirability)
            adoption_desirability_now = [premise for premise in system._premises if premise.adoption_desirability is True]
            total_adoption_desirability_percentage = (len(adoption_desirability_now) / len(total_premises) * 100)
            print("Annual adoption desirability rate is {}%".format(round(total_adoption_desirability_percentage, 2)))

            #calculate the maximum adoption level based on the scenario, to make sure the model doesn't overestimate
            MAXIMUM_ADOPTION = len(premises_adoption_desirability_ids) + sum(getattr(premise, intervention_strategy) for premise in system._premises)
            print("Maximum annual adoption rate is {}%".format(round(total_adoption_desirability_percentage, 2)))

            #actually decide which interventions to build
            interventions, budget, spend, match_funding_spend, subsidised_spend = decide_interventions(
                policy, budget, SERVICE_OBLIGATION_CAPACITY,  
                system, year, MAXIMUM_ADOPTION, TELCO_MATCH_FUNDING, SUBSIDY)

            #give the interventions to the system model
            system.upgrade(interventions)
            
            #write out the decisions
            write_decisions(interventions, year, intervention_strategy)

            #write_spend(intervention_strategy, interventions, spend, year)

            #write_pcd_results(system, year, pop_scenario, throughput_scenario,intervention_strategy, cost_by_pcd)


