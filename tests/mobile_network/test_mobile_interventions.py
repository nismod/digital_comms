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


@pytest.fixture
def non_4g_system(setup_lad, setup_pcd_sector, setup_non_4g_assets,
    setup_capacity_lookup, setup_clutter_lookup,
    setup_service_obligation_capacity, setup_traffic, setup_market_share,
    setup_mast_height):

    system = NetworkManager(setup_lad, setup_pcd_sector, setup_non_4g_assets,
        setup_capacity_lookup, setup_clutter_lookup,
        setup_service_obligation_capacity,
        setup_traffic, setup_market_share, setup_mast_height)

    return system


@pytest.fixture
def mixed_system(setup_lad, setup_pcd_sector, setup_mixed_assets,
    setup_capacity_lookup, setup_clutter_lookup,
    setup_service_obligation_capacity, setup_traffic, setup_market_share,
    setup_mast_height):

    system = NetworkManager(setup_lad, setup_pcd_sector, setup_mixed_assets,
        setup_capacity_lookup, setup_clutter_lookup,
        setup_service_obligation_capacity,
        setup_traffic, setup_market_share, setup_mast_height)

    return system


def test_decide_interventions(non_4g_system, basic_system,
    mixed_system, setup_traffic, setup_market_share):

    actual_result = decide_interventions(
        'minimal', 250000, 0,
        mixed_system, 2020, 0.15, 0.25, 30
    )

    assert actual_result == ([], 250000)

    actual_result = decide_interventions(
        'upgrade-to-lte', 284892, 2,
        non_4g_system, 2020, 0.15, 0.25, 30
    )

    assert len(actual_result[0]) == 2
    assert actual_result[1] == 0

    actual_result = decide_interventions(
        'upgrade-to-lte', 250000, 2,
        mixed_system, 2020, 0.15, 0.25, 30
    )

    assert actual_result == ([], 250000)


    actual_result = decide_interventions(
        'macrocell-700-3500', 101834, 2,
        mixed_system, 2020, 0.15, 0.25, 30
    )

    assert len(actual_result[0]) == 2
    assert actual_result[1] == 0

    actual_result = decide_interventions(
        'macrocell-700', 50917, 2,
        mixed_system, 2020, 0.15, 0.25, 30
    )

    assert len(actual_result[0]) == 1
    assert actual_result[1] == 0

    actual_result = decide_interventions(
        'sectorisation', 303668, 100,
        mixed_system, 2020, 0.5, 0.25, 30
    )

    assert len(actual_result[0]) == 6
    assert actual_result[1] == 0

    actual_result = decide_interventions(
        'macro-densification', 300000, 100,
        basic_system, 2018, 0.5, 0.25, 30
    )

    assert len(actual_result[0]) == 2
    assert actual_result[1] == 0

    actual_result = decide_interventions(
        'macro-densification', (101834+150000)*2 , 10,
        basic_system, 2020, 0.5, 0.25, 30
    )

    # build
    # site_100 CB11 carrier_700 50917
    # site_100 CB11 carrier_3500 50917
    # site_101 CB11 build_5G_macro_site 150000
    # site_200 CB12 carrier_700 50917
    # site_200 CB12 carrier_3500 50917
    # site_201 CB12 build_5G_macro_site 150000

    assert len(actual_result[0]) == 6
    assert actual_result[1] == 0

    actual_result = decide_interventions(
        'deregulation', (101834+30000)*2 , 10,
        mixed_system, 2020, 0.5, 0.25, 30
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
        mixed_system, 2020, 0.5, 0.25, 30
    )

    #build
    # site_100 CB11 carrier_700 50917
    # site_100 CB11 carrier_3500 50917
    # site_100 CB11 deploy_c_ran 30000
    # site_100 CB12 carrier_700 50917
    # site_100 CB12 carrier_3500 50917
    # site_100 CB12 deploy_c_ran 30000

    assert len(actual_result[0]) == 6
    assert actual_result[1] == 0

    actual_result = decide_interventions(
        'small-cell-and-spectrum', 203668 , 1000,
        mixed_system, 2020, 0.5, 0.25, 30
    )






    # won't build in these areas because they are rural

    # #build
    # # site_100 CB11 50917
    # # site_100 CB11 50917
    # # site_200 CB12 50917
    # # site_200 CB12 50917
    # # avoids building small cells in rural areas
    # assert len(actual_result[0]) == 4
    # assert actual_result[1] == 0

    # actual_result = decide_interventions(
    # 'small-cell-and-spectrum', 239668, 1000,
    # mixed_system, 2020, 0.5, 0.25, 30
    # )

    # #build
    # # site_100 CB11 50917
    # # site_100 CB11 50917
    # # small_cell_site2 CB11 12000
    # # small_cell_site? CB11 12000
    # # small_cell_site? CB11 12000
    # # site_200 CB12 50917
    # # site_200 CB12 50917

    # #budget ran out after building 7 assets
    # assert len(actual_result[0]) == 7
    # assert actual_result[1] == 0

    # actual_result = decide_interventions(
    # 'small-cell-and-spectrum', 251668 , 10,
    # mixed_system, 2020, 0.5, 0.25, 30
    # )

    # #build
    # # site_100 CB11 50917
    # # site_100 CB11 50917
    # # small_cell_site1 CB11 12000
    # # small_cell_site2 CB11 12000
    # # small_cell_site3 CB11 12000
    # # small_cell_site4 CB11 12000
    # # site_200 CB12 50917
    # # site_200 CB12 50917

    # #service obligation capacity met
    # assert len(actual_result[0]) == 8
    # assert actual_result[1] == 0
