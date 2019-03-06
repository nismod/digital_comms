import pytest
import os

from digital_comms.fixed_network.model import NetworkManager

def test_init(setup_fixed_network, assets, links):

    assert len(assets['premises']) == len(setup_fixed_network.assets['premises'])
    assert len(assets['distributions']) == len(setup_fixed_network.assets['distributions'])
    assert len(assets['cabinets']) == len(setup_fixed_network.assets['cabinets'])
    assert len(assets['exchanges']) == len(setup_fixed_network.assets['exchanges'])


if __name__ == '__main__':

    ASSETS = {
        'premises':[{
            'id': 'osgb5000005186077869',
            'lad': '1.84163492526694',
            'wta': '0.7322',
            'wtp': '20',
            'postcode': 'VCB00078',
            'CAB_ID': '{EACAM}{P100}',
            'connection': 'distribution_{EACAM}{795}',
            'FTTP': '0',
            'GFast': '0',
            'FTTC': '0',
            'DOCSIS3': '0',
            'ADSL': '1',
        }],
        'distributions':[{
            'id': 'distribution_{EACAM}{795}',
            'connection': 'cabinet_{EACAM}{P100}',
            'FTTP': '0',
            'GFast': '0',
            'FTTC': '0',
            'DOCSIS3': '0',
            'ADSL': '1',
            'name': 'distribution_{EACAM}{795}',
        }],
        'cabinets':[{
            'id': 'cabinet_{EACAM}{P100}',
            'connection': 'exchange_EACAM',
            'FTTP': '0',
            'GFast': '0',
            'FTTC': '0',
            'DOCSIS3': '0',
            'ADSL': '1',
            'name': 'cabinet_{EACAM}{P100}',
        }],
        'exchanges':[{
            'id': 'exchange_EACAM',
            'Name': 'Cambridge',
            'pcd': 'CB23ET',
            'Region': 'East',
            'County': 'Cambridgeshire',
            'FTTP': '0',
            'GFast': '0',
            'FTTC': '0',
            'DOCSIS3': '0',
            'ADSL': '1',
        }]
    }

    LINKS = [
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

    PARAMETERS = {
        'costs_links_fibre_meter': 5,
        'costs_links_copper_meter': 3,
        'costs_assets_exchange_fttp': 50000,
        'costs_assets_exchange_gfast': 40000,
        'costs_assets_exchange_fttc': 30000,
        'costs_assets_exchange_adsl': 20000,
        'costs_assets_cabinet_fttp_32_ports': 10,
        'costs_assets_cabinet_gfast': 4000,
        'costs_assets_cabinet_fttc': 3000,
        'costs_assets_cabinet_adsl': 2000,
        'costs_assets_distribution_fttp_32_ports': 10,
        'costs_assets_distribution_gfast_4_ports': 1500,
        'costs_assets_distribution_fttc': 300,
        'costs_assets_distribution_adsl': 200,
        'costs_assets_premise_fttp_modem': 20,
        'costs_assets_premise_fttp_optical_network_terminator': 10,
        'costs_assets_premise_gfast_modem': 20,
        'costs_assets_premise_fttc_modem': 15,
        'costs_assets_premise_adsl_modem': 10,
        'benefits_assets_premise_fttp': 50,
        'benefits_assets_premise_gfast': 40,
        'benefits_assets_premise_fttc': 30,
        'benefits_assets_premise_adsl': 20,
        'planning_administration_cost': 200,
        'costs_assets_premise_fttdp_modem': 37,
    }

    system = NetworkManager(ASSETS, LINKS, PARAMETERS)
