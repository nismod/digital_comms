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
            setup_site_sectors, setup_capacity_lookup,
            setup_clutter_lookup,
            setup_service_obligation_capacity,
            setup_traffic, setup_market_share):

    system = NetworkManager(setup_lad, setup_pcd_sector, setup_assets,
        setup_site_sectors, setup_capacity_lookup, setup_clutter_lookup,
        setup_service_obligation_capacity,
        setup_traffic, setup_market_share)

    return system

def test_decide_interventions(basic_system, setup_traffic,
    setup_market_share):

    # #test strategy minimal
    # actual_result = decide_interventions(
    #     'minimal', 250000, 2,
    #     basic_system, 2020, 3, 0.15, 0.25
    # )[2]

    # assert actual_result == []

    # #test strategy 'upgrade_to_lte'
    # actual_result = decide_interventions(
    #     'upgrade_to_lte', 250000, 2,
    #     basic_system, 2020, 3, 0.15, 0.25
    # )[2]

    # assert actual_result == []

    # #test strategy 'upgrade_to_lte'
    # actual_result = decide_interventions(
    #     'macrocell_700_3500', 101834, 2,
    #     basic_system, 2020, 3, 0.15, 0.25
    # )[2]

    # expected_result = [
    #     ('CB11', 1, 'carrier_700', 50917),
    #     ('CB11', 1, 'carrier_3500', 50917)
    # ]

    # #test strategy 'macrocell_700'
    # actual_result = decide_interventions(
    #     'macrocell_700', 50917, 2,
    #     basic_system, 2020, 3, 0.15, 0.25
    # )[2]

    # expected_result = [
    #     ('CB11', 1, 'carrier_700', 50917)
    # ]

    #test strategy 'sectorisation'
    actual_result = decide_interventions(
        'sectorisation', 1000000, 1000,
        basic_system, 2020, 3, 0.15, 0.25
    )#[2]

    # expected_result = [
    #     ('CB11', 1, 'carrier_700', 50917),
    #     ('CB11', 1, 'carrier_3500', 50917),
    #     ('CB12', 1, 'carrier_700', 50917),
    #     ('CB12', 1, 'carrier_3500', 50917),
    #     ('CB11', 1, 'carrier_700', 50917),
    #     ('CB11', 1, 'carrier_3500', 50917),
    #     ('CB12', 1, 'carrier_700', 50917),
    #     ('CB12', 1, 'carrier_3500', 50917),
    # ]

    print(actual_result)
    assert actual_result == 0




# def test_area_satisfied(setup_pcd_sector, setup_built_interventions,
#     setup_site_sectors, setup_service_obligation_capacity,
#     setup_traffic, setup_market_share
#     ):

#     actual_result = _area_satisfied(setup_pcd_sector, setup_built_interventions,
#     setup_site_sectors, setup_service_obligation_capacity,
#     setup_traffic, setup_market_share)

#     print(actual_result)
#     assert actual_result == True
