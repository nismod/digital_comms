import configparser
import csv
import glob
import itertools
import logging
import os

import yaml

from digital_comms.fixed_network.model import NetworkManager
from digital_comms.fixed_network.interventions import decide_interventions
from digital_comms.fixed_network.adoption import update_adoption_desirability


def read_csv(file):
    """Read in a .csv file. Convert each line to single dict, and then append to a list.

    Parameters
    ----------
    file : string
        This is a directory string to point to the desired file from the BASE_PATH.

    Returns
    -------
    list_of_dicts
        Returns a list of dicts, with each line [an asset or link] in the .csv forming its own
        dict

    """
    results = []
    with open(file, 'r') as system_file:
        reader = csv.DictReader(system_file)
        for line in reader:
            results.append(dict(line))

    return results


def read_assets():
    """Read in all assets required to run the model:
        - Premises
        - Distribution Points
        - Cabinets
        - Exchanges

    Returns
    -------
    dict
        Returns a dict containing all Premises, Distribution Points, Cabinets and Exchanges.

    """
    assets = {}
    assets['premises'] = read_csv(os.path.join(
        'data', 'processed', 'assets_layer5_premises.csv'))
    assets['distributions'] = read_csv(os.path.join(
        'data', 'processed', 'assets_layer4_distributions.csv'))
    assets['cabinets'] = read_csv(os.path.join(
        'data', 'processed', 'assets_layer3_cabinets.csv'))
    assets['exchanges'] = read_csv(os.path.join(
        'data', 'processed', 'assets_layer2_exchanges.csv'))

    return assets


def read_links():
    """Read in all links required to run the model:
        - Premises to Distribution Point,
        - Distribution Point to Cabinet,
        - Cabinet to Exchange.

    Returns
    -------
    list_of_dicts
        Returns a list_of_dicts containing all links between Premises, Distribution Points,
        Cabinets and Exchanges.

    """
    links = []
    links.extend(read_csv(os.path.join('data', 'processed', 'links_layer5_premises.csv')))
    links.extend(read_csv(os.path.join('data', 'processed', 'links_layer4_distributions.csv')))
    links.extend(read_csv(os.path.join('data', 'processed', 'links_layer3_cabinets.csv')))

    return links


def read_parameters():
    """Reads in all parameters from the 'digital_comms.yml' file.

    Returns
    -------
    dict
        Returns a dict containing all parameters from 'digital_comms.yml'.

    """
    params = {}

    path = os.path.join(YAML_DIRECTORY, 'sector_models', 'digital_comms.yml')
    with open(path, 'r') as ymlfile:
        for data in yaml.load_all(ymlfile):
            parameters = data['parameters']
            for param in parameters:
                if param['name'] == 'costs_assets_exchange_fttp':
                    params['costs_assets_exchange_fttp'] = param['default_value']
                if param['name'] == 'costs_assets_exchange_fttdp':
                    params['costs_assets_exchange_fttdp'] = param['default_value']
                if param['name'] == 'costs_assets_exchange_fttc':
                    params['costs_assets_exchange_fttc'] = param['default_value']
                if param['name'] == 'costs_assets_exchange_adsl':
                    params['costs_assets_exchange_adsl'] = param['default_value']
                if param['name'] == 'costs_assets_upgrade_cabinet_fttp':
                    params['costs_assets_upgrade_cabinet_fttp'] = param['default_value']
                if param['name'] == 'costs_assets_cabinet_fttdp':
                    params['costs_assets_cabinet_fttdp'] = param['default_value']
                if param['name'] == 'costs_assets_cabinet_fttc':
                    params['costs_assets_cabinet_fttc'] = param['default_value']
                if param['name'] == 'costs_assets_cabinet_adsl':
                    params['costs_assets_cabinet_adsl'] = param['default_value']
                if param['name'] == 'costs_assets_premise_fttp_optical_connection_point':
                    params['costs_assets_premise_fttp_optical_connection_point'] = \
                        param['default_value']
                if param['name'] == 'costs_assets_distribution_fttdp_8_ports':
                    params['costs_assets_distribution_fttdp_8_ports'] = param['default_value']
                if param['name'] == 'costs_assets_distribution_fttc':
                    params['costs_assets_distribution_fttc'] = param['default_value']
                if param['name'] == 'costs_assets_distribution_adsl':
                    params['costs_assets_distribution_adsl'] = param['default_value']
                if param['name'] == 'costs_links_fibre_meter':
                    params['costs_links_fibre_meter'] = param['default_value']
                if param['name'] == 'costs_links_copper_meter':
                    params['costs_links_copper_meter'] = param['default_value']
                if param['name'] == 'costs_assets_premise_fttp_modem':
                    params['costs_assets_premise_fttp_modem'] = param['default_value']
                if param['name'] == 'costs_assets_premise_fttp_optical_network_terminator':
                    params['costs_assets_premise_fttp_optical_network_terminator'] = \
                        param['default_value']
                if param['name'] == 'planning_administration_cost':
                    params['planning_administration_cost'] = param['default_value']
                if param['name'] == 'costs_assets_premise_fttdp_modem':
                    params['costs_assets_premise_fttdp_modem'] = param['default_value']
                if param['name'] == 'costs_assets_premise_fttc_modem':
                    params['costs_assets_premise_fttc_modem'] = param['default_value']
                if param['name'] == 'costs_assets_premise_adsl_modem':
                    params['costs_assets_premise_adsl_modem'] = param['default_value']
                # revenue aspects
                if param['name'] == 'months_per_year':
                    params['months_per_year'] = param['default_value']
                if param['name'] == 'payback_period':
                    params['payback_period'] = param['default_value']
                if param['name'] == 'profit_margin':
                    params['profit_margin'] = param['default_value']
    return params

