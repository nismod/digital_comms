"""Cost module
"""

def calculate_costs(data, discount_rate, timestep):
    """
    Calculates the discounted cost for capex and opex, depending on timestep.

    Parameters
    ----------
    data : list of dicts
        Contains a list of assets
    timestep : int
        The timestep relative to the initial starting point

    Returns
    -------
    output : list of dicts
        Contains a list of assets, with affliated discounted capex and opex costs.

    """
    output = []

    for datum in data:
        output_datum = {}
        cost = datum['capex']
        discounted_cost = discount_function(cost, discount_rate, timestep)
        output_datum['capex'] = discounted_cost

        cost = datum['opex']
        discounted_cost = discount_function(cost, discount_rate, timestep)
        output_datum['opex'] = discounted_cost

        output.append(output_datum)

    return output


def discount_function(cost, discount_rate, timestep):
    """
    Discount cost based on timestep

    """
    # print('timestep {}'.format(timestep))
    # print('1 + discount_rate {}'.format(1 + discount_rate))
    # print('cost / (1 + discount_rate)**(timestep-1) {}'.format(cost / (1 + discount_rate)**(timestep)))
    discounted_cost = (
        cost / (1 + discount_rate)**(timestep)
        )

    return discounted_cost
