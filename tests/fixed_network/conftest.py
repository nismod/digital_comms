import pytest
from pytest import fixture
import csv
import os

from digital_comms.fixed_network.model import NetworkManager
from digital_comms.fixed_network.interventions import decide_interventions

def read_csv(file):
    output = []
    with open(file, 'r') as source:
        reader = csv.DictReader(source)
        [dict(line) for line in source]

@pytest.fixture
def assets(rootdir):
    return {
        'distributions': read_csv(os.path.join(
            rootdir, 'fixed_network', 'fixtures', 'premises_by_distribution_point.csv')),
        'cabinets': read_csv(os.path.join(
            rootdir, 'fixed_network', 'fixtures', 'assets_layer3_cabinets.csv')),
        'exchanges': read_csv(os.path.join(
            rootdir, 'fixed_network', 'fixtures', 'assets_layer2_exchanges.csv'))
    }

@pytest.fixture
def links(rootdir):
    links = []
    links.extend(read_csv(os.path.join(
        rootdir, 'fixed_network', 'fixtures', 'links_premises_by_distribution_point.csv')))
    links.extend(read_csv(os.path.join(
        rootdir, 'fixed_network', 'fixtures', 'links_layer4_distributions.csv')))
    links.extend(read_csv(os.path.join(
        rootdir, 'fixed_network', 'fixtures', 'links_layer3_cabinets.csv')))
    return links

@pytest.fixture
def parameters():
    return {
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

@pytest.fixture
def setup_system(assets, links, parameters):
    return NetworkManager(assets, links, parameters)

@pytest.fixture
def setup_annual_adoption_rate():
    return 2

@pytest.fixture
def setup_update_adoption_desirability():
    return 2

@pytest.fixture
def setup_timestep():
    return 2019

@pytest.fixture
def setup_technology():
    return 'fttp'

@pytest.fixture
def setup_policy():
    return 'fttp_s1_market_based_roll_out'

@pytest.fixture
def setup_annual_budget():
    return 2500000

@pytest.fixture
def setup_adoption_cap():
    return 2500000

@pytest.fixture
def setup_subsidy():
    return 2500000

@pytest.fixture
def setup_telco_match_funding():
    return 2500000

@pytest.fixture
def setup_service_obligation_capacity():
    return 10

@pytest.fixture
def setup_interventions(assets, links, parameters):
    return