################################################################
# LOAD SCENARIO DATA
################################################################


def load_in_yml_parameters():
    """Load in digital_comms sector model .yml parameter data from
    digital_comms/config/sector_models.

    This relates to ANNUAL_BUDGET, TELCO_MATCH_FUNDING, SUBSIDY and any
    SERVICE_OBLIGATION_CAPACITY

    Returns
    -------
    annual_budget : int
        Returns the annual budget capable of spending.
    telco_match_funding : int
        Returns the annual budget capable of being match funded.
    subsidy : int
        Returns the annual subsidy amount.
    service_obligation_capacity : int
        Returns the annual universal service obligation.

    """
    path = os.path.join(YAML_DIRECTORY, 'sector_models', 'digital_comms.yml')
    with open(path, 'r') as ymlfile:
        for data in yaml.load_all(ymlfile):
            parameters = data['parameters']
            for param in parameters:
                if param['name'] == 'annual_budget':
                    annual_budget = param['default_value']
                    logging.info("annual_budget is {}".format(annual_budget))
                if param['name'] == 'subsidy':
                    subsidy = param['default_value']
                    logging.info("government subsidy is {}".format(subsidy))
                if param['name'] == 'telco_match_funding':
                    telco_match_funding = param['default_value']
                    logging.info("telco match funding is {}".format(telco_match_funding))
                if param['name'] == 'service_obligation_capacity':
                    service_obligation_capacity = param['default_value']
                    logging.info("USO is {}".format(service_obligation_capacity))

    return annual_budget, telco_match_funding, subsidy, service_obligation_capacity

annual_budget, subsidy, telco_match_funding, service_obligation_capacity = load_in_yml_parameters()

def load_in_scenarios_and_strategies():
    """Load in each model run .yaml file from digital_comms/config/sos_model_runs,
    separting out scenarios, technologies and policies.

    Returns
    -------
    scenarios : list
        Returns the scenario names available for testing.
    strategy_technologies : list
        Returns the technologies names available for testing.
    strategy_policies : list
        Returns the policy names available for testing.

    """
    scenarios = []
    strategy_technologies = []
    strategy_policies = []
    pathlist = glob.iglob(os.path.join(
        YAML_DIRECTORY, 'sos_model_runs') + '/*.yml', recursive=True)
    for path in pathlist:
        with open(path, 'r') as ymlfile:
            for data in yaml.load_all(ymlfile):
                narratives = data['narratives']
                technology = narratives['technology_strategy'][0].split('_', 1)[0]
                strategy_technologies.append(technology)
                scenario_data = data['scenarios']
                scenarios.append(scenario_data['adoption'].split('_', 2)[0])
                policy = narratives['technology_strategy'][0].split('_', 1)[1]
                strategy_policies.append(policy)

    scenarios = list(set(scenarios))
    strategy_technologies = list(set(strategy_technologies))
    strategy_policies = list(set(strategy_policies))

    return scenarios, strategy_technologies, strategy_policies


def load_adoption_data(scenarios):
    """Load in adoption forecasts for each scenario.

    Returns
    -------
    adoption_data : dict
        Returns the adoption data.

    """
    adoption_data = {}

    for scenario in scenarios:
        adoption_data[scenario] = {}
        path = os.path.join(SCENARIO_DATA, '{}_adoption.csv'.format(scenario))
        with open(path, 'r') as scenario_file:
            scenario_reader = csv.reader(scenario_file)
            next(scenario_reader, None)
            # Put the values in the dict
            for year, _, _, value in scenario_reader:
                year = int(year)
                if year in TIMESTEPS:
                    adoption_data[scenario][year] = float(value)

    return adoption_data

################################################################
# WRITE RESULTS DATA
################################################################


