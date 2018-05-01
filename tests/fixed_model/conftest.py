import pytest
from pytest import fixture

import fiona
import os

from digital_comms.fixed_model.fixed_model import ICTManager

def read_shapefile(file):
    with fiona.open(file, 'r') as source:
        return [f['properties'] for f in source]

@pytest.fixture
def assets(rootdir):
    return {
        'premises': read_shapefile(os.path.join(rootdir, 'fixed_model', 'fixtures', 'assets_layer5_premises.shp')),
        'distributions': read_shapefile(os.path.join(rootdir, 'fixed_model', 'fixtures', 'assets_layer4_distributions.shp')),
        'cabinets': read_shapefile(os.path.join(rootdir, 'fixed_model', 'fixtures', 'assets_layer3_cabinets.shp')),
        'exchanges': read_shapefile(os.path.join(rootdir, 'fixed_model', 'fixtures', 'assets_layer2_exchanges.shp'))
    }

@pytest.fixture
def links(rootdir):
    links = []
    links.extend(read_shapefile(os.path.join(rootdir, 'fixed_model', 'fixtures', 'links_layer5_premises.shp')))
    links.extend(read_shapefile(os.path.join(rootdir, 'fixed_model', 'fixtures', 'links_layer4_distributions.shp')))
    links.extend(read_shapefile(os.path.join(rootdir, 'fixed_model', 'fixtures', 'links_layer3_cabinets.shp')))    
    return links

@pytest.fixture
def parameters():
    return {
        'costs': {
            'links': {
                'fiber': {
                    'meter': 5
                },
                'copper': {
                    'meter': 3
                }
            },
            'assets': {
                'exchange': {
                    'fttp': 50000,
                    'gfast': 40000,
                    'fttc': 30000,
                    'adsl': 20000
                },
                'cabinet': {
                    'fttp':{
                        '32_ports': 10
                    },
                    'gfast': 4000,
                    'fttc': 3000,
                    'adsl': 2000
                },
                'distribution': {
                    'fttp':  {
                        '32_ports': 10
                    },
                    'gfast': {
                        '4_ports': 1500
                    },
                    'fttc': 300,
                    'adsl': 200
                },
                'premise': {
                    'fttp': {
                        'modem': 20,
                        'optical_network_terminator': 10
                    },
                    'gfast': {
                        'modem': 20,
                    },
                    'fttc': {
                        'modem': 15,
                    },
                    'adsl': {
                        'modem': 10
                    }
                }
            }
        },
        'benefits': {
            'assets': {
                'premise': {
                    'fttp': 50,
                    'gfast': 40,
                    'fttc': 30,
                    'adsl': 20
                }
            }
        }
    }

@pytest.fixture
def setup_fixed_network(assets, links, parameters):
    return ICTManager(assets, links, parameters)