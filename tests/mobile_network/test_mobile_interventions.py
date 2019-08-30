"""
Test Mobile Network interventions.py

11th May 2019
Written by Ed Oughton

"""
import pytest
from digital_comms.mobile_network.interventions import decide_interventions, _area_satisfied
from digital_comms.mobile_network.model import NetworkManager, PostcodeSector

@pytest.fixture
def basic_system(setup_lad, setup_pcd_sector, setup_assets,
    setup_capacity_lookup, setup_clutter_lookup,
    setup_simulation_parameters):

    system = NetworkManager(setup_lad, setup_pcd_sector,
        setup_assets, setup_capacity_lookup, setup_clutter_lookup,
        setup_simulation_parameters)

    return system


@pytest.fixture
def non_4g_system(setup_lad, setup_pcd_sector, setup_non_4g_assets,
    setup_capacity_lookup, setup_clutter_lookup,
    setup_simulation_parameters):

    system = NetworkManager(setup_lad, setup_pcd_sector,
        setup_non_4g_assets, setup_capacity_lookup,
        setup_clutter_lookup, setup_simulation_parameters)

    return system


@pytest.fixture
def mixed_system(setup_lad, setup_pcd_sector, setup_mixed_assets,
    setup_capacity_lookup, setup_clutter_lookup,
    setup_simulation_parameters):

    system = NetworkManager(setup_lad, setup_pcd_sector, setup_mixed_assets,
        setup_capacity_lookup, setup_clutter_lookup,
        setup_simulation_parameters)

    return system


def test_decide_interventions(non_4g_system, basic_system,
    mixed_system, setup_simulation_parameters):

    actual_result = decide_interventions(
        'minimal', 250000, 0,
        mixed_system, 2020, setup_simulation_parameters
    )

    assert actual_result == ([], 250000, [])

    actual_result = decide_interventions(
        'upgrade_to_lte', 142446, 2,
        non_4g_system, 2020, setup_simulation_parameters
    )

    assert len(actual_result[0]) == 2
    assert actual_result[1] == 0

    actual_result = decide_interventions(
        'upgrade_to_lte', 142446, 2,
        mixed_system, 2020, setup_simulation_parameters
    )

    assert actual_result == ([], 142446, [])

    # #50917 * 4 = 203668
    actual_result = decide_interventions(
        'macrocell', 203668, 10,
        mixed_system, 2020, setup_simulation_parameters
    )
    assert len(actual_result[0]) == 4
    assert actual_result[1] == 0

    actual_result = decide_interventions(
        'macrocell', 203668, 0,
        mixed_system, 2020, setup_simulation_parameters
    )
    assert len(actual_result[0]) == 0
    assert actual_result[1] == 203668

    actual_result = decide_interventions(
        'macrocell_700', 50917, 10,
        mixed_system, 2020, setup_simulation_parameters
    )

    assert len(actual_result[0]) == 1
    assert actual_result[1] == 0

    # #50917 * 2 = 101,834
    # #40220 * 3 = £120,660
    actual_result = decide_interventions(
        'small_cell_and_spectrum', 222494 , 1000,
        mixed_system, 2020, setup_simulation_parameters
    )

    assert len(actual_result[0]) == 5
    assert actual_result[1] == 0
