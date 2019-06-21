"""Cost module
"""

def calculate_costs(data, discount_rate, start_timestep, current_timestep):
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
        discounted_cost = discount_function(
            cost, discount_rate, start_timestep, current_timestep
            )
        output_datum['capex'] = discounted_cost

        cost = datum['opex']
        discounted_cost = discount_function(
            cost, discount_rate, start_timestep, current_timestep
            )
        output_datum['opex'] = discounted_cost

        output_datum['build_date'] = datum['build_date']
        output_datum['pcd_sector'] = datum['pcd_sector']
        output_datum['ran_type'] = datum['ran_type']
        output_datum['site_ngr'] = datum['site_ngr']
        output_datum['frequency'] = datum['frequency']
        output_datum['bandwidth'] = datum['bandwidth']
        output_datum['sectors'] = datum['sectors']
        output_datum['technology'] = datum['technology']
        output_datum['type'] = datum['type']
        output_datum['item'] = datum['item']
        output_datum['mast_height'] = datum['mast_height']
        output_datum['lad'] = datum['lad']

        output.append(output_datum)

    return output


def discount_function(cost, discount_rate, start_timestep, current_timestep):
    """
    Discount cost based on timestep

    """
    timestep = current_timestep - start_timestep

    discounted_cost = (
        cost / (1 + discount_rate)**(timestep)
        )

    return discounted_cost
