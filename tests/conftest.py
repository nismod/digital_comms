#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import, division

import pytest
from pytest import fixture

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