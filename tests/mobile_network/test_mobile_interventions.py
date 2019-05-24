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











    # assets += interventions_built

    # # simulate with decisions
    # system = NetworkManager(
    #     lads, postcode_sectors, assets,
    #     capacity_lookup_table, clutter_lookup,
    #     service_obligation_capacity, traffic,
    #     market_share, mast_height
    #     )


    # #test strategy 'sectorisation'
    # actual_result = decide_interventions(
    #     'sectorisation', 2e9, 0,
    #     basic_system, 2020, 0.5, 0.25, 30
    # )
    # print(actual_result)
    # assert len(actual_result[0]) == 2
    # assert actual_result[1] == 0
















    # #test strategy 'sectorisation'
    # initial_result = decide_interventions(
    #     'sectorisation', 1e6, 1000,
    #     basic_system, 2020, 0.15, 0.25
    # )[2]

    # actual_interventions = []
    # for result in initial_result:
    #     actual_interventions.append(result[2])

    # actual_result = list(set(actual_interventions)).sort()

    # expected_result = [
    #     'carrier_700',
    #     'add_3_sectors',
    #     'carrier_3500',
    #     ]

    # assert actual_result == expected_result.sort()

    # #test strategy 'macro_densification'
    # actual_result = decide_interventions(
    #     'macro-densification', 150000, 1000,
    #     basic_system, 2020, 0.15, 0.25
    # )[2]

    # expected_result = [
    #     ('CB12', 1, 'carrier_700', 50917),
    #     ('CB12', 1, 'carrier_3500', 50917),
    #     ('CB12', 1, 'build_5G_macro_site', 150000),
    # ]

    # assert actual_result == expected_result

    # #test strategy 'macro_densification'
    # actual_result = decide_interventions(
    #     'macro-densification', 1e6, 1000,
    #     basic_system, 2020, 0.15, 0.25, 30
    # )[2]

    # expected_result = [
    #     ('CB12', 1, 'carrier_700', 50917),
    #     ('CB12', 1, 'carrier_3500', 50917),
    #     ('CB12', 1, 'build_5G_macro_site', 150000),
    # ]
    # print(actual_result)
    # assert actual_result == 0

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

# def test_area_satisfied(setup_pcd_sector, setup_built_interventions,
#     setup_site_sectors, setup_service_obligation_capacity,
#     setup_traffic, setup_market_share
#     ):

#     actual_result = _area_satisfied(setup_pcd_sector, setup_built_interventions,
#     setup_site_sectors, setup_service_obligation_capacity,
#     setup_traffic, setup_market_share)

#     print(actual_result)
#     assert actual_result == True
