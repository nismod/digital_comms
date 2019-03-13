import pytest
import os

from digital_comms.fixed_network.model import NetworkManager
from digital_comms.fixed_network.adoption import update_adoption_desirability
from digital_comms.fixed_network.interventions import decide_interventions

class TestNetworkManager():

    def test_create(self, assets, links, parameters):

        NetworkManager(assets, links, parameters)


def test_init(setup_system, assets):

<<<<<<< HEAD
    assert len([d for d in assets['distributions']]) == len([
        dist for dist in setup_system['distributions']])
=======
    print(len(setup_system._distributions))

    assert len(assets['distributions']) == len(setup_system._distributions)
>>>>>>> 78ff86f5286aa16e1758c7ae1151754de256356a
    assert len(assets['cabinets']) == len(setup_system.assets['cabinets'])
    assert len(assets['exchanges']) == len(setup_system.assets['exchanges'])

# def test_update_adoption_desirability(setup_system, setup_annual_adoption_rate):

#     assert


# def test_decide_interventions(setup_system, setup_timestep, setup_technology,
#     setup_policy, setup_annual_budget, setup_adoption_cap, setup_subsidy,
#     setup_telco_match_funding, setup_service_obligation_capacity):

#     assert





# if __name__ == '__main__':

#     ASSETS = {
#         'premises':[{
#             'id': 'osgb5000005186077869',
#             'lad': '1.84163492526694',
#             'wta': '0.7322',
#             'wtp': '20',
#             'postcode': 'VCB00078',
#             'CAB_ID': '{EACAM}{P100}',
#             'connection': 'distribution_{EACAM}{795}',
#             'FTTP': '0',
#             'GFast': '0',
#             'FTTC': '0',
#             'DOCSIS3': '0',
#             'ADSL': '1',
#         }],
#         'distributions':[{
#             'id': 'distribution_{EACAM}{795}',
#             'connection': 'cabinet_{EACAM}{P100}',
#             'FTTP': '0',
#             'GFast': '0',
#             'FTTC': '0',
#             'DOCSIS3': '0',
#             'ADSL': '1',
#             'name': 'distribution_{EACAM}{795}',
#         }],
#         'cabinets':[{
#             'id': 'cabinet_{EACAM}{P100}',
#             'connection': 'exchange_EACAM',
#             'FTTP': '0',
#             'GFast': '0',
#             'FTTC': '0',
#             'DOCSIS3': '0',
#             'ADSL': '1',
#             'name': 'cabinet_{EACAM}{P100}',
#         }],
#         'exchanges':[{
#             'id': 'exchange_EACAM',
#             'Name': 'Cambridge',
#             'pcd': 'CB23ET',
#             'Region': 'East',
#             'County': 'Cambridgeshire',
#             'FTTP': '0',
#             'GFast': '0',
#             'FTTC': '0',
#             'DOCSIS3': '0',
#             'ADSL': '1',
#         }]
#     }

#     LINKS = [
#         {
#         'origin': 'osgb5000005186077869',
#         'dest': 'distribution_{EACAM}{795}',
#         'length': '20',
#         'technology': 'copper'
#         },
#         {
#         'origin': 'distribution_{EACAM}{795}',
#         'dest': 'cabinet_{EACAM}{P100}',
#         'length': '94',
#         'technology': 'copper'
#         },
#         {
#         'origin': 'cabinet_{EACAM}{P100}',
#         'dest': 'exchange_EACAM',
#         'length': '1297',
#         'technology': 'fiber'
#         },
#     ]

#     PARAMETERS = {
#         'costs_links_fibre_meter': 5,
#         'costs_links_copper_meter': 3,
#         'costs_assets_exchange_fttp': 50000,
#         'costs_assets_exchange_gfast': 40000,
#         'costs_assets_exchange_fttc': 30000,
#         'costs_assets_exchange_adsl': 20000,
#         'costs_assets_cabinet_fttp_32_ports': 10,
#         'costs_assets_cabinet_gfast': 4000,
#         'costs_assets_cabinet_fttc': 3000,
#         'costs_assets_cabinet_adsl': 2000,
#         'costs_assets_distribution_fttp_32_ports': 10,
#         'costs_assets_distribution_gfast_4_ports': 1500,
#         'costs_assets_distribution_fttc': 300,
#         'costs_assets_distribution_adsl': 200,
#         'costs_assets_premise_fttp_modem': 20,
#         'costs_assets_premise_fttp_optical_network_terminator': 10,
#         'costs_assets_premise_gfast_modem': 20,
#         'costs_assets_premise_fttc_modem': 15,
#         'costs_assets_premise_adsl_modem': 10,
#         'benefits_assets_premise_fttp': 50,
#         'benefits_assets_premise_gfast': 40,
#         'benefits_assets_premise_fttc': 30,
#         'benefits_assets_premise_adsl': 20,
#         'planning_administration_cost': 200,
#         'costs_assets_premise_fttdp_modem': 37,
#     }

#     system = NetworkManager(ASSETS, LINKS, PARAMETERS)
