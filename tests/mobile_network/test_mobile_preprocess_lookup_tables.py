"""
Test for scripts/mobile_preprocess_lookup_tables.py.

Written by Edward Oughton, 8th April 2019.

"""
import pytest
import os

from scripts.mobile_preprocess_lookup_tables import (
    get_postcode_sectors,
    get_local_authority_district,
    read_building_polygons,
    calculate_indoor_outdoor_ratio,
    get_geotype_information,
)

@pytest.fixture
def postcode_sector():
    yield {
        'type': "Feature",
        'geometry': {
            "type": "Polygon",
            "coordinates": [[(10, 1),(20, 2),(30, 3),(40, 1)]],
        },
        'properties': {}
    }

@pytest.fixture
def buildings():
    yield [
    {
        'type': "Feature",
        'geometry': {
            "type": "Polygon",
            "coordinates": [[(1, 1),(2, 2),(3, 3),(4, 1)]],
        },
        'properties': {
            'floor_area': 10,
            'footprint_area': 5,
            'res_count': 10,
            }
    },
    {
        'type': "Feature",
        'geometry': {
            "type": "Polygon",
            "coordinates": [[(1, 1),(2, 2),(3, 3),(4, 1)]],
        },
        'properties': {
            'floor_area': 5,
            'footprint_area': 2.5,
            'res_count': 10,
            }
    },
    ]

def test_calculate_indoor_outdoor_ratio(postcode_sector, buildings):

    actual_result = calculate_indoor_outdoor_ratio(postcode_sector, buildings)

    #building_footprint
    #7.5 = 5 + 2.5
    #total_inside_floor_area
    #15 = 10 = 5
    #total_outside_area  = postcode_sector_area - building_footprint
    #22.5 = 30 - 7.5
    #total_usage_area = total_outside_area + total_inside_floor_area
    #37.5 = 22.5 + 15
    #indoor probability
    #40 = (15/37.5)*100
    #outdoor probability
    #60 = (22.5/37.5)*100

    expected_indoor_outdoor_result = (40, 60)

    assert actual_result == expected_indoor_outdoor_result

def test_get_geotype_information(postcode_sector, buildings):

    actual_residential_count, actual_non_residential_count, \
        actual_area = get_geotype_information(
        postcode_sector, buildings
        )
    print(actual_residential_count, actual_non_residential_count, actual_area)
    # sum of res_count
    # 20 = 10 + 10
    expected_residential_count = 20

    expected_non_residential_count = 0

    # sum of postcode_sector area = 30 m^2/1000000
    expected_area = (30/1000000)

    assert actual_residential_count == expected_residential_count
    assert actual_non_residential_count == expected_non_residential_count
    assert actual_area == expected_area
