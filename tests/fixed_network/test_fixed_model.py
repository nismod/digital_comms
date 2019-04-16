import pytest
import os

from digital_comms.fixed_network.model import NetworkManager
from digital_comms.fixed_network.adoption import update_adoption_desirability
from digital_comms.fixed_network.interventions import decide_interventions


@pytest.fixture
def base_system():

    assets = {
        'distributions':[{
            'id': 'distribution_{EACAM}{795}',
            'lad': 'ABABA',
            'connection': 'cabinet_{EACAM}{P100}',
            'fttp': 0,
            'fttdp': 0,
            'fttc': 5,
            'docsis3': 5,
            'adsl': 20,
            'total_prems': 20,
            'wta': 2.333,
            'wtp': 200,
            'name': 'distribution_{EACAM}{795}',
        }],
        'cabinets':[{
            'id': 'cabinet_{EACAM}{P100}',
            'connection': 'exchange_EACAM',
            'fttp': 0,
            'fttdp': 0,
            'fttc': 1,
            'docsis3': 0,
            'adsl': 1,
            'name': 'cabinet_{EACAM}{P100}',
        }],
        'exchanges':[{
            'id': 'exchange_EACAM',
            'Name': 'Cambridge',
            'pcd': 'CB23ET',
            'Region': 'East',
            'County': 'Cambridgeshire',
            'fttp': 0,
            'fttdp': 0,
            'fttc': 1,
            'docsis3': 0,
            'adsl': 1,
        }]
    }

    links = [
        {
        'origin': 'premises_aggregated',
        'dest': 'distribution_{EACAM}{795}',
        'length': 200,
        'technology': 'copper'
        },
        {
        'origin': 'distribution_{EACAM}{795}',
        'dest': 'cabinet_{EACAM}{P100}',
        'length': 94,
        'technology': 'copper'
        },
        {
        'origin': 'cabinet_{EACAM}{P100}',
        'dest': 'exchange_EACAM',
        'length': 1297,
        'technology': 'copper'
        },
    ]

    parameters = {
        'costs_links_fibre_meter': 5,
        'costs_links_copper_meter': 3,
        'costs_assets_exchange_fttp': 50000,
        'costs_assets_exchange_fttdp': 25000,
        'costs_assets_exchange_fttc': 30000,
        'costs_assets_exchange_adsl': 20000,
        'costs_assets_cabinet_fttp': 50,
        'costs_assets_cabinet_fttdp': 2500,
        'costs_assets_cabinet_fttc': 3000,
        'costs_assets_cabinet_adsl': 2000,
        'costs_assets_distribution_fttp_32_ports': 10,
        'costs_assets_distribution_fttdp_8_ports': 250,
        'costs_assets_distribution_fttc': 300,
        'costs_assets_distribution_adsl': 200,
        'costs_assets_premise_fttp_modem': 20,
        'costs_assets_premise_fttp_optical_network_terminator': 10,
        'costs_assets_premise_fttp_optical_connection_point': 37,
        'costs_assets_premise_fttdp_modem': 20,
        'costs_assets_premise_fttc_modem': 15,
        'costs_assets_premise_adsl_modem': 10,
        'benefits_assets_premise_fttp': 50,
        'benefits_assets_premise_fttdp': 40,
        'benefits_assets_premise_fttc': 30,
        'benefits_assets_premise_adsl': 20,
        'planning_administration_cost': 10,
        'months_per_year': 12,
        'payback_period': 4,
        'profit_margin': 20,
    }

    system = NetworkManager(assets, links, parameters)

    return system


@pytest.fixture
def technology():

    return 'fttp'


@pytest.fixture
def small_system(base_system, technology):

    #40% want to adopt in total
    distribution_adoption_desirability_ids = update_adoption_desirability(
        base_system._distributions, 40, technology
    )

    #update model adoption desirability
    base_system.update_adoption_desirability(distribution_adoption_desirability_ids)

    return base_system


