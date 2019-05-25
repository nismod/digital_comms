"""
Test Mobile Network interventions.py
11th May 2019
Written by Edward J. Oughton

"""
import pytest
from digital_comms.mobile_network.interventions import(
    decide_interventions,
    _area_satisfied,
    )
from digital_comms.mobile_network.model import (
    NetworkManager, PostcodeSector
    )

@pytest.fixture
def basic_system(setup_lad, setup_pcd_sector, setup_assets,
            setup_capacity_lookup,
            setup_clutter_lookup,
            setup_service_obligation_capacity,
            setup_traffic, setup_market_share, setup_mast_height):

    system = NetworkManager(setup_lad, setup_pcd_sector, setup_assets,
        setup_capacity_lookup, setup_clutter_lookup,
        setup_service_obligation_capacity,
        setup_traffic, setup_market_share, setup_mast_height)

    return system

def test_decide_interventions(basic_system, setup_traffic,
    setup_market_share):

    actual_result = decide_interventions(
        'minimal', 250000, 2,
        basic_system, 2020, 0.15, 0.25, 30
    )

    assert actual_result == ([], 250000)

    actual_result = decide_interventions(
        'upgrade-to-lte', 250000, 2,
        basic_system, 2020, 0.15, 0.25, 30
    )

    assert actual_result == ([], 250000)

    actual_result = decide_interventions(
        'macrocell-700-3500', 101834, 2,
        basic_system, 2020, 0.15, 0.25, 30
    )

    assert len(actual_result[0]) == 2
    assert actual_result[1] == 0

    actual_result = decide_interventions(
        'macrocell-700', 50917, 2,
        basic_system, 2020, 0.15, 0.25, 30
    )

    assert len(actual_result[0]) == 1
    assert actual_result[1] == 0

    actual_result = decide_interventions(
        'sectorisation', 303668, 100,
        basic_system, 2020, 0.5, 0.25, 30
    )

    assert len(actual_result[0]) == 6
    assert actual_result[1] == 0

    # actual_result = decide_interventions(
    #     'macro-densification', 450000, 100,
    #     basic_system, 2018, 0.5, 0.25, 30
    # )

    # assert len(actual_result[0]) == 3
    # assert actual_result[1] == 0

    # actual_result = decide_interventions(
    #     'macro-densification', 401834 , 10,
    #     basic_system, 2020, 0.5, 0.25, 30
    # )

    #build
    # site_100 CB11 carrier_700 50917
    # site_100 CB11 carrier_3500 50917
    # site_2 CB11 build_5G_macro_site 150000
    # site_3 CB11 build_5G_macro_site 150000

    # assert len(actual_result[0]) == 4
    # assert actual_result[1] == 0

    actual_result = decide_interventions(
        'deregulation', (101834+30000)*2 , 10,
        basic_system, 2020, 0.5, 0.25, 30
    )

    #build
    # site_100 CB11 carrier_700 50917
    # site_100 CB11 carrier_3500 50917
    # site_100 CB11 raise_mast_height 30000
    # site_100 CB12 carrier_700 50917
    # site_100 CB12 carrier_3500 50917
    # site_100 CB12 raise_mast_height 30000

    assert len(actual_result[0]) == 6
    assert actual_result[1] == 0


    actual_result = decide_interventions(
        'cloud-ran', (101834+30000)*2 , 10,
        basic_system, 2020, 0.5, 0.25, 30
    )

    #build
    # site_100 CB11 carrier_700 50917
    # site_100 CB11 carrier_3500 50917
    # site_100 CB11 deploy_c_ran 30000
    # site_100 CB12 carrier_700 50917
    # site_100 CB12 carrier_3500 50917
    # site_100 CB12 deploy_c_ran 30000

    # for row in actual_result[0]:
    #     print(row['site_ngr'],row['pcd_sector'],row['item'],row['cost'])

    assert len(actual_result[0]) == 6
    assert actual_result[1] == 0
