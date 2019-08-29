import pytest
from digital_comms.fixed_network.model import NetworkManager
from digital_comms.fixed_network.interventions import get_all_assets_ranked
from digital_comms.fixed_network.interventions import decide_interventions

@pytest.fixture
def parameters():
    return {
        'annual_budget': 1e7,
        'max_market_investment_per_dwelling': 1000,
        'annual_subsidy': 1e7,
        'subsidy_rural_percentile': 0.5,
        'subsidy_outsidein_percentile': 0.0,
        'market_match_funding': 1e7,
    }


@pytest.fixture
def base_system(parameters):

    assets = [
        {
        'exchange_id': 'A',
        'area': 10,
        'lad_id': 'ABC',
        'fttp_availability': 10,
        'fttdp_availability': 10,
        'fttc_availability': 90,
        'adsl_availability': 100,
        'exchange_dwellings': 100,
        },
        {
        'exchange_id': 'B',
        'area': 10,
        'lad_id': 'ABC',
        'fttp_availability': 10,
        'fttdp_availability': 10,
        'fttc_availability': 90,
        'adsl_availability': 100,
        'exchange_dwellings': 200,
        },
        {
        'exchange_id': 'C',
        'area': 10,
        'lad_id': 'ABC',
        'fttp_availability': 10,
        'fttdp_availability': 10,
        'fttc_availability': 90,
        'adsl_availability': 100,
        'exchange_dwellings': 300,
        },
        {
        'exchange_id': 'D',
        'area': 10,
        'lad_id': 'ABC',
        'fttp_availability': 10,
        'fttdp_availability': 10,
        'fttc_availability': 90,
        'adsl_availability': 100,
        'exchange_dwellings': 400,
        },
    ]

    system = NetworkManager(assets, parameters)

    return system

@pytest.fixture
def constrained_parameters():
    return {
        'annual_budget': 1e5,
        'max_market_investment_per_dwelling': 1000,
        'annual_subsidy': 1e7,
        'subsidy_rural_percentile': 0.5,
        'subsidy_outsidein_percentile': 0.0,
        'market_match_funding': 1e7,
    }


def test_get_all_assets_ranked(base_system, parameters):

    actual_ranking = get_all_assets_ranked(
        base_system, 'fttdp', 'insideout', 0
    )

    actual_ranking_ids = [e.id for e in actual_ranking]

    expected_ranking = ['A', 'B', 'C', 'D']

    assert actual_ranking_ids == expected_ranking

    actual_ranking = get_all_assets_ranked(
        base_system, 'fttdp', 'rural', 0.5
    )

    actual_ranking_ids = [e.id for e in actual_ranking]

    expected_ranking = ['B', 'A']

    assert actual_ranking_ids == expected_ranking

    actual_ranking = get_all_assets_ranked(
        base_system, 'fttdp', 'outsidein', 0
    )

    actual_ranking_ids = [e.id for e in actual_ranking]

    expected_ranking = ['D', 'C', 'B', 'A']

    assert actual_ranking_ids == expected_ranking


def test_decide_interventions(base_system, parameters, constrained_parameters):

    built_interventions = decide_interventions(
        base_system, 'fttdp', 'market_insideout', parameters
    )

    built_intervention_ids = [i[0] for i in built_interventions]

    expectated_intervention_ids = ['A', 'B', 'C', 'D']

    assert built_intervention_ids == expectated_intervention_ids

    built_interventions = decide_interventions(
        base_system, 'fttdp', 'subsidy_rural', parameters
    )

    built_intervention_ids = [i[0] for i in built_interventions]

    expectated_intervention_ids = ['D','C','B', 'A']

    assert built_intervention_ids == expectated_intervention_ids

    built_interventions = decide_interventions(
        base_system, 'fttdp', 'subsidy_outsidein', parameters
    )

    built_intervention_ids = [i[0] for i in built_interventions]

    expectated_intervention_ids = ['D', 'C', 'B', 'A']

    assert built_intervention_ids == expectated_intervention_ids

    built_interventions = decide_interventions(
        base_system, 'fttdp', 'market_insideout', constrained_parameters
    )

    expectated_interventions = [
        ('A', 'fttdp', 'market', 'private', 50000),
        ('B', 'fttdp', 'market', 'private', 50000)
    ]

    assert built_interventions == expectated_interventions

    built_interventions = decide_interventions(
        base_system, 'fttp', 'market_insideout', constrained_parameters
    )

    expectated_interventions = [('A', 'fttp', 'market', 'private', 100000)]

    assert built_interventions == expectated_interventions

    built_interventions = decide_interventions(
        base_system, 'fttdp', 'subsidy_rural', constrained_parameters
    )

    expectated_interventions = [
        ('D', 'fttdp', 'subsidy', 'private', 50000, 50000, 0),
        ('C', 'fttdp', 'subsidy', 'private', 50000, 50000, 0),
        ('B', 'fttdp', 'subsidy', 'public_private', 50000, 8000, 42000),
        ('A', 'fttdp', 'subsidy', 'public_private', 50000, 9000, 41000)
    ]

    assert built_interventions == expectated_interventions

    built_interventions = decide_interventions(
        base_system, 'fttp', 'subsidy_rural', constrained_parameters
    )

    expectated_interventions = [
       ('D', 'fttp', 'subsidy', 'private', 100000, 100000, 0),
       ('B', 'fttp', 'subsidy', 'public_private', 100000, 8000, 92000),
       ('A', 'fttp', 'subsidy', 'public_private', 100000, 9000, 91000)
    ]

    assert built_interventions == expectated_interventions


    built_interventions = decide_interventions(
        base_system, 'fttdp', 'subsidy_outsidein', constrained_parameters
    )

    expectated_interventions = [
        ('D', 'fttdp', 'subsidy', 'private', 50000, 50000, 0),
        ('C', 'fttdp', 'subsidy', 'private', 50000, 50000, 0),
        ('B', 'fttdp', 'subsidy', 'public_private', 50000, 8000, 42000),
        ('A', 'fttdp', 'subsidy', 'public_private', 50000, 9000, 41000)
    ]

    assert built_interventions == expectated_interventions

    built_interventions = decide_interventions(
        base_system, 'fttp', 'subsidy_outsidein', constrained_parameters
    )

    expectated_interventions = [
        ('D', 'fttp', 'subsidy', 'private', 100000, 100000, 0),
        ('C', 'fttp', 'subsidy', 'public_private', 100000, 7000, 93000),
        ('B', 'fttp', 'subsidy', 'public_private', 100000, 8000, 92000),
        ('A', 'fttp', 'subsidy', 'public_private', 100000, 9000, 91000)
    ]

    assert built_interventions == expectated_interventions
