import pytest
from digital_comms.fixed_network.model import NetworkManager
from digital_comms.fixed_network.adoption import update_adoption_desirability
from digital_comms.fixed_network.interventions import get_all_assets_ranked
from digital_comms.fixed_network.interventions import decide_interventions

@pytest.fixture
def base_system():

    assets = {
        'distributions':[{
            'id': 'distribution_{EACAM}{1}',
            'lad': 'E07000008',
            'connection': 'cabinet_{EACAM}{P100}',
            'fttp': 0,
            'fttdp': 0,
            'fttc': 5,
            'docsis3': 5,
            'adsl': 20,
            'total_prems': 20,
            'wta': 0.4,
            'wtp': 800,
            'name': 'distribution_{EACAM}{1}',
            'adoption_desirability': True
        },
        {
            'id': 'distribution_{EACAM}{2}',
            'lad': 'E07000008',
            'connection': 'cabinet_{EACAM}{P100}',
            'fttp': 0,
            'fttdp': 0,
            'fttc': 5,
            'docsis3': 5,
            'adsl': 20,
            'total_prems': 20,
            'wta': 1.0,
            'wtp': 700,
            'name': 'distribution_{EACAM}{2}',
            'adoption_desirability': True
        },
        {
            'id': 'distribution_{EACAM}{3}',
            'lad': 'E07000008',
            'connection': 'cabinet_{EACAM}{P100}',
            'fttp': 0,
            'fttdp': 0,
            'fttc': 5,
            'docsis3': 5,
            'adsl': 20,
            'total_prems': 20,
            'wta': 1.5,
            'wtp': 600,
            'name': 'distribution_{EACAM}{3}',
            'adoption_desirability': True
        },
        {
            'id': 'distribution_{EACOM}{4}',
            'lad': 'E07000012',
            'connection': 'cabinet_{EACOM}{P200}',
            'fttp': 0,
            'fttdp': 0,
            'fttc': 5,
            'docsis3': 5,
            'adsl': 20,
            'total_prems': 20,
            'wta': 0.3,
            'wtp': 500,
            'name': 'distribution_{EACOM}{4}',
            'adoption_desirability': True
        },
        {
            'id': 'distribution_{EACOM}{5}',
            'lad': 'E07000012',
            'connection': 'cabinet_{EACOM}{P200}',
            'fttp': 0,
            'fttdp': 0,
            'fttc': 5,
            'docsis3': 5,
            'adsl': 20,
            'total_prems': 20,
            'wta': 0.2,
            'wtp': 600,
            'name': 'distribution_{EACOM}{5}',
            'adoption_desirability': True
        }
        ],
        'cabinets':[{
            'id': 'cabinet_{EACAM}{P100}',
            'connection': 'exchange_EACAM',
            'fttp': 0,
            'fttdp': 0,
            'fttc': 5,
            'docsis3': 0,
            'adsl': 1,
            'name': 'cabinet_{EACAM}{P100}',
        },
        {
            'id': 'cabinet_{EACOM}{P200}',
            'connection': 'exchange_EACOM',
            'fttp': 0,
            'fttdp': 0,
            'fttc': 5,
            'docsis3': 0,
            'adsl': 1,
            'name': 'cabinet_{EACOM}{P200}',
        }],
        'exchanges':[{
            'id': 'exchange_EACAM',
            'Name': 'Cambridge',
            'pcd': '?',
            'Region': 'East',
            'County': 'Cambridgeshire',
            'fttp': 0,
            'fttdp': 0,
            'fttc': 1,
            'docsis3': 0,
            'adsl': 1,
        },
        {
            'id': 'exchange_EACOM',
            'Name': 'Cambridge',
            'pcd': '?',
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
        'dest': 'distribution_{EACAM}{1}',
        'length': 200,
        'technology': 'copper'
        },
        {
        'origin': 'premises_aggregated',
        'dest': 'distribution_{EACAM}{2}',
        'length': 250,
        'technology': 'copper'
        },
        {
        'origin': 'premises_aggregated',
        'dest': 'distribution_{EACAM}{3}',
        'length': 300,
        'technology': 'copper'
        },
        {
        'origin': 'premises_aggregated',
        'dest': 'distribution_{EACOM}{4}',
        'length': 350,
        'technology': 'copper'
        },
        {
        'origin': 'premises_aggregated',
        'dest': 'distribution_{EACOM}{5}',
        'length': 400,
        'technology': 'copper'
        },
        {
        'origin': 'distribution_{EACAM}{1}',
        'dest': 'cabinet_{EACAM}{P100}',
        'length': 200,
        'technology': 'copper'
        },
        {
        'origin': 'distribution_{EACAM}{2}',
        'dest': 'cabinet_{EACAM}{P100}',
        'length': 250,
        'technology': 'copper'
        },
        {
        'origin': 'distribution_{EACAM}{3}',
        'dest': 'cabinet_{EACAM}{P100}',
        'length': 300,
        'technology': 'copper'
        },
        {
        'origin': 'distribution_{EACOM}{4}',
        'dest': 'cabinet_{EACOM}{P200}',
        'length': 350,
        'technology': 'copper'
        },
        {
        'origin': 'distribution_{EACOM}{5}',
        'dest': 'cabinet_{EACOM}{P200}',
        'length': 400,
        'technology': 'copper'
        },
        {
        'origin': 'cabinet_{EACAM}{P100}',
        'dest': 'exchange_EACAM',
        'length': 1000,
        'technology': 'fibre'
        },
        {
        'origin': 'cabinet_{EACOM}{P200}',
        'dest': 'exchange_EACOM',
        'length': 1000,
        'technology': 'fibre'
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

    #create system using network manager
    system = NetworkManager(assets, links, parameters)

    #40% want to adopt in total
    distribution_adoption_desirability_ids = update_adoption_desirability(system, 40)

    #update model adoption desirability
    system.update_adoption_desirability(distribution_adoption_desirability_ids)

    return system

@pytest.fixture
def small_system_40(base_system):

    #40% want to adopt in total
    distribution_adoption_desirability_ids = update_adoption_desirability(base_system, 40)

    #update model adoption desirability
    base_system.update_adoption_desirability(distribution_adoption_desirability_ids)

    return base_system

@pytest.fixture
def small_system_80(base_system):

    #40% want to adopt in total
    distribution_adoption_desirability_ids = update_adoption_desirability(base_system, 80)

    #update model adoption desirability
    base_system.update_adoption_desirability(distribution_adoption_desirability_ids)

    return base_system

def test_ranking_benefits_by_exchange(small_system_40):

    #my_list = [600, 100, 200, 300]
    #print(sorted(my_list, reverse=False))
    # [100, 200, 300, 600]

    actual_ranking_by_benefit = get_all_assets_ranked(small_system_40,
        'rollout_benefits', 'exchange', 'fttp', False)

    actual_ranking_by_benefit_ids = [asset.id for asset in actual_ranking_by_benefit]

    expectation_ranking_by_benefit = [
        'exchange_EACOM',
        'exchange_EACAM',
    ]

    assert expectation_ranking_by_benefit == actual_ranking_by_benefit_ids

def test_ranking_benefits_by_exchange_reversed(small_system_40):

    #my_list = [600, 100, 200, 300]
    #print(sorted(my_list, reverse=True))
    # [600, 300, 200, 100]

    actual_ranking_by_benefit = get_all_assets_ranked(small_system_40,
        'rollout_benefits', 'exchange', 'fttp', True)

    actual_ranking_by_benefit_ids = [asset.id for asset in actual_ranking_by_benefit]


    expectation_ranking_by_benefit = [
        'exchange_EACAM',
        'exchange_EACOM',
    ]

    assert expectation_ranking_by_benefit == actual_ranking_by_benefit_ids

def test_benefits_calculation_by_exchange(small_system_40):

    #two dists capable of ungrading totalling £49920
    #benefit = wtp * months * payback_years * ((100-profit_margin)/100)
    #£26880 = 700 * 12 * 4 * (100-20)/100)
    #£23040 = 600 * 12 * 4 * (100-20)/100)

    actual_ranking_by_benefit = get_all_assets_ranked(small_system_40,
        'rollout_benefits', 'exchange', 'fttp', False)

    actual_benefits_calculation = [asset.rollout_benefits['fttp'] for asset in actual_ranking_by_benefit]

    expectation_benefits_calculation = [0, 49920.0]

    assert expectation_benefits_calculation == actual_benefits_calculation

def test_ranking_benefits_by_cabinet(small_system_40):

    actual_ranking_by_benefit = get_all_assets_ranked(small_system_40,
        'rollout_benefits', 'cabinet', 'fttp', False)

    actual_ranking_by_benefit_ids = [asset.id for asset in actual_ranking_by_benefit]

    expectation_ranking_by_benefit = [
        'cabinet_{EACOM}{P200}',
        'cabinet_{EACAM}{P100}',
    ]

    assert expectation_ranking_by_benefit == actual_ranking_by_benefit_ids

def test_ranking_benefits_by_cabinet_reversed(small_system_40):

    actual_ranking_by_benefit = get_all_assets_ranked(small_system_40,
        'rollout_benefits', 'cabinet', 'fttp', True)

    actual_ranking_by_benefit_ids = [asset.id for asset in actual_ranking_by_benefit]

    expectation_ranking_by_benefit = [
        'cabinet_{EACAM}{P100}',
        'cabinet_{EACOM}{P200}',
    ]

    assert expectation_ranking_by_benefit == actual_ranking_by_benefit_ids

def test_ranking_benefits_by_distribution(small_system_80):

    actual_ranking_by_benefit = get_all_assets_ranked(small_system_80,
        'rollout_benefits', 'distribution', 'fttp', True)

    actual_ranking_by_benefit_ids = [asset.id for asset in actual_ranking_by_benefit]

    expectation_ranking_by_benefit = [
        'distribution_{EACAM}{1}',
        'distribution_{EACAM}{2}',
        'distribution_{EACAM}{3}',
        'distribution_{EACOM}{4}',
        'distribution_{EACOM}{5}',
    ]

    assert expectation_ranking_by_benefit == actual_ranking_by_benefit_ids

def test_system_level_using_an_unknown(small_system_40):

    with pytest.raises(ValueError) as ex:
        get_all_assets_ranked(small_system_40, 'rollout_benefits', 'unknown', 'fttp', False)

    msg = 'Did not recognise asset_variable'

    assert msg in str(ex)

def test_rollout_costs_calculation(small_system_40):

    actual_rollout_costs_exchange = get_all_assets_ranked(small_system_40,
        'rollout_costs', 'exchange', 'fttp', True) #True equals most expensive at the top

    # [{'id': 'exchange_EACAM', 'costs_assets_exchange_fttp': 50000, 'link_upgrade_costs': 0, 'total_cost': 50000}]
    # [{'id': 'exchange_EACOM', 'costs_assets_exchange_fttp': 50000, 'link_upgrade_costs': 0, 'total_cost': 50000}]

    actual_rollout_costs_exchange_values = [asset.rollout_costs['fttp'] for asset in actual_rollout_costs_exchange]

    expected_rollout_costs_exchange = [57811, 57474]

    assert actual_rollout_costs_exchange_values == expected_rollout_costs_exchange

    actual_rollout_costs_cabinet = get_all_assets_ranked(small_system_40,
        'rollout_costs', 'cabinet', 'fttp', True) #True equals most expensive at the top

    # [{'id': 'cabinet_{EACAM}{P100}', 'costs_assets_cabinet_fttp': 50, 'link_upgrade_costs': 1500.0, 'total_cost': 1550.0}]
    # [{'id': 'cabinet_{EACOM}{P200}', 'costs_assets_cabinet_fttp': 50, 'link_upgrade_costs': 2000.0, 'total_cost': 2050.0}]

    actual_rollout_costs_cabinet_values = [
        asset.rollout_costs['fttp'] for asset in actual_rollout_costs_cabinet
        ]

    expected_rollout_costs_cabinet = [7811, 7474]

    assert actual_rollout_costs_cabinet_values == expected_rollout_costs_cabinet

    actual_rollout_costs_distribution = get_all_assets_ranked(small_system_40,
        'rollout_costs', 'distribution', 'fttp', True) #True equals the least beneficial at the top

    # [{'id': 'distribution_{EACAM}{1}', 'costs_assets_premise_fttp_modem': 400, 'costs_assets_premise_fttp_optical_network_terminator': 200, 'planning_administration_cost': 200, 'costs_assets_premise_fttp_optical_connection_point': 37, 'link_upgrade_costs': 1000.0, 'total_cost': 1837.0}]
    # [{'id': 'distribution_{EACAM}{2}', 'costs_assets_premise_fttp_modem': 400, 'costs_assets_premise_fttp_optical_network_terminator': 200, 'planning_administration_cost': 200, 'costs_assets_premise_fttp_optical_connection_point': 37, 'link_upgrade_costs': 1250.0, 'total_cost': 2087.0}]
    # [{'id': 'distribution_{EACAM}{3}', 'costs_assets_premise_fttp_modem': 400, 'costs_assets_premise_fttp_optical_network_terminator': 200, 'planning_administration_cost': 200, 'costs_assets_premise_fttp_optical_connection_point': 37, 'link_upgrade_costs': 1500.0, 'total_cost': 2337.0}]
    # [{'id': 'distribution_{EACOM}{4}', 'costs_assets_premise_fttp_modem': 400, 'costs_assets_premise_fttp_optical_network_terminator': 200, 'planning_administration_cost': 200, 'costs_assets_premise_fttp_optical_connection_point': 37, 'link_upgrade_costs': 1750.0, 'total_cost': 2587.0}]
    # [{'id': 'distribution_{EACOM}{5}', 'costs_assets_premise_fttp_modem': 400, 'costs_assets_premise_fttp_optical_network_terminator': 200, 'planning_administration_cost': 200, 'costs_assets_premise_fttp_optical_connection_point': 37, 'link_upgrade_costs': 2000.0, 'total_cost': 2837.0}]

    actual_rollout_costs_distribution_values = [
        asset.rollout_costs['fttp'] for asset in actual_rollout_costs_distribution
        ]

    expected_rollout_costs_distribution = [2837, 2587, 2337, 2087, 1837]

    assert expected_rollout_costs_distribution == actual_rollout_costs_distribution_values

def test_ranking_using_rollout_costs_at_exchange_level(small_system_40):

    actual_ranking_by_cost = get_all_assets_ranked(small_system_40,
        'rollout_costs', 'exchange', 'fttp', True) #True equals most expensive at the top

    actual_ranking_by_cost_ids = [asset.id for asset in actual_ranking_by_cost]

    expectation_ranking_by_cost = [
        'exchange_EACAM',
        'exchange_EACOM',
    ]

    assert expectation_ranking_by_cost == actual_ranking_by_cost_ids

def test_ranking_using_rollout_costs_at_cabinet_level(small_system_40):

    actual_ranking_by_cost = get_all_assets_ranked(small_system_40,
        'rollout_costs', 'cabinet', 'fttp', True) #True equals most expensive at the top

    actual_ranking_by_cost_ids = [asset.id for asset in actual_ranking_by_cost]

    expectation_ranking_by_cost = [
        'cabinet_{EACAM}{P100}',
        'cabinet_{EACOM}{P200}',
    ]

    assert expectation_ranking_by_cost == actual_ranking_by_cost_ids

def test_ranking_using_rollout_costs(small_system_40):

    actual_ranking_by_cost = get_all_assets_ranked(small_system_40,
        'rollout_costs', 'distribution', 'fttp', True)

    actual_ranking_by_cost_ids = [asset.id for asset in actual_ranking_by_cost]

    expectation_ranking_by_cost = [
        'distribution_{EACOM}{5}',
        'distribution_{EACOM}{4}',
        'distribution_{EACAM}{3}',
        'distribution_{EACAM}{2}',
        'distribution_{EACAM}{1}',
    ]

    assert expectation_ranking_by_cost == actual_ranking_by_cost_ids

def test_ranking_using_max_costs(small_system_40):

    actual_ranking_by_cost = get_all_assets_ranked(small_system_40,
        'max_rollout_costs', 'distribution', 'fttp', False)

    actual_ranking_by_cost_ids = [asset.id for asset in actual_ranking_by_cost]

    expectation_ranking_by_cost = [
        'distribution_{EACAM}{1}',
        'distribution_{EACAM}{2}',
        'distribution_{EACAM}{3}',
        'distribution_{EACOM}{4}',
        'distribution_{EACOM}{5}',
    ]

    assert expectation_ranking_by_cost == actual_ranking_by_cost_ids


def test_reverse_ranking_using_max_costs(small_system_40):

    actual_ranking_by_cost = get_all_assets_ranked(small_system_40,
        'max_rollout_costs', 'distribution', 'fttp', True)

    actual_ranking_by_cost_ids = [asset.id for asset in actual_ranking_by_cost]

    expectation_ranking_by_cost = [
        'distribution_{EACOM}{5}',
        'distribution_{EACOM}{4}',
        'distribution_{EACAM}{3}',
        'distribution_{EACAM}{2}',
        'distribution_{EACAM}{1}',
    ]

    assert expectation_ranking_by_cost == actual_ranking_by_cost_ids

def test_ranking_using_an_unknown(small_system_40):

    with pytest.raises(ValueError) as ex:
        get_all_assets_ranked(small_system_40, 'unknown', 'exchange', 'fttp', False)

    msg = 'Did not recognise ranking preference variable'

    assert msg in str(ex)

def test_fttp_s1(small_system_40):

    year = 2019
    technology = 'fttp'
    policy = 's1_market_based_roll_out'
    annual_budget = 10000
    adoption_cap = 40
    subsidy = 2000
    telco_match_funding = 2000
    service_obligation_capacity = 10

    fttp_s1_expected_built_interventions = [
        ('distribution_{EACAM}{2}', 'fttp', 's1_market_based_roll_out', 'market_based', 26880, 2087, 13)
    ]

    #Total cost for the distribution downwards should be £2087
    #fttp modem: £20 * 20 = £400
    #optical network terminal: £10 * 20 = £200
    #planning cost: £10 * 20 = £200
    #optical connection point: £37 * 1 = £37 (32 premises per connection point)
    #distribution point upgrade = £10
    #fibre upgrade cost: £5 * 250 = 1250

    #build interventions
    fttp_s1_built_interventions = decide_interventions(
        small_system_40, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity, 'distribution')

    assert fttp_s1_built_interventions == fttp_s1_expected_built_interventions

def test_fttp_s1_from_exchange(small_system_40):

    year = 2019
    technology = 'fttp'
    policy = 's1_market_based_roll_out'
    annual_budget = 100000
    adoption_cap = 70
    subsidy = 2000
    telco_match_funding = 2000
    service_obligation_capacity = 10

    fttp_s1_expected_built_interventions = [
        ('exchange_EACAM', 'fttp', 's1_market_based_roll_out', 'market_based', 49920, 57811, 1),
        #('exchange_EACOM', 'fttp', 's1_market_based_roll_out', 'market_based', 57474)
    ]

    #Total cost for exchange_EACAM should be:
    #exchange = £50000 +
    #cabinet = 1550 +
    #distribution = £1837 + £2087 + £2337
    # == 57811

    #build interventions
    fttp_s1_built_interventions = decide_interventions(
        small_system_40, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity, 'exchange')

    assert fttp_s1_built_interventions == fttp_s1_expected_built_interventions

def test_fttp_s1_from_cabinet(small_system_40):

    year = 2019
    technology = 'fttp'
    policy = 's1_market_based_roll_out'
    annual_budget = 100000
    adoption_cap = 70
    subsidy = 2000
    telco_match_funding = 2000
    service_obligation_capacity = 10

    fttp_s1_expected_built_interventions = [
        ('cabinet_{EACAM}{P100}', 'fttp', 's1_market_based_roll_out', 'market_based', 49920, 7811, 6)
    ]

    #Total cost for exchange_EACOM should be:
    #cabinet = 1550 +
    #distribution = £1837 + £2087 + £2337
    # == 7811

    #build interventions
    fttp_s1_built_interventions = decide_interventions(
        small_system_40, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity, 'cabinet')

    assert fttp_s1_built_interventions == fttp_s1_expected_built_interventions


def test_fttp_s2_from_exchange(small_system_40):

    year = 2019
    technology = 'fttp'
    policy = 's2_rural_based_subsidy'
    annual_budget = 60000
    adoption_cap = 80
    subsidy = 60000
    telco_match_funding = 60000
    service_obligation_capacity = 10

    fttp_s2_expected_built_interventions = [
        ('exchange_EACAM', 'fttp', 's2_rural_based_subsidy', 'market_based', 49920, 57811, 1),
        ('exchange_EACOM', 'fttp', 's2_rural_based_subsidy', 'subsidy_based', 0, 57474, 0),
        ]

    #build interventions
    fttp_s2_built_interventions = decide_interventions(
        small_system_40, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity, 'exchange')

    assert fttp_s2_built_interventions == fttp_s2_expected_built_interventions

def test_fttp_s3(small_system_40):

    year = 2019
    technology = 'fttp'
    policy = 's3_outside_in_subsidy'
    annual_budget = 60000
    adoption_cap = 80
    subsidy = 60000
    telco_match_funding = 60000
    service_obligation_capacity = 10

    fttp_s3_expected_built_interventions = [
        ('exchange_EACAM', 'fttp', 's3_outside_in_subsidy', 'market_based', 49920, 57811, 1),
        ('exchange_EACOM', 'fttp', 's3_outside_in_subsidy', 'subsidy_based', 0, 57474, 0),
        ]

    #Total cost should be £1837
    #fttp modem: £20 * 20 = £400
    #optical network terminal: £10 * 20 = £200
    #planning cost: £10 * 20 = £200
    #optical connection point: £37 * 1 = £37 (32 premises per connection point)
    #fibre upgrade cost: £5 * 200 = 1000

    #Total cost should be 2837
    #fttp modem: £20 * 20 = £400
    #optical network terminal: £10 * 20 = £200
    #planning cost: £10 * 20 = £200
    #optical connection point: £37 * 1 = £37 (32 premises per connection point)
    #fibre upgrade cost: £5 * 400 = 2000

    #build interventions
    fttp_s3_built_interventions = decide_interventions(
        small_system_40, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity, 'exchange')

    assert fttp_s3_built_interventions == fttp_s3_expected_built_interventions

    with pytest.raises(ValueError) as ex:
        decide_interventions(
        small_system_40, year, technology, 'unknown_policy', annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity, 'exchange')

    msg = 'Did not recognise stipulated policy'

    assert msg in str(ex)

def test_fttdp_s1_from_exchange(small_system_40):

    year = 2019
    technology = 'fttdp'
    policy = 's1_market_based_roll_out'
    annual_budget = 60000
    adoption_cap = 80
    subsidy = 2000
    telco_match_funding = 2000
    service_obligation_capacity = 10

    fttdp_s1_expected_built_interventions = [
        ('exchange_EACAM', 'fttdp', 's1_market_based_roll_out', 'market_based',  49920, 32450, 2),
    ]

    #Total cost should be £32400
    #fttdp modem: £20 * 20 = £400
    #costs_assets_distribution_fttdp_8_ports: £250 * 3 = £750
    #fibre from cab to dist: £5 * (200+250+300) = £3750
    #cabinet upgrade = £2500
    #exchange upgrade = £25000

    #build interventions
    fttdp_s1_built_interventions = decide_interventions(
        small_system_40, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity, 'exchange')

    assert fttdp_s1_built_interventions == fttdp_s1_expected_built_interventions

# def test_fttdp_s2(small_system_40):

#     year = 2019
#     technology = 'fttdp'
#     policy = 's2_rural_based_subsidy'
#     annual_budget = 2500
#     adoption_cap = 40
#     subsidy = 2500
#     telco_match_funding = 2500
#     service_obligation_capacity = 10

#     fttdp_s2_expected_built_interventions = [
#         ('distribution_{EACAM}{1}', 'fttdp', 's2_rural_based_subsidy', 'market_based', 1837),
#         ('distribution_{EACAM}{2}', 'fttdp', 's2_rural_based_subsidy', 'subsidy_based', 2087)
#         ]

#     #Total cost should be £2150
#     #fttdp modem: £20 * 20 = £400
#     #costs_assets_distribution_fttdp_8_ports: £250 * 3 = £750
#     #fibre from cab to dist: £5 * 200 = £1000

#     #Total cost should be £2400
#     #fttdp modem: £20 * 20 = £400
#     #costs_assets_distribution_fttdp_8_ports: £250 * 3 = £750
#     #fibre from cab to dist: £5 * 250 = £1250

#     #build interventions
#     fttdp_s2_built_interventions = decide_interventions(
#         small_system_40, year, technology, policy, annual_budget, adoption_cap,
#         subsidy, telco_match_funding, service_obligation_capacity)

#     assert fttdp_s2_built_interventions == fttdp_s2_expected_built_interventions

# def test_fttdp_s3(small_system_40):

#     year = 2019
#     technology = 'fttdp'
#     policy = 's3_outside_in_subsidy'
#     annual_budget = 4000
#     adoption_cap = 40
#     subsidy = 4000
#     telco_match_funding = 4000
#     service_obligation_capacity = 10

#     fttdp_s3_expected_built_interventions = [
#         ('distribution_{EACAM}{1}', 'fttdp', 's3_outside_in_subsidy', 'market_based', 1837),
#         ('distribution_{EACOM}{5}', 'fttdp', 's3_outside_in_subsidy', 'subsidy_based', 2837)
#         ]

#     #build interventions
#     fttdp_s3_built_interventions = decide_interventions(
#         small_system_40, year, technology, policy, annual_budget, adoption_cap,
#         subsidy, telco_match_funding, service_obligation_capacity)
#     print(fttdp_s3_built_interventions)
#     assert fttdp_s3_built_interventions == fttdp_s3_expected_built_interventions

# def test_budget(small_system_80):

#     year = 2019
#     technology = 'fttp'
#     policy = 's1_market_based_roll_out'
#     annual_budget = 2000
#     adoption_cap = 40
#     subsidy = 2000
#     telco_match_funding = 2000
#     service_obligation_capacity = 10

#     expected_budget_constrained_interventions = [
#         ('distribution_{EACAM}{1}', 'fttp', 's1_market_based_roll_out', 'market_based', 1837)
#     ]

#     #Total cost should be £1837
#     #fttp modem: £20 * 20 = £400
#     #optical network terminal: £10 * 20 = £200
#     #planning cost: £10 * 20 = £200
#     #optical connection point: £37 * 1 = £37 (32 premises per connection point)
#     #fibre upgrade cost: £5 * 200 = 1000

#     #build interventions
#     budget_constrained_interventions = decide_interventions(
#         small_system_80, year, technology, policy, annual_budget, adoption_cap,
#         subsidy, telco_match_funding, service_obligation_capacity)

#     assert budget_constrained_interventions == expected_budget_constrained_interventions
