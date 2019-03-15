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
            'fttp': 1,
            'fttdp': 1,
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
            'fttp': '0',
            'fttdp': '0',
            'fttc': '0',
            'docsis3': '0',
            'adsl': '1',
            'name': 'cabinet_{EACAM}{P100}',
        }],
        'exchanges':[{
            'id': 'exchange_EACAM',
            'Name': 'Cambridge',
            'pcd': 'CB23ET',
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

    expected_coverage = {
        'ABABA':{
            'num_premises': 20,
            'num_fttp': 1,
            'num_fttdp': 1,
            'num_fttc': 5,
            'num_docsis3': 5,
            'num_adsl': 20
        }
    }

    expected_aggregate_coverage = [{
        'percentage_of_premises_with_fttp': 5.0,
        'percentage_of_premises_with_fttdp': 5.0,
        'percentage_of_premises_with_fttc': 25.0,
        'percentage_of_premises_with_docsis3': 25.0,
        'percentage_of_premises_with_adsl': 100.0,
        'sum_of_premises': 20
    }]

    expected_capacity = {
        'ABABA':{
                'average_capacity': 132.1,
        }
    }

    system = NetworkManager(assets, links, parameters)

    actual_coverage = system.coverage()

    assert expected_coverage == actual_coverage

    actual_aggregate_coverage = system.aggregate_coverage()

    assert expected_aggregate_coverage == actual_aggregate_coverage

    actual_capacity = system.capacity()

    assert expected_capacity == actual_capacity
