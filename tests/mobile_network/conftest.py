#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, division

import pytest
from pytest import fixture
from shapely.geometry import Point, LineString
import os

from digital_comms.mobile_network.model import NetworkManager

@pytest.fixture
def rootdir():
    return os.path.dirname(os.path.abspath(__file__))

@fixture(scope='function')
def setup_lad():
    return [
        {
            "id": 1,
            "name": "Cambridge",
        }
    ]

@fixture(scope='function')
def setup_pcd_sector():
    return [
        {
            "id": "CB11",
            "lad_id": 1,
            "population": 500,
            "area": 2,
            "user_throughput": 2,
        },
        {
            "id": "CB12",
            "lad_id": 1,
            "population": 200,
            "area": 2,
            "user_throughput": 2,
        }
    ]

@fixture(scope='function')
def setup_assets():
    return [
        {
            "pcd_sector": "CB11",
            "site_ngr": "site_100",
            "technology": "LTE",
            "type": "macrocell_site",
            "frequency": ["800", "2600"],
            "bandwidth": "2x10MHz",
            "build_date": 2017,
            "sectors": 3,
        },
        {
            "pcd_sector": "CB12",
            "site_ngr": "site_200",
            "technology": "LTE",
            "type": "macrocell_site",
            "frequency": ["800", "2600"],
            "bandwidth": "2x10MHz",
            "build_date": 2017,
            "sectors": 3,
        }
    ]

@fixture(scope='function')
def setup_site_sectors():
    return 3

@fixture(scope='function')
def setup_capacity_lookup():
    return {
        ("Urban", "700", "2x10MHz"): [
            (0, 0),
            (1, 2),
        ],
        ("Urban", "800", "2x10MHz"): [
            (0, 0),
            (1, 2),
        ],
        ("Urban", "2600", "2x10MHz"): [
            (0, 0),
            (3, 5),
        ],
        ("Urban", "3500", "2x10MHz"): [
            (0, 0),
            (3, 5),
        ],
        ('Small cells', '3700', '2x25MHz'): [
            (0, 0),
            (3, 10),
        ],
        ("Rural", "700", "2x10MHz"): [
            (0, 0),
            (1, 2),
        ],
        ("Rural", "800", "2x10MHz"): [
            (0, 0),
            (1, 2),
        ],
        ("Rural", "2600", "2x10MHz"): [
            (0, 0),
            (3, 5),
        ],
        ("Rural", "3500", "2x10MHz"): [
            (0, 0),
            (3, 5),
        ],
    }

@fixture(scope='function')
def setup_clutter_lookup():
    return  [
        (0.0, 'Rural'),
        (782.0, 'Suburban'),
        (7959.0, 'Urban'),
    ]

@fixture(scope='function')
def setup_service_obligation_capacity():
    return 2

@fixture(scope='function')
def setup_traffic():
    return 0.15

@fixture(scope='function')
def setup_market_share():
    return 0.25

@fixture(scope='function')
def setup_built_interventions():
    return [
        {
            "pcd_sector": "CB11",
            "site_ngr": 100,
            "technology": "LTE",
            "type": "macrocell_site",
            "frequency": ["800"],
            "bandwidth": "2x10MHz",
            "build_date": 2017
        },
        {
            "pcd_sector": "CB12",
            "site_ngr": 200,
            "technology": "LTE",
            "type": "macrocell_site",
            "frequency": ["2600"],
            "bandwidth": "2x10MHz",
            "build_date": 2017
        }
    ]

@fixture(scope='function')
def setup_interventions():
    return {
    'upgrade_to_lte': {
        'name': 'Upgrade site to LTE',
        'description': 'If a site has only 2G/3G',
        'result': '800 and 2600 bands available',
        'cost': 142446,
        'assets_to_build': [
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '800',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                # set build date when deciding
                'build_date': None,
            },
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '2600',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'carrier_700': {
        'name': 'Build 700 MHz carrier',
        'description': 'Available if a site has LTE',
        'result': '700 band available',
        'cost': 50917,
        'assets_to_build': [
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '700',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'carrier_3500': {
        'name': 'Build 3500 MHz carrier',
        'description': 'Available if a site has LTE',
        'result': '3500 band available',
        'cost': 50917,
        'assets_to_build': [
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': '3500',
                'technology': 'LTE',
                'type': 'macrocell_site',
                'bandwidth': '2x10MHz',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'sectorisation': {
        'name': 'sectorisation carrier',
        'description': 'Available if a site has LTE',
        'result': '6 sectors are available',
        'cost': 50000, #£10k each, plus £20 installation
        'assets_to_build': [
            {
                # site_ngr to match upgraded
                'site_ngr': None,
                'frequency': 'x6_sectors',
                'technology': 'same',
                'type': 'macrocell_site',
                'bandwidth': 'same',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'build_macro_site': {
        'name': 'Build a new macro site',
        'description': 'Must be deployed at preset densities \
            to be modelled',
        'result': 'Macrocell sites available at given density',
        'cost': 150000,
        'assets_to_build': [
            {
                # site_ngr not used
                'site_ngr': 'new_macro_site',
                'frequency': 'same',
                'technology': 'same',
                'type': 'macro_site',
                'bandwidth': 'same',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'small_cell': {
        'name': 'Build a small cell',
        'description': 'Must be deployed at preset densities \
            to be modelled',
        'result': '2x25 MHz small cells available at given density',
        'cost': 40220,
        'assets_to_build': [
            {
                # site_ngr not used
                'site_ngr': 'small_cell_sites',
                'frequency': '3700',
                'technology': '5G',
                'type': 'small_cell',
                'bandwidth': '2x25MHz',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'raise_mast_height': {
        'name': 'Raises existing mast height',
        'description': 'Must be deployed at preset densities to \
            be modelled',
        'result': 'Same technology but with new enhanced capacity',
        'cost': 30000,
        'assets_to_build': [
            {
                # site_ngr not used
                'site_ngr': 'extended_height',
                'frequency': 'same',
                'technology': 'same',
                'type': 'extended_height_macro',
                'bandwidth': 'same',
                # set build date when deciding
                'build_date': None,
            },
        ]
    },
    'deploy_c_ran': {
        'name': 'Replace D-Ran with C-RAN',
        'description': 'Must be deployed within viable distance \
            from exchange',
        'result': 'Network architecture change to SDN/NFV',
        'cost': 30000,
        'assets_to_build': [
            {
                'site_ngr': 'c_ran',
                'frequency': 'same',
                'technology': '5G c_ran',
                'type': 'macro_c_ran',
                'bandwidth': 'same',
                'build_date': None,
            },
        ]
    },
}

@fixture(scope='function')
def setup_strategies():
    return {
    'minimal': (),
    'macrocell_700_3500': (
        'upgrade_to_lte', 'carrier_700', 'carrier_3500'
        ),
    'macrocell_700': ('upgrade_to_lte', 'carrier_700'),
    'sectorisation': (
        'upgrade_to_lte', 'carrier_700',
        'carrier_3500', 'x6_sectors'
        ),
    'macro_densification': ('build_macro_site'),
    'deregulation': ('raise_mast_height'),
    'cloud_ran': ('deploy_c_ran'),
    'small_cell': ('upgrade_to_lte', 'small_cell'),
    'small_cell_and_spectrum': (
        'upgrade_to_lte', 'carrier_700',
        'carrier_3500', 'small_cell'
        ),
    }






@fixture(scope='function')
def setup_fixed_model_pcp():
    return [
        ((-1.944580, 52.792175), {'Name': 'cab_1', 'Type': 'pcp'}),
        ((-0.395508, 52.485498), {'Name': 'cab_2', 'Type': 'pcp'}),
        ((-2.713623, 52.652437), {'Name': 'cab_3', 'Type': 'pcp'}),
        (( 0.417480, 51.147694), {'Name': 'cab_4', 'Type': 'pcp'}),
        (( 1.219482, 52.431944), {'Name': 'cab_5', 'Type': 'pcp'}),
        ((-1.900635, 51.223443), {'Name': 'cab_6', 'Type': 'pcp'}),
        (( 0.802002, 51.154586), {'Name': 'cab_7', 'Type': 'pcp'})
    ]

@fixture(scope='function')
def setup_fixed_model_exchanges():
    return [
        ((-0.572275, 51.704581), {'Name': 'EAARR', 'Type': 'exchange'}),
        (( 0.537344, 51.745323), {'Name': 'EABTM', 'Type': 'exchange'})
    ]

@fixture(scope='function')
def setup_fixed_model_corenodes():
    return [
        ((0.3, 51.825323), {'Name': 'CoreNode', 'Type': 'core'})
    ]

@fixture(scope='function')
def setup_fixed_model_links():
    return [
        ([(-0.572275, 51.704581), (0, 52), (-1.944580, 52.792175)], {'Origin': 'EAARR',    'Dest': 'cab_1', 'Type': 'link', 'Physical': 'fiberglass'}),
        ([(-0.572275, 51.704581), (0, 52), (-0.395508, 52.485498)], {'Origin': 'EAARR',    'Dest': 'cab_2', 'Type': 'link', 'Physical': 'fiberglass'}),
        ([(-0.572275, 51.704581), (0, 52), (-2.713623, 52.652437)], {'Origin': 'EAARR',    'Dest': 'cab_3', 'Type': 'link', 'Physical': 'fiberglass'}),
        ([(-0.572275, 51.704581), (0, 52), ( 0.417480, 51.147694)], {'Origin': 'EAARR',    'Dest': 'cab_4', 'Type': 'link', 'Physical': 'fiberglass'}),
        ([( 0.537344, 51.745323), (0, 52), ( 1.219482, 52.431944)], {'Origin': 'EABTM',    'Dest': 'cab_5', 'Type': 'link', 'Physical': 'copper'    }),
        ([( 0.537344, 51.745323), (0, 52), (-1.900635, 51.223443)], {'Origin': 'EABTM',    'Dest': 'cab_6', 'Type': 'link', 'Physical': 'copper'    }),
        ([( 0.537344, 51.745323), (0, 52), ( 0.802002, 51.154586)], {'Origin': 'EABTM',    'Dest': 'cab_7', 'Type': 'link', 'Physical': 'copper'    }),
        ([( 0.3,      51.825323), (0, 51), (-0.572275, 51.704581)], {'Origin': 'CoreNode', 'Dest': 'EAARR', 'Type': 'link', 'Physical': 'copper'    }),
        ([( 0.3,      51.825323), (0, 51), ( 0.537344, 51.745323)], {'Origin': 'CoreNode', 'Dest': 'EABTM', 'Type': 'link', 'Physical': 'copper'    })
    ]

@fixture(scope='function')
def setup_fixed_network(setup_fixed_model_pcp, setup_fixed_model_exchanges, setup_fixed_model_links):
    empty_data = {}

    return NetworkManager(empty_data, empty_data, setup_fixed_model_pcp,
                      setup_fixed_model_exchanges, empty_data,
                      setup_fixed_model_links)
