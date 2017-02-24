from digital_comms.fixed import Band, Exchange, read_in_exchange, apply_interventions_to_exchanges, calculate_speed, aggregate_by_region, run

def test_exchange():

    exchange = Exchange([100, 200, 300], [50, 50, 50], {})
    actual = exchange.average_speed_per_exchange()

    expected = 50

    assert actual == expected

def test_exchange_all_fttp():

    exchange = Exchange([100, 200, 300], [50, 50, 50], {})
    exchange.update_band_technology(1, 'fttp')
    exchange.update_band_technology(2, 'fttp')
    exchange.update_band_technology(3, 'fttp')

    actual = exchange.average_speed_per_exchange()

    expected = 2000

    assert actual == expected

def test_exchange_only_two_fttp():

    exchange = Exchange([100, 200, 300], [50, 50, 50], {})
    exchange.update_band_technology(1, 'fttp')
    exchange.update_band_technology(2, 'fttp')

    actual = exchange.average_speed_per_exchange()

    expected = 1025

    assert actual == expected

def test_apply_interventions():

    data = [{'name': 'gfast_1_1',
             'capital_cost': {'value': 2201,
                              'units': '£(million)'},
             'economic_lifetime': {'value': 15,
                                   'units': 'years'},
             'operational_life': {'value': 15,
                                  'units': 'years'},
             'capacity': {'value': 2000,
                          'units': 'Mbps'},
             'location': 'Great Britain'}]

    filepath = './tests/fixtures/test_exchange.csv'
    exchanges, codes, geotypes = read_in_exchange(filepath)

    apply_interventions_to_exchanges(data, exchanges, geotypes)

    # assert 0

def test_calculate_speed():

    filepath = './tests/fixtures/test_exchange.csv'
    exchanges, codes, geotypes = read_in_exchange(filepath)

    actual = calculate_speed(exchanges)

    expected = {'CLBER': 50,
                'CLBIS': 50,
                'CLCAN': 50}

    assert actual == expected

def test_calc_aggregate():

    results = {'CLBER': 50,
               'CLBIS': 50,
               'CLCAN': 50}

    aggregation = {'00London': ['CLBER', 'CLBIS', 'CLCAN']}
    actual = aggregate_by_region(results, aggregation)

    expected = {'00London': 50}

    assert actual == expected

def test_run_model():

    data = [{'name': 'gfast_1_1',
             'capital_cost': {'value': 2201, 'units': '£(million)'},
             'economic_lifetime': {'value': 15, 'units': 'years'},
             'operational_life': {'value': 15, 'units': 'years'},
             'capacity': {'value': 2000, 'units': 'Mbps'},
             'location': 'Great Britain'}]

    actual = run(data, './tests/fixtures/test_exchange.csv')
    expected = {'average_speed': {'00London': 100}}

    assert actual == expected
