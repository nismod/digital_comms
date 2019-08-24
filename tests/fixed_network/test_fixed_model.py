import pytest
import os

from digital_comms.fixed_network.model import NetworkManager
from digital_comms.fixed_network.interventions import decide_interventions

@pytest.fixture
def parameters():
    return {
        'annual_budget': 1e7,
        'max_market_investment_per_dwelling': 1000,
        'annual_subsidy': 1e7,
        'subsidy_rural_percentile': 0.66,
        'subsidy_outsidein_percentile': 0.0,
        'market_match_funding': 1e7,
    }

@pytest.fixture
def base_system(parameters):

    assets = [{
        'exchange_id': 'exchange_EACAM',
        'exchange_area': 10,
        'lad_id': 'ABC',
        'fttp_availability': 10,
        'fttdp_availability': 0,
        'fttc_availability': 90,
        'adsl_availability': 100,
        'exchange_dwellings': 100,
    }]

    system = NetworkManager(assets, parameters)

    return system


class TestUpgradeExchange:
    """
    """

    def test_compute_exchange(self, base_system):

        actual = base_system._exchanges[0]
        assert actual.id == 'exchange_EACAM'
        assert actual.lad == 'ABC'

        assert actual.fttp == 10
        assert actual.fttdp == 0
        assert actual.fttc == 80
        assert actual.adsl == 10
        assert actual.total_prems == 100

        assert actual.fttp_unserved == 1
        assert actual.fttdp_unserved == 0
        assert actual.fttc_unserved == 8

        intervention_list = [('exchange_EACAM', 'fttdp')]
        base_system.upgrade(intervention_list)

        assert actual.id == 'exchange_EACAM'
        assert actual.fttp == 10
        assert actual.fttdp == 90
        assert actual.fttc == 0
        assert actual.adsl == 0
        assert actual.total_prems == 100

        intervention_list = [('exchange_EACAM', 'fttp')]
        base_system.upgrade(intervention_list)

        assert actual.id == 'exchange_EACAM'
        assert actual.fttp == 100
        assert actual.fttdp == 0
        assert actual.fttc == 0
        assert actual.adsl == 0
        assert actual.total_prems == 100


def test_coverage(base_system):

    expected_coverage = [{
        'id': 'exchange_EACAM',
        'percentage_of_premises_with_fttp': 10.0,
        'percentage_of_premises_with_fttdp': 0.0,
        'percentage_of_premises_with_fttc': 80.0,
        'percentage_of_premises_with_adsl': 10.0,
        'sum_of_premises': 100,
    }]

    actual_coverage = base_system.coverage()

    assert expected_coverage == actual_coverage

    intervention_list = [('exchange_EACAM', 'fttdp')]
    base_system.upgrade(intervention_list)

    expected_coverage = [{
        'id': 'exchange_EACAM',
        'percentage_of_premises_with_fttp': 10.0,
        'percentage_of_premises_with_fttdp': 90.0,
        'percentage_of_premises_with_fttc': 0.0,
        'percentage_of_premises_with_adsl': 0.0,
        'sum_of_premises': 100,
    }]

    actual_coverage = base_system.coverage()

    assert expected_coverage == actual_coverage

    intervention_list = [('exchange_EACAM', 'fttp')]
    base_system.upgrade(intervention_list)

    expected_coverage = [{
        'id': 'exchange_EACAM',
        'percentage_of_premises_with_fttp': 100.0,
        'percentage_of_premises_with_fttdp': 0.0,
        'percentage_of_premises_with_fttc': 0.0,
        'percentage_of_premises_with_adsl': 0.0,
        'sum_of_premises': 100,
    }]

    actual_coverage = base_system.coverage()

    assert expected_coverage == actual_coverage


def test_capacity(base_system):

        # 'fttp_availability': 10 * 1000
        # 'fttdp_availability': 0,
        # 'fttc_availability': 80 * 90
        # 'adsl_availability': 10 * 24
        # 'exchange_dwellings': 100,

    expected_capacity = [{
        'id': 'exchange_EACAM',
        #  fttp       fttdp     fttc     docsis3   adsl
        # ((10*1000) + (0*300) + (80*80) + (0*150) + (10*24)) / 20 == round(69.5)
        # ((0*1000) + (0*300) + (5*80) + (5*150) + (10*24)) / 20 == round(69.5)
        'average_capacity': 166,
    }]

    actual_capacity = base_system.capacity()

    assert expected_capacity == actual_capacity

def test_fttp_costs(base_system):

    actual = base_system._exchanges[0]

    actual_costs = actual._calculate_roll_out_costs()

    assert actual_costs['fttp'] == 100000
    assert actual_costs['fttdp'] == 50000
    assert actual_costs['fttc'] == 25000


def test_fttp_upgrade_exchanges(base_system, parameters):

    year = 2019
    technology = 'fttp'
    policy = 'market_insideout'
    parameters['annual_budget'] = 10000000
    parameters['subsidy'] = 10000000
    parameters['telco_match_funding'] = 10000000
    # print(base_system)
    # #build interventions
    built_interventions = decide_interventions(
        base_system, year, technology, policy, parameters)

    # small_system.upgrade(built_interventions)

    # actual_coverage = small_system.coverage('exchange')

    # expected_coverage = [{
    #     'id': 'exchange_EACAM',
    #     'percentage_of_premises_with_fttp': 100,
    #     'percentage_of_premises_with_fttdp': 0,
    #     'percentage_of_premises_with_fttc': 0,
    #     'percentage_of_premises_with_docsis3': 0,
    #     'percentage_of_premises_with_adsl': 0,
    #     'sum_of_premises': 20,
    # }]

    assert built_interventions[0][4] == 100000
