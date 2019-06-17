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
            'opex': 50
        }
    ]

    # output_data = calculate_costs(input_data, 0.05, 0)

    # assert round(output_data[0]['capex'], 0) == 200
    # assert round(output_data[0]['opex'], 0) == 50

    # # input_data = [
    # #     {
    # #         'capex': 200,
    # #         'opex': 50
    # #     }
    # # ]

    # output_data = calculate_costs(input_data, 0.1, 0)

    # assert round(output_data[0]['capex'], 0) == 200
    # assert round(output_data[0]['opex'], 0) == 50

    # # input_data = [
    # #     {
    # #         'capex': 200,
    # #         'opex': 50
    # #     }
    # # ]

    # output_data = calculate_costs(input_data, 0.05, 2)

    # assert round(output_data[0]['capex'], 0) == 181
    # assert round(output_data[0]['opex'], 0) == 45

    # # input_data = [
    # #     {
    # #         'capex': 200,
    # #         'opex': 50
    # #     }
    # # ]

    # output_data = calculate_costs(input_data, 0.1, 2)

    # assert round(output_data[0]['capex'], 0) == 165
    # assert round(output_data[0]['opex'], 0) == 41

    # # input_data = [
    # #     {
    # #         'capex': 200,
    # #         'opex': 50
    # #     }
    # # ]

    output_data = calculate_costs(input_data, 0.05, 5)

    assert round(output_data[0]['capex'], 0) == 157
    assert round(output_data[0]['opex'], 0) == 39

    # input_data = [
    #     {
    #         'capex': 200,
    #         'opex': 50
    #     }
    # ]

    output_data = calculate_costs(input_data, 0.1, 5)

    assert round(output_data[0]['capex'], 0) == 124
    assert round(output_data[0]['opex'], 0) == 31
