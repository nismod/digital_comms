#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, division

import pytest
from pytest import fixture
from shapely.geometry import Point, LineString

from digital_comms.fixed_model.network_structure import ICTManager

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
def setup_fixed_model_dps():
    return [

    ]

# @fixture(scope='function')
# def setup_fixed_model_pcp_to_dps():
#     return {
#         'cab_1':(,'geometry'),
#         'cab_2':(,'geometry'),
#         'cab_3':(,'geometry'),
#         'cab_4':(,'geometry'),
#         'cab_5':(,'geometry'),
#         'cab_6':(,'geometry'),
#         'cab_7':(,'geometry')
#     }

@fixture(scope='function')
def setup_fixed_model_pcp():
    return [
        ('cab_1', Point(52.02917, 0.13409)),
        ('cab_2', Point(53.02917, 0.23409)),
        ('cab_3', Point(54.02917, 0.33409)),
        ('cab_4', Point(55.02917, 0.43409)),
        ('cab_5', Point(56.02917, 0.53409)),
        ('cab_6', Point(57.02917, 0.63409)),
        ('cab_7', Point(58.02917, 0.73409))
    ]

@fixture(scope='function')
def setup_fixed_model_exchanges():
    return [
        ('EAARR', Point(52.02917, 0.13409)),
        ('EABTM', Point(52.12916, 0.14408))
    ]

@fixture(scope='function')
def setup_fixed_model_links():
    return [
        ('MSAN_T3', 'EAARR', 'PCP', 'cab_1', 'LineString'),
        ('MSAN_T3', 'EAARR', 'PCP', 'cab_2', 'geometry'),
        ('MSAN_T3', 'EAARR', 'PCP', 'cab_3', 'geometry'),
        ('MSAN_T3', 'EAARR', 'PCP', 'cab_4', 'geometry'),
        ('MSAN_T3', 'EABTM', 'PCP', 'cab_5', 'geometry'),
        ('MSAN_T3', 'EABTM', 'PCP', 'cab_6', 'geometry'),
        ('MSAN_T3', 'EABTM', 'PCP', 'cab_7', 'geometry')
    ]
@fixture(scope='function')
def setup_fixed_network(setup_fixed_model_pcp, setup_fixed_model_exchanges, setup_fixed_model_links):
    empty_data = {}

    return ICTManager(empty_data, empty_data, setup_fixed_model_pcp,
                      setup_fixed_model_exchanges, empty_data,
                      setup_fixed_model_links)



