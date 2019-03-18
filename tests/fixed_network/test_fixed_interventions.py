from digital_comms.fixed_network.model import NetworkManager
from digital_comms.fixed_network.adoption import update_adoption_desirability
from digital_comms.fixed_network.interventions import decide_interventions

def test_init_from_data():
    """import decide_interventions and test function.

    S1 = FTTP, market_based_roll_out
    S2 = FTTP, rural_based_subsidy
    S3 = FTTP, outside_in_subsidy
    S4 = FTTdp, market_based_roll_out
    S5 = FTTdp, rural_based_subsidy
    S6 = FTTdp, outside_in_subsidy

    """
    # setup phase
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
            'fttp': '0',
            'fttdp': '0',
            'fttc': '0',
            'docsis3': '0',
            'adsl': '1',
            'name': 'cabinet_{EACAM}{P100}',
        },
        {
            'id': 'cabinet_{EACOM}{P200}',
            'connection': 'exchange_EACOM',
            'fttp': '0',
            'fttdp': '0',
            'fttc': '0',
            'docsis3': '0',
            'adsl': '1',
            'name': 'cabinet_{EACOM}{P200}',
        }],
        'exchanges':[{
            'id': 'exchange_EACAM',
            'Name': 'Cambridge',
            'pcd': '?',
            'Region': 'East',
            'County': 'Cambridgeshire',
            'fttp': '0',
            'fttdp': '0',
            'fttc': '0',
            'docsis3': '0',
            'adsl': '1',
        },
        {
            'id': 'exchange_EACOM',
            'Name': 'Cambridge',
            'pcd': '?',
            'Region': 'East',
            'County': 'Cambridgeshire',
            'fttp': '0',
            'fttdp': '0',
            'fttc': '0',
            'docsis3': '0',
            'adsl': '1',
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
        'dest': 'cabinet_{EACAM}{100}',
        'length': 200,
        'technology': 'copper'
        },
        {
        'origin': 'distribution_{EACAM}{2}',
        'dest': 'cabinet_{EACAM}{100}',
        'length': 250,
        'technology': 'copper'
        },
        {
        'origin': 'distribution_{EACAM}{3}',
        'dest': 'cabinet_{EACAM}{100}',
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
        'length': 0,
        'technology': 'fibre'
        },
        {
        'origin': 'cabinet_{EACOM}{P200}',
        'dest': 'exchange_EACOM',
        'length': 0,
        'technology': 'fibre'
        },
    ]

    parameters = {
        'costs_links_fibre_meter': 5,
        'costs_links_copper_meter': 3,
        'costs_assets_exchange_fttp': 50000,
        'costs_assets_exchange_fttc': 30000,
        'costs_assets_exchange_fttdp': 25000,
        'costs_assets_exchange_adsl': 20000,
        'costs_assets_cabinet_fttp_32_ports': 10,
        'costs_assets_cabinet_fttdp': 4000,
        'costs_assets_cabinet_fttc': 3000,
        'costs_assets_cabinet_fttdp': 2500,
        'costs_assets_cabinet_adsl': 2000,
        'costs_assets_distribution_fttp_32_ports': 10,
        'costs_assets_distribution_fttdp_4_ports': 1500,
        'costs_assets_distribution_fttc': 300,
        'costs_assets_distribution_fttdp_8_ports': 250,
        'costs_assets_distribution_adsl': 200,
        'costs_assets_premise_fttp_modem': 20,
        'costs_assets_premise_fttp_optical_network_terminator': 10,
        'costs_assets_premise_fttp_optical_connection_point': 37,
        'costs_assets_premise_fttdp_modem': 20,
        'costs_assets_premise_fttc_modem': 15,
        'costs_assets_premise_fttdp_modem': 12,
        'costs_assets_premise_adsl_modem': 10,
        'benefits_assets_premise_fttp': 50,
        'benefits_assets_premise_fttdp': 40,
        'benefits_assets_premise_fttc': 30,
        'benefits_assets_premise_adsl': 20,
        'planning_administration_cost': 10,
    }

    #####################################################
    #TEST S1 FTTP
    #####################################################

    year = 2019
    technology = 'fttp'
    policy = 's1_market_based_roll_out'
    annual_budget = 2000
    adoption_cap = 40
    subsidy = 2000
    telco_match_funding = 2000
    service_obligation_capacity = 10

    s1_expected_built_interventions = [
        ('distribution_{EACAM}{1}', 'fttp', 's1_market_based_roll_out', 'market_based', 1837)
    ]

    system = NetworkManager(assets, links, parameters)

    #40% want to adopt in total
    distribution_adoption_desirability_ids = update_adoption_desirability(system, 40)

    #update model adoption desirability
    system.update_adoption_desirability(distribution_adoption_desirability_ids)

    #Total cost should be £1837
    #fttp modem: £20 * 20 = £400
    #optical network terminal: £10 * 20 = £200
    #planning cost: £10 * 20 = £200
    #optical connection point: £37 * 1 = £37 (32 premises per connection point)
    #fibre upgrade cost: £5 * 200 = 1000

    #build interventions
    s1_built_interventions = decide_interventions(
        system, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity)

    assert s1_built_interventions == s1_expected_built_interventions


    #####################################################
    #TEST S2 FTTP
    #####################################################

    year = 2019
    technology = 'fttp'
    policy = 's2_rural_based_subsidy'
    annual_budget = 2500
    adoption_cap = 40
    subsidy = 2500
    telco_match_funding = 2500
    service_obligation_capacity = 10

    s2_expected_built_interventions = [
        ('distribution_{EACAM}{1}', 'fttp', 's2_rural_based_subsidy', 'market_based', 1837),
        ('distribution_{EACAM}{2}', 'fttp', 's2_rural_based_subsidy', 'subsidy_based', 2087)
        ]

    #Total cost should be £1837
    #fttp modem: £20 * 20 = £400
    #optical network terminal: £10 * 20 = £200
    #planning cost: £10 * 20 = £200
    #optical connection point: £37 * 1 = £37 (32 premises per connection point)
    #fibre upgrade cost: £5 * 200 = 1000

    #Total cost should be 2087
    #fttp modem: £20 * 20 = £400
    #optical network terminal: £10 * 20 = £200
    #planning cost: £10 * 20 = £200
    #optical connection point: £37 * 1 = £37 (32 premises per connection point)
    #fibre upgrade cost: £5 * 250 = 1250

    #build interventions
    s2_built_interventions = decide_interventions(
        system, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity)

    assert s2_built_interventions == s2_expected_built_interventions

    #####################################################
    #TEST S3 FTTP
    #####################################################

    year = 2019
    technology = 'fttp'
    policy = 's3_outside_in_subsidy'
    annual_budget = 4000
    adoption_cap = 40
    subsidy = 4000
    telco_match_funding = 4000
    service_obligation_capacity = 10

    s3_expected_built_interventions = [
        ('distribution_{EACAM}{1}', 'fttp', 's3_outside_in_subsidy', 'market_based', 1837),
        ('distribution_{EACOM}{5}', 'fttp', 's3_outside_in_subsidy', 'subsidy_based', 2837)
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
    s3_built_interventions = decide_interventions(
        system, year, technology, policy, annual_budget, adoption_cap,
        subsidy, telco_match_funding, service_obligation_capacity)

    assert s3_built_interventions == s3_expected_built_interventions

    # #####################################################
    # #TEST S4 FTTdp
    # #####################################################

    # year = 2019
    # technology = 'fttdp'
    # policy = 's1_market_based_roll_out'
    # annual_budget = 2000
    # adoption_cap = 40
    # subsidy = 2000
    # telco_match_funding = 2000
    # service_obligation_capacity = 10

    # s4_expected_built_interventions = [
    #     ('distribution_{EACAM}{1}', 'fttdp', 's1_market_based_roll_out', 'market_based', 1837)
    # ]

    # system = NetworkManager(assets, links, parameters)

    # #40% want to adopt in total
    # distribution_adoption_desirability_ids = update_adoption_desirability(system, 40)

    # #update model adoption desirability
    # system.update_adoption_desirability(distribution_adoption_desirability_ids)

    # #Total cost should be £1150
    # #fttdp modem: £20 * 20 = £400
    # #costs_assets_distribution_fttdp_8_ports: £250 * 3 = £750

    # #build interventions
    # s4_built_interventions = decide_interventions(
    #     system, year, technology, policy, annual_budget, adoption_cap,
    #     subsidy, telco_match_funding, service_obligation_capacity)

    # assert s4_built_interventions == s4_expected_built_interventions

    # #####################################################
    # #TEST S2 FTTdp
    # #####################################################

    # year = 2019
    # technology = 'fttp'
    # policy = 's2_rural_based_subsidy'
    # annual_budget = 2500
    # adoption_cap = 40
    # subsidy = 2500
    # telco_match_funding = 2500
    # service_obligation_capacity = 10

    # s2_expected_built_interventions = [
    #     ('distribution_{EACAM}{1}', 'fttp', 's2_rural_based_subsidy', 'market_based', 1837),
    #     ('distribution_{EACAM}{2}', 'fttp', 's2_rural_based_subsidy', 'subsidy_based', 2087)
    #     ]

    # #Total cost should be £1837
    # #fttp modem: £20 * 20 = £400
    # #optical network terminal: £10 * 20 = £200
    # #planning cost: £10 * 20 = £200
    # #optical connection point: £37 * 1 = £37 (32 premises per connection point)
    # #fibre upgrade cost: £5 * 200 = 1000

    # #Total cost should be 2087
    # #fttp modem: £20 * 20 = £400
    # #optical network terminal: £10 * 20 = £200
    # #planning cost: £10 * 20 = £200
    # #optical connection point: £37 * 1 = £37 (32 premises per connection point)
    # #fibre upgrade cost: £5 * 250 = 1250

    # #build interventions
    # s2_built_interventions = decide_interventions(
    #     system, year, technology, policy, annual_budget, adoption_cap,
    #     subsidy, telco_match_funding, service_obligation_capacity)

    # assert s2_built_interventions == s2_expected_built_interventions

    # #####################################################
    # #TEST S3 FTTdp
    # #####################################################

    # year = 2019
    # technology = 'fttp'
    # policy = 's3_outside_in_subsidy'
    # annual_budget = 4000
    # adoption_cap = 40
    # subsidy = 4000
    # telco_match_funding = 4000
    # service_obligation_capacity = 10

    # s3_expected_built_interventions = [
    #     ('distribution_{EACAM}{1}', 'fttp', 's3_outside_in_subsidy', 'market_based', 1837),
    #     ('distribution_{EACOM}{5}', 'fttp', 's3_outside_in_subsidy', 'subsidy_based', 2837)
    #     ]

    # #Total cost should be £1837
    # #fttp modem: £20 * 20 = £400
    # #optical network terminal: £10 * 20 = £200
    # #planning cost: £10 * 20 = £200
    # #optical connection point: £37 * 1 = £37 (32 premises per connection point)
    # #fibre upgrade cost: £5 * 200 = 1000

    # #Total cost should be 2837
    # #fttp modem: £20 * 20 = £400
    # #optical network terminal: £10 * 20 = £200
    # #planning cost: £10 * 20 = £200
    # #optical connection point: £37 * 1 = £37 (32 premises per connection point)
    # #fibre upgrade cost: £5 * 400 = 2000

    # #build interventions
    # s3_built_interventions = decide_interventions(
    #     system, year, technology, policy, annual_budget, adoption_cap,
    #     subsidy, telco_match_funding, service_obligation_capacity)

    # assert s3_built_interventions == s3_expected_built_interventions