class TestUpgradeExchange:
    """
    """

    def test_compute_exchange(self, base_system):

        actual = base_system._exchanges[0]
        assert actual.id == 'exchange_EACAM'
        assert actual.fttp == 0
        assert actual.fttdp == 0
        assert actual.fttc == 5
        assert actual.docsis3 == 5
        assert actual.adsl == 20
        assert actual.total_prems == 20

        intervention_list = [('exchange_EACAM', 'fttp')]
        base_system.upgrade(intervention_list)

        actual.compute()

        assert actual.id == 'exchange_EACAM'
        assert actual.fttp == 20
        assert actual.fttdp == 0
        assert actual.fttc == 0
        assert actual.docsis3 == 0
        assert actual.adsl == 0
        assert actual.total_prems == 20

    def test_upgrade_exchange_base(self, base_system):

        actual = base_system._exchanges[0]
        assert actual.id == 'exchange_EACAM'
        assert actual.fttp == 0
        assert actual.fttdp == 0
        assert actual.fttc == 5
        assert actual.docsis3 == 5
        assert actual.adsl == 20
        assert actual.total_prems == 20
        assert isinstance(actual._clients, list)

        intervention_list = [('exchange_EACAM', 'fttp')]
        base_system.upgrade(intervention_list)
        actual = base_system._exchanges[0]
        assert actual.fttp == 20
        assert actual.adsl == 0

    def test_upgrade_exchange(self, small_system):

        intervention_list = [('exchange_EACAM', 'fttp')]
        small_system.upgrade(intervention_list)

        actual = small_system._exchanges[0]

        assert actual.id == 'exchange_EACAM'
        assert actual.fttp == 20
        assert actual.fttdp == 0
        assert actual.fttc == 0
        assert actual.docsis3 == 0
        assert actual.adsl == 0
        assert actual.total_prems == 20
        assert isinstance(actual._clients, list)

    def test_sequence_upgrade_exchange(self, small_system):

        intervention_list = [('exchange_EACAM', 'fttp')]
        small_system.upgrade(intervention_list)

        actual = small_system._exchanges[0]

        assert actual.id == 'exchange_EACAM'
        assert actual.fttp == 20
        assert actual.fttdp == 0
        assert actual.fttc == 0
        assert actual.docsis3 == 0
        assert actual.adsl == 0
        assert actual.total_prems == 20
        assert isinstance(actual._clients, list)

        intervention_list = [('exchange_EACAM', 'fttdp')]
        small_system.upgrade(intervention_list)

        actual = small_system._exchanges[0]

        assert actual.id == 'exchange_EACAM'
        assert actual.fttp == 0
        assert actual.fttdp == 20
        assert actual.fttc == 0
        assert actual.docsis3 == 5
        assert actual.adsl == 20
        assert actual.total_prems == 20
        assert isinstance(actual._clients, list)



def test_coverage(small_system):

    expected_coverage = {
        'ABABA':{
            'num_premises': 20,
            'num_fttp': 0,
            'num_fttdp': 0,
            'num_fttc': 5,
            'num_docsis3': 5,
            'num_adsl': 20
        }
    }

    actual_coverage = small_system.coverage()

    assert expected_coverage == actual_coverage

def test_aggregate_coverage(small_system):

    expected_aggregate_coverage = [{
        'id': 'ABABA',
        'percentage_of_premises_with_fttp': 0.0,
        'percentage_of_premises_with_fttdp': 0.0,
        'percentage_of_premises_with_fttc': 25.0,
        'percentage_of_premises_with_docsis3': 25.0,
        'percentage_of_premises_with_adsl': 100.0,
        'sum_of_premises': 20
    }]

    actual_aggregate_coverage = small_system.aggregate_coverage('lad')

    assert expected_aggregate_coverage == actual_aggregate_coverage

def test_capacity(small_system):

    expected_capacity = [{
        'id': 'ABABA',
        #  fttp       fttdp     fttc     docsis3   adsl
        # ((0*1000) + (0*300) + (5*80) + (5*150) + (10*24)) / 20 == round(69.5)
        'average_capacity': 70,
    }]

    actual_capacity = small_system.capacity('lad')

    assert expected_capacity == actual_capacity

def test_fttp_costs(small_system):

    actual_total_costs = small_system.get_total_upgrade_costs('fttp')

    #### dist_point to premises = £1837.0 ###
    #costs_assets_premise_fttp_modem: 20 * 20 = 400
    #costs_assets_premise_fttp_optical_network_terminator = 10 * 20 = 200
    #planning administation code = £10 * 20 = £200
    #costs_assets_premise_fttp_optical_connection_point: 37 * 1 = 37
    #fibre = £5 * 200 = £1000

    #### cabinet to dist_point = £520.0 ###
    #fibre = £5 * 94 = £470
    #costs_assets_upgrade_cabinet_fttp = £50

    #### exchange to cabinet = £56485 ###
    #costs_assets_upgrade_exchange_fttp = £50000
    #fibre = £5 * 1297 = £6485

    expected_total_costs = (1837.0, 520.0, 56485.0)

    assert actual_total_costs['distribution_{EACAM}{795}'] == expected_total_costs

def test_fttdp_costs(small_system):

    #get actual costs
    actual_total_costs = small_system.get_total_upgrade_costs('fttdp')

    #### dist_point to premises = £1150.0 ###
    #'costs_assets_premise_fttdp_modem': 20 * 20 = 400,
    #'costs_assets_distribution_fttdp_8_ports': 250 * 3 = £750,

    #### cabinet to dist_point = £2970.0 ###
    #fibre = £5 * 94 = £470,
    #'costs_assets_cabinet_fttdp': 2500,

    #### exchange to cabinet = 25000.0 ###
    #'costs_assets_exchange_fttdp': 40000,
    #fibre = £5 * 1297 = £6485

    expected_total_costs = (1150.0, 2970.0, 31485.0)

    assert actual_total_costs['distribution_{EACAM}{795}'] == expected_total_costs

def test_fttp_upgrade_exchanges(small_system):

    year = 2019
    technology = 'fttp'
    policy = 's1_market_based_roll_out'
    annual_budget = 100000
    adoption_cap = 40
    subsidy = 10000
    telco_match_funding = 10000
    service_obligation_capacity = 10

    #build interventions
    built_interventions = decide_interventions(
        small_system._exchanges, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity, 'exchange')

    small_system.upgrade(built_interventions)

    actual_coverage = small_system.coverage()

    expected_coverage = {
        'ABABA':{
            'num_premises': 20,
            'num_fttp': 20,
            'num_fttdp': 0,
            'num_fttc': 0,
            'num_docsis3': 0,
            'num_adsl': 0
        }
    }

    assert expected_coverage == actual_coverage

def test_fttp_upgrade_cabinets(small_system):

    year = 2019
    technology = 'fttp'
    policy = 's1_market_based_roll_out'
    annual_budget = 3000
    adoption_cap = 40
    subsidy = 3000
    telco_match_funding = 3000
    service_obligation_capacity = 10

    #build interventions
    built_interventions = decide_interventions(
        small_system._cabinets, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity, 'cabinet')

    small_system.upgrade(built_interventions)

    actual_coverage = small_system.coverage()

    expected_coverage = {
        'ABABA':{
            'num_premises': 20,
            'num_fttp': 20,
            'num_fttdp': 0,
            'num_fttc': 0,
            'num_docsis3': 0,
            'num_adsl': 0
        }
    }

    assert expected_coverage == actual_coverage

def test_fttp_upgrade_distributions(small_system):

    year = 2019
    technology = 'fttp'
    policy = 's1_market_based_roll_out'
    annual_budget = 2000
    adoption_cap = 40
    subsidy = 2000
    telco_match_funding = 2000
    service_obligation_capacity = 10

    #build interventions
    built_interventions = decide_interventions(
        small_system._distributions, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity, 'distribution')

    small_system.upgrade(built_interventions)

    actual_coverage = small_system.coverage()

    expected_coverage = {
        'ABABA':{
            'num_premises': 20,
            'num_fttp': 20,
            'num_fttdp': 0,
            'num_fttc': 0,
            'num_docsis3': 0,
            'num_adsl': 0
        }
    }

    assert expected_coverage == actual_coverage

def test_fttdp_upgrade_distributions(small_system):

    year = 2019
    technology = 'fttdp'
    policy = 's1_market_based_roll_out'
    annual_budget = 2000
    adoption_cap = 40
    subsidy = 2000
    telco_match_funding = 2000
    service_obligation_capacity = 10

    # build interventions
    built_interventions = decide_interventions(
        small_system._distributions, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity, 'distribution')

    small_system.upgrade(built_interventions)

    actual_coverage = small_system.coverage()

    expected_coverage = {
        'ABABA':{
            'num_premises': 20,
            'num_fttp': 0,
            'num_fttdp': 20,
            'num_fttc': 0,
            'num_docsis3': 0,
            'num_adsl': 0
        }
    }

    assert expected_coverage == actual_coverage

# def upgrade_exchange_with_fttp(small_system):

#     year = 2019
#     technology = 'fttp'
#     policy = 's1_market_based_roll_out'
#     annual_budget = 1000000
#     adoption_cap = 70
#     subsidy = 2000
#     telco_match_funding = 2000
#     service_obligation_capacity = 10

#     #build interventions
#     fttp_s1_built_interventions = decide_interventions(
#         small_system._distributions, year, technology, policy, annual_budget, adoption_cap,
#         subsidy, telco_match_funding, service_obligation_capacity, 'exchange')
#     print(fttp_s1_built_interventions)
#     assert fttp_s1_built_interventions == 'fail'





def test_enhanced_fttp_capacity_at_lad(small_system):

    year = 2019
    technology = 'fttp'
    policy = 's1_market_based_roll_out'
    annual_budget = 10000000
    adoption_cap = 40
    subsidy = 2000
    telco_match_funding = 2000
    service_obligation_capacity = 10

    #build interventions
    built_interventions = decide_interventions(
        small_system._exchanges, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity, 'exchange')

    small_system.upgrade(built_interventions)

    expected_capacity = [{
        'id': 'ABABA',
        #  fttp       fttdp     fttc     docsis3   adsl
        # ((20*1000) + (0*300) + (5*80) + (5*150) + (0*24)) / 20 == round(69.5)
        'average_capacity': 1000,
    }]

    actual_capacity = small_system.capacity('lad')

    assert expected_capacity == actual_capacity

def test_enhanced_fttp_capacity_at_exchange(small_system):

    year = 2019
    technology = 'fttp'
    policy = 's1_market_based_roll_out'
    annual_budget = 10000000
    adoption_cap = 40
    subsidy = 2000
    telco_match_funding = 2000
    service_obligation_capacity = 10

    #build interventions
    built_interventions = decide_interventions(
        small_system._exchanges, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity, 'exchange')

    small_system.upgrade(built_interventions)

    expected_capacity = [{
        'id': 'exchange_EACAM',
        #  fttp       fttdp     fttc     docsis3   adsl
        # ((20*1000) + (0*300) + (5*80) + (5*150) + (0*24)) / 20 == round(69.5)
        'average_capacity': 1000,
    }]

    actual_capacity = small_system.capacity('exchange')

    assert expected_capacity == actual_capacity
