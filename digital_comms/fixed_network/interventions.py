"""

Decide on interventions

"""
import math

def get_all_assets_ranked(system, technology, roll_out, percentile):
    """

    Specifically obtain and rank exchanges by technology and policy.

    Parameters
    ----------
    distributions : list of digital_comms.fixed_network.model.Distribution
        A list of distribution points
    technology : str
        The current technology being deployed.
    reverse_value : bool
        Used as an argument in 'sorted' to rank how assets will be deployed.

    Returns
    -------
    list_of_objects
        Returns desired assets ranked based on technology benefit-cost ratio
        and reverse_value preference.

    """
    if roll_out == 'insideout':
        handle = '{}_unserved'.format(technology)

        all_assets = sorted(
            (exchange for exchange in system._exchanges \
            if getattr(exchange, technology) != exchange.total_prems),
                key=lambda item: getattr(item, handle), reverse=True)

    elif roll_out == 'rural':
        handle = '{}_unserved'.format(technology)

        all_assets = sorted(
            (exchange for exchange in system._exchanges \
            if getattr(exchange, technology) != exchange.total_prems),
                key=lambda item: getattr(item, handle), reverse=False)

    elif roll_out == 'outsidein':
        handle = '{}_unserved'.format(technology)

        all_assets = sorted(
            (exchange for exchange in system._exchanges \
            if getattr(exchange, technology) != exchange.total_prems),
                key=lambda item: getattr(item, handle), reverse=False)

    else:
        raise ValueError('Did not recognise ranking preference variable')

    cutoff = math.floor(len(all_assets) * percentile)

    assets = all_assets[cutoff:]

    return assets


def decide_interventions(system, year, technology, policy, parameters):
    """
    ???

    """
    built_interventions = []
    upgraded_ids = []
    premises_passed = 0

    annual_budget = parameters['annual_budget']

    roll_out = policy.split('_')[1]
    policy = policy.split('_')[0]

    if policy == 'market':

        assets = get_all_assets_ranked(system, technology, roll_out, 0)

        capital_investment_type= 'private'

        for asset in assets:
            if asset.id not in upgraded_ids:
                if asset.rollout_costs[technology] < annual_budget:
                    annual_budget -= asset.rollout_costs[technology]
                    built_interventions.append(
                        (
                            asset.id,
                            technology,
                            policy,
                            capital_investment_type,
                            asset.rollout_costs[technology],
                        )
                    )
                    upgraded_ids.append(asset.id)
                    premises_passed += asset.total_prems
                else:
                    break

    elif policy == 'subsidy':

        capital_investment_type = 'private'

        assets = get_all_assets_ranked(system, technology, roll_out, 100)

        for asset in assets:
            if asset.id not in upgraded_ids:
                if asset.rollout_costs[technology] < annual_budget:
                    annual_budget -= asset.rollout_costs[technology]
                    built_interventions.append(
                        (
                            asset.id,
                            technology,
                            policy,
                            capital_investment_type,
                            asset.rollout_costs[technology], #total cost
                            asset.rollout_costs[technology], #private sector spending
                            0, #subsidy
                        )
                    )
                    upgraded_ids.append(asset.id)
                    premises_passed += asset.total_prems
                else:
                    break

        capital_investment_type = 'public_private'
        percentile = parameters['subsidy_{}_percentile'.format(roll_out)]
        max_market_investment_per_dwelling = parameters['max_market_investment_per_dwelling']
        annual_subsidy = parameters['annual_subsidy']
        market_match_funding = parameters['market_match_funding']

        subsidised_assets = get_all_assets_ranked(system, technology, roll_out, percentile)

        for asset in subsidised_assets:
            if asset.id not in upgraded_ids:

                handle = '{}_unserved'.format(technology)
                dwellings_to_upgrade = getattr(asset, handle)

                total_private_investment = round(dwellings_to_upgrade *  max_market_investment_per_dwelling)

                total_upgrade_cost = asset.rollout_costs[technology]

                if total_upgrade_cost < total_private_investment:
                    total_subsidy = 0
                else:
                    total_subsidy = round(total_upgrade_cost - total_private_investment)

                if total_subsidy <= annual_subsidy:

                    annual_subsidy -= total_subsidy
                    market_match_funding -= total_private_investment

                    built_interventions.append(
                        (
                            asset.id,
                            technology,
                            policy,
                            capital_investment_type,
                            total_upgrade_cost, #total cost
                            total_private_investment, #private sector spending
                            total_subsidy, #subsidy
                        )
                    )
                    upgraded_ids.append(asset.id)

                else:
                    break
    else:
        raise ValueError('Did not recognise stipulated policy')

    return built_interventions