def write_decisions(decisions, year, technology, policy):
    """Write out the infrastructure decisions made annually for each technology and policy.

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

    decisions_filename = os.path.join(
        RESULTS_DIRECTORY, 'decisions_{}_{}.csv'.format(technology, policy))

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
# RUN MODEL
################################################################


def run():
    """Run model over scenario/strategy combinations
    """

    scenarios, strategy_technologies, policies = load_in_scenarios_and_strategies()

    adoption_data = load_adoption_data(scenarios)

    for scenario, technology, policy in itertools.product(
            scenarios, strategy_technologies, policies):

        logging.info("--")
        logging.info("Running: %s, %s, %s", scenario, technology, policy)
        logging.info("--")

        assets = read_assets()
        links = read_links()
        parameters = read_parameters()

        for year in TIMESTEPS:
            logging.info("-%s", year)

            budget = annual_budget

            # Simulate first year
            if year == BASE_YEAR:
                system = NetworkManager(assets, links, parameters)

            # get the adoption rate for each time period (by scenario and technology)
            annual_adoption_rate = adoption_data[scenario][year]
            logging.info("Annual scenario adoption rate is %s", annual_adoption_rate)

            # get adoption desirability from previous timestep
            adoption_desirability = [
                premise for premise in system._premises if premise.adoption_desirability]
            total_premises = [premise for premise in system._premises]

            # get adoption desirability percentage increase for this timestep
            adoption_desirability_percentage = (
                len(adoption_desirability) / len(total_premises) * 100)
            percentage_annual_increase = annual_adoption_rate - \
                adoption_desirability_percentage
            percentage_annual_increase = round(float(percentage_annual_increase), 1)

            # update the number of premises wanting to adopt (adoption_desirability)
            premises_adoption_desirability_ids = update_adoption_desirability(
                system, percentage_annual_increase)
            system.update_adoption_desirability(premises_adoption_desirability_ids)

            # get total adoption desirability for this time step (has to be done after
            # system.update_adoption_desirability)
            # adoption_desirability_now = [
            #     premise for premise in system._premises if premise.adoption_desirability]
            # total_adoption_desirability_percentage = round(
            #     (len(adoption_desirability_now) / len(total_premises) * 100), 2)
            # logging.info("Annual adoption desirability rate is {}%".format(
            #     round(total_adoption_desirability_percentage, 2)))

            # calculate the maximum adoption level based on the scenario, to make sure the
            # model doesn't overestimate
            adoption_cap = len(premises_adoption_desirability_ids) + \
                sum(getattr(premise, technology) for premise in system._premises)
            #logging.info("Maximum annual adoption rate is {}%".format(
            #   round(total_adoption_desirability_percentage, 2)))

            # actually decide which interventions to build
            built_interventions = decide_interventions(
                system, year, technology, policy, budget, adoption_cap,
                SUBSIDY, TELCO_MATCH_FUNDING, SERVICE_OBLIGATION_CAPACITY)

            # give the interventions to the system model
            system.upgrade(built_interventions)

            # write out the decisions
            write_decisions(built_interventions, year, technology, policy)

            # write_spend(built_interventions, year, technology, policy, spend)

            # write_pcd_results(system, year, pop_scenario, throughput_scenario, technology,
            #                   policy, cost_by_pcd)

            logging.info("--")


if __name__ == "__main__":
    # allow the module to be executed directly
    print("Running fixed broadband runner.py")

    CONFIG = configparser.ConfigParser()
    CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
    BASE_PATH = CONFIG['file_locations']['base_path']

    logging.basicConfig(filename='fixed_runner.py_logged_info', level=logging.INFO)

    #####################################
    # SETUP FILE LOCATIONS
    #####################################

    YAML_DIRECTORY = os.path.join(BASE_PATH, '..', 'config')
    SCENARIO_DATA = os.path.join(BASE_PATH, 'scenarios')
    DATA_PROCESSED_INPUTS = os.path.join(BASE_PATH, 'processed')
    RESULTS_DIRECTORY = os.path.join(BASE_PATH, '..', 'results')

    #####################################
    # SETUP MODEL PARAMETERS
    #####################################

    BASE_YEAR = 2019
    END_YEAR = 2021
    TIMESTEP_INCREMENT = 1
    TIMESTEPS = range(BASE_YEAR, END_YEAR + 1, TIMESTEP_INCREMENT)

    logging.info('--')
    logging.info('Loading scenario data')

    YML_PARAMS = load_in_yml_parameters()
    ANNUAL_BUDGET, TELCO_MATCH_FUNDING, SUBSIDY, SERVICE_OBLIGATION_CAPACITY = YML_PARAMS

    run()
    print("Fixed broadband runner.py is complete")
