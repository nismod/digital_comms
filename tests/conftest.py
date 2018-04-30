#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, division

import pytest
from pytest import fixture
from shapely.geometry import Point, LineString

from digital_comms.fixed_model.fixed_model import ICTManager

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
            "user_throughput": 2
        },
        {
            "id": "CB12",
            "lad_id": 1,
            "population": 200,
            "area": 2,
            "user_throughput": 2
        }
    ]

@fixture(scope='function')
def setup_assets():
    return [
        {
            "pcd_sector": "CB11",
            "site_ngr": 100,
            "technology": "LTE",
            "type": "macrocell_site",
            "frequency": "800",
            "bandwidth": "2x10MHz",
            "build_date": 2017
        },
        {
            "pcd_sector": "CB12",
            "site_ngr": 200,
            "technology": "LTE",
            "type": "macrocell_site",
            "frequency": "2600",
            "bandwidth": "2x10MHz",
            "build_date": 2017
        }
    ]

@fixture(scope='function')
def setup_capacity_lookup():
    return {
        ("Urban", "700", "2x10MHz"): [
            (0, 1),
            (1, 2),
        ],
        ("Urban", "800", "2x10MHz"): [
            (0, 1),
            (1, 2),
        ],
        ("Urban", "2600", "2x10MHz"): [
            (0, 3),
            (3, 5),
        ],
        ("Urban", "3500", "2x10MHz"): [
            (0, 3),
            (3, 5),
        ],
        ('Small cells', '3700', '2x25MHz'): [
            (0, 3),
            (3, 5),
        ]
    }

@fixture(scope='function')
def setup_clutter_lookup():
    return [
        (5, "Urban")
    ]

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

    return ICTManager(empty_data, empty_data, setup_fixed_model_pcp,
                      setup_fixed_model_exchanges, empty_data,
                      setup_fixed_model_links)
