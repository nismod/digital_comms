"""
Test Mobile Network interventions.py
11th May 2019
Written by Edward J. Oughton

"""
import pytest
from digital_comms.mobile_network.costs import(
    calculate_costs
    )


def test_costs():

    base_year = 2019
    end_year = 2021
    increment = 1
    timesteps = range(base_year, end_year + 1, increment)

    input_data = [
        {
            'capex': 200,
            'opex': 50,
            'build_date': 2020,
            'pcd_sector': '',
            'ran_type': '',
            'site_ngr': '',
            'frequency': '',
            'bandwidth': '',
            'sectors': '',
            'technology': '',
            'type': '',
            'item': '',
            'mast_height': '',
            'lad': '',
        }
    ]

    output_data = calculate_costs(input_data, 0.05, 2019, 2019)

    assert round(output_data[0]['capex'], 0) == 200
    assert round(output_data[0]['opex'], 0) == 50

    output_data = calculate_costs(input_data, 0.1, 2019, 2019)

    assert round(output_data[0]['capex'], 0) == 200
    assert round(output_data[0]['opex'], 0) == 50

    output_data = calculate_costs(input_data, 0.05, 2019, 2021)

    assert round(output_data[0]['capex'], 0) == 181
    assert round(output_data[0]['opex'], 0) == 45

    output_data = calculate_costs(input_data, 0.1, 2019, 2021)

    assert round(output_data[0]['capex'], 0) == 165
    assert round(output_data[0]['opex'], 0) == 41

    output_data = calculate_costs(input_data, 0.05, 2019, 2024)

    assert round(output_data[0]['capex'], 0) == 157
    assert round(output_data[0]['opex'], 0) == 39

    output_data = calculate_costs(input_data, 0.1, 2019, 2024)

    assert round(output_data[0]['capex'], 0) == 124
    assert round(output_data[0]['opex'], 0) == 31

    output_data = calculate_costs(input_data, 0.05, 2019, 2039)

    assert round(output_data[0]['capex'], 0) == 75
    assert round(output_data[0]['opex'], 0) == 19

    output_data = calculate_costs(input_data, 0.1, 2019, 2039)

    assert round(output_data[0]['capex'], 0) == 30
    assert round(output_data[0]['opex'], 0) == 7
