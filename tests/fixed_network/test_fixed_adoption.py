"""Skeleton test
"""
from digital_comms.fixed_network.model import NetworkManager
from digital_comms.fixed_network.adoption import update_adoption_desirability


def test_init_from_data():
    """ update_adoption_desirability takes the system and annual adoption rate,
    returning a list of tuples, with each tuple consisting of:
    - distribution.id, distribution.adoption_desirability

    To test:
        Give function test data which contains:
        - 5 distribution points
        - 100 premises

    """

    # setup phase
    assets = {
        'distributions':[{
            'id': 'distribution_{EACAM}{1}',
            'lad': 'E07000008',
            'connection': 'cabinet_{EACAM}{P100}',
            'fttp': 1,
            'fttdp': 1,
            'fttc': 5,
            'docsis3': 5,
            'adsl': 20,
            'total_prems': 20,
            'wta': 0.4,
            'wtp': 200,
            'name': 'distribution_{EACAM}{1}',
            'adoption_desirability': True
        },
        {
            'id': 'distribution_{EACAM}{2}',
            'lad': 'E07000008',
            'connection': 'cabinet_{EACAM}{P100}',
            'fttp': 1,
            'fttdp': 1,
            'fttc': 5,
            'docsis3': 5,
            'adsl': 20,
            'total_prems': 20,
            'wta': 1.0,
            'wtp': 200,
            'name': 'distribution_{EACAM}{2}',
            'adoption_desirability': True
        },
        {
            'id': 'distribution_{EACAM}{3}',
            'lad': 'E07000008',
            'connection': 'cabinet_{EACAM}{P100}',
            'fttp': 1,
            'fttdp': 1,
            'fttc': 5,
            'docsis3': 5,
            'adsl': 20,
            'total_prems': 20,
            'wta': 1.5,
            'wtp': 200,
            'name': 'distribution_{EACAM}{3}',
            'adoption_desirability': True
        },
        {
            'id': 'distribution_{EACOM}{4}',
            'lad': 'E07000012',
            'connection': 'cabinet_{EACOM}{P200}',
            'fttp': 1,
            'fttdp': 1,
            'fttc': 5,
            'docsis3': 5,
            'adsl': 20,
            'total_prems': 20,
            'wta': 0.3,
            'wtp': 200,
            'name': 'distribution_{EACOM}{4}',
            'adoption_desirability': True
        },
        {
            'id': 'distribution_{EACOM}{5}',
            'lad': 'E07000012',
            'connection': 'cabinet_{EACOM}{P200}',
            'fttp': 1,
            'fttdp': 1,
            'fttc': 5,
            'docsis3': 5,
            'adsl': 20,
            'total_prems': 20,
            'wta': 0.2,
            'wtp': 200,
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
        'origin': 'osgb5000005186077869',
        'dest': 'distribution_{EACAM}{795}',
        'length': '20',
        'technology': 'copper'
        },
        {
        'origin': 'distribution_{EACAM}{795}',
        'dest': 'cabinet_{EACAM}{P100}',
        'length': '94',
        'technology': 'copper'
        },
        {
        'origin': 'cabinet_{EACAM}{P100}',
        'dest': 'exchange_EACAM',
        'length': '1297',
        'technology': 'fiber'
        },
    ]

    parameters = {
        'costs_links_fibre_meter': 5,
        'costs_links_copper_meter': 3,
        'costs_assets_exchange_fttp': 50000,
        'costs_assets_exchange_fttdp': 40000,
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

    expected_adoption_year_1 = [
        ('distribution_{EACAM}{3}', True),
        ('distribution_{EACAM}{2}', True),
        ]

    expected_adoption_year_2 = [
        ('distribution_{EACAM}{1}', True)
        ]

    expected_adoption_year_3 = []

    expected_adoption_year_4 = [
        ('distribution_{EACOM}{4}', True)
        ]

    system = NetworkManager(assets, links, parameters)

    #Expected overall distribution ranking based on wta (willingness to adopt)
    #'distribution_{EACAM}{3}' = 1.5
    #'distribution_{EACAM}{2}' = 1
    #'distribution_{EACAM}{1}' = 0.4
    #'distribution_{EACOM}{4}' = 0.3
    #'distribution_{EACOM}{5}' = 0.2

    actual_adoption_year_1 = update_adoption_desirability(system, 40)

    #actual_adoption_year_1 = [
    #('distribution_{EACAM}{3}', True), ('distribution_{EACAM}{2}', True)
    #]

    assert actual_adoption_year_1 == expected_adoption_year_1

    actual_adoption_year_2 = update_adoption_desirability(system, 60)

    #actual_adoption_year_2 = [
    #('distribution_{EACAM}{2}', True)
    #]

    assert actual_adoption_year_2 == expected_adoption_year_2

    actual_adoption_year_3 = update_adoption_desirability(system, 70)

    assert actual_adoption_year_3 == expected_adoption_year_3

    actual_adoption_year_3 = update_adoption_desirability(system, 70)

    #actual_adoption_year_3 = []

    assert actual_adoption_year_3 == expected_adoption_year_3

    actual_adoption_year_4 = update_adoption_desirability(system, 80)

    #actual_adoption_year_4 = [
    #('distribution_{EACOM}{4}', True)
    #]

    assert actual_adoption_year_4 == expected_adoption_year_4
