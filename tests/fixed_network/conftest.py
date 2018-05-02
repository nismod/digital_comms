import pytest
from pytest import fixture

import fiona
import os

from digital_comms.fixed_network.model import ICTManager

def read_shapefile(file):
    with fiona.open(file, 'r') as source:
        return [f['properties'] for f in source]

@pytest.fixture
def assets(rootdir):
    return {
        'premises': read_shapefile(os.path.join(rootdir, 'fixed_network', 'fixtures', 'assets_layer5_premises.shp')),
        'distributions': read_shapefile(os.path.join(rootdir, 'fixed_network', 'fixtures', 'assets_layer4_distributions.shp')),
        'cabinets': read_shapefile(os.path.join(rootdir, 'fixed_network', 'fixtures', 'assets_layer3_cabinets.shp')),
        'exchanges': read_shapefile(os.path.join(rootdir, 'fixed_network', 'fixtures', 'assets_layer2_exchanges.shp'))
    }

@pytest.fixture
def links(rootdir):
    links = []
    links.extend(read_shapefile(os.path.join(rootdir, 'fixed_network', 'fixtures', 'links_layer5_premises.shp')))
    links.extend(read_shapefile(os.path.join(rootdir, 'fixed_network', 'fixtures', 'links_layer4_distributions.shp')))
    links.extend(read_shapefile(os.path.join(rootdir, 'fixed_network', 'fixtures', 'links_layer3_cabinets.shp')))    
    return links

@pytest.fixture
def parameters():
    return {
        'costs_links_fiber_meter': 5,
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
        'benefits_assets_premise_adsl': 20
    }

@pytest.fixture
def setup_fixed_network(assets, links, parameters):
    return ICTManager(assets, links, parameters)