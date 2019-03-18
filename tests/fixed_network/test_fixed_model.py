import pytest
import os

from digital_comms.fixed_network.model import NetworkManager
from digital_comms.fixed_network.adoption import update_adoption_desirability
from digital_comms.fixed_network.interventions import decide_interventions

class TestNetworkManager():

    def test_create(self, assets, links, parameters):

        NetworkManager(assets, links, parameters)


def test_init(setup_system, assets):
    """Check the number of assets we load in is correct
    """
    assert len(assets['distributions']) == len(setup_system.assets['distributions'])
    assert len(assets['cabinets']) == len(setup_system.assets['cabinets'])
    assert len(assets['exchanges']) == len(setup_system.assets['exchanges'])

def test_init_from_data():

    # setup phase
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
        'costs_assets_upgrade_cabinet_fttp': 50,
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
    }

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

    expected_aggregate_coverage = [{
        'percentage_of_premises_with_fttp': 0.0,
        'percentage_of_premises_with_fttdp': 0.0,
        'percentage_of_premises_with_fttc': 25.0,
        'percentage_of_premises_with_docsis3': 25.0,
        'percentage_of_premises_with_adsl': 100.0,
        'sum_of_premises': 20
    }]

    expected_capacity = {
        'ABABA':{
            #  fttp       fttdp     fttc     docsis3   adsl
            # ((0*1000) + (0*300) + (5*80) + (5*150) + (10*24)) / 20 == 69.5
            'average_capacity': 69.5,
        }
    }

    system = NetworkManager(assets, links, parameters)

    actual_coverage = system.coverage()

    assert expected_coverage == actual_coverage

    actual_aggregate_coverage = system.aggregate_coverage()

    assert expected_aggregate_coverage == actual_aggregate_coverage

    actual_capacity = system.capacity()

    assert expected_capacity == actual_capacity

    #get actual costs
    actual_total_costs = system.get_total_upgrade_costs_by_distribution_point('fttp')

    #### dist_point to premises = £1837.0 ###
    #costs_assets_premise_fttp_modem: 20 * 20 = 400
    #costs_assets_premise_fttp_optical_network_terminator = 10 * 20 = 200
    #planning administation code = £10 * 20 = £200
    #costs_assets_premise_fttp_optical_connection_point: 37 * 1 = 37
    #fibre = £5 * 200 = £1000

    #### cabinet to dist_point = £520.0 ###
    #fibre = £5 * 94 = £470
    #costs_assets_upgrade_cabinet_fttp = £50

    #### exchange to cabinet = £50000 ###
    #costs_assets_upgrade_exchange_fttp = £50000

    expected_total_costs = (1837.0, 520.0, 50000.0)

    assert actual_total_costs['distribution_{EACAM}{795}'] == expected_total_costs

    #get actual costs
    actual_total_costs = system.get_total_upgrade_costs_by_distribution_point('fttdp')

    #### dist_point to premises = £1150.0 ###
    #'costs_assets_premise_fttdp_modem': 20 * 20 = 400,
    #'costs_assets_distribution_fttdp_8_ports': 250 * 3 = £750,

    #### cabinet to dist_point = £2970.0 ###
    #fibre = £5 * 94 = £470,
    #'costs_assets_cabinet_fttdp': 2500,

    #### exchange to cabinet = 25000.0 ###
    #'costs_assets_exchange_fttdp': 40000,

    expected_total_costs = (1150.0, 2970.0, 25000.0)

    assert actual_total_costs['distribution_{EACAM}{795}'] == expected_total_costs
