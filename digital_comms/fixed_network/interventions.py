"""Decide on interventions
"""

################################################################
# EXAMPLE COST LOOKUP TABLE
# - TODO come back to net present value or total cost of ownership for costs
################################################################


def get_all_assets_ranked(system_assets, ranking_variable, asset_variable, technology, reverse_value):
    """Specifically obtain and rank Distribution Points by technology and policy.

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
        Returns desired assets ranked based on technology benefit-cost ratio and reverse_value
        preference.

    """
    if ranking_variable == 'rollout_benefits':
            assets = sorted(
            (asset for asset in system_assets \
            if getattr(asset, technology) != asset.total_prems),
            key=lambda item: item.rollout_benefits[technology], reverse=reverse_value)

    elif ranking_variable == 'rollout_costs':
        assets = sorted(
            (asset for asset in system_assets \
            if getattr(asset, technology) != asset.total_prems),
            key=lambda item: item.rollout_costs[technology], reverse=reverse_value)

    elif ranking_variable == 'rollout_bcr':
        assets = sorted(
            (asset for asset in system_assets \
            if getattr(asset, technology) != asset.total_prems),
            key=lambda item: item.rollout_bcr[technology], reverse=reverse_value)

    elif ranking_variable == 'total_potential_bcr':
        assets = sorted(
            (asset for asset in system_assets \
            if getattr(asset, technology) != asset.total_prems),
            key=lambda item: item.total_potential_bcr[technology], reverse=reverse_value)
    else:
        raise ValueError('Did not recognise ranking preference variable')

    return assets


def decide_interventions(system_assets, year, technology, policy, annual_budget,
                        adoption_cap, subsidy, telco_match_funding,
                        service_obligation_capacity, asset_variable):
    """Given strategy parameters and a system, decide the best potential interventions.

    Parameters
    ----------
    distributions : list of digital_comms.fixed_network.model.Distribution
        A list of distribution points
    year : int
        The current year.
    technology : string
        The current technology being deployed.
    policy : string
        Policy used to determine how new technologies will be deployed.
    annual_budget : int
        The annual annual_budget capable of spending.
    adoption_cap : int
        Maximum annual adoption as exogenously specified by scenario.
    subsidy : int
        Annual subsidy amount.
    telco_match_funding : int
        Returns the annual budget capable of being match funded.
    service_obligation_capacity
        annual universal service obligation

    Returns
    -------
    built_interventions : list of tuples
        Contains the upgraded asset id with technology, policy, deployment type and affliated costs.

    """
    # Build to meet demand most beneficial demand

    built_interventions = meet_most_beneficial_demand(system_assets, year, technology,
                                                    policy, annual_budget,
                                                    adoption_cap, subsidy,
                                                    telco_match_funding,
                                                    service_obligation_capacity,
                                                    asset_variable)

    return built_interventions


def meet_most_beneficial_demand(system_assets, year, technology, policy, annual_budget, adoption_cap,
                                subsidy, telco_match_funding, service_obligation_capacity, asset_variable):
    """Given strategy parameters and a system, suggest the best potential interventions.

    Parameters
    ----------
    distributions : list of digital_comms.fixed_network.model.Distribution
        A list of distribution points
    year : int
        The current year.
    technology : string
        The current technology being deployed.
    policy : string
        Policy used to determine how new technologies will be deployed.
    annual_budget : int
        The annual annual_budget capable of spending.
    adoption_cap : int
        Maximum annual adoption as exogenously specified by scenario.
    subsidy : int
        Annual subsidy amount.
    telco_match_funding : int
        Returns the annual budget capable of being match funded.

    Returns
    -------
    built_interventions : list of tuples
        Contains the upgraded asset id with technology, policy, deployment type and affliated costs.

    TODO: revise subsidy code to be targetted at specific geotypes (e.g. rural).

    """
    built_interventions = []
    upgraded_ids = []
    premises_passed = 0

    if policy == 's1_market_based_roll_out':

        assets = get_all_assets_ranked(
            system_assets, 'rollout_bcr', asset_variable, technology, True
        )
        for asset in assets:
            if asset.id not in upgraded_ids:
                if asset.rollout_costs[technology] < annual_budget:
                    annual_budget -= asset.rollout_costs[technology]
                    deployment_type = 'market_based'
                    built_interventions.append(
                        (
                            asset.id,
                            technology,
                            policy,
                            deployment_type,
                            asset.rollout_benefits[technology],
                            asset.rollout_costs[technology],
                            asset.rollout_bcr[technology],
                        )
                    )
                    upgraded_ids.append(asset.id)
                    premises_passed += asset.total_prems
                else:
                    break


    elif policy == 's2_rural_based_subsidy' or 's3_outside_in_subsidy':

        assets = get_all_assets_ranked(
            system_assets, 'total_potential_bcr', asset_variable, technology, True
        )
        deployment_type = 'market_based'
        for asset in assets:
            if asset.id not in upgraded_ids:
                if asset.rollout_costs[technology] < annual_budget:
                    annual_budget -= asset.rollout_costs[technology]
                    built_interventions.append(
                        (
                            asset.id,
                            technology,
                            policy,
                            deployment_type,
                            asset.rollout_benefits[technology],
                            asset.rollout_costs[technology],
                            asset.rollout_bcr[technology],
                        )
                    )
                    upgraded_ids.append(asset.id)
                    premises_passed += asset.total_prems
                else:
                    break
            else:
                break

        if policy == 's2_rural_based_subsidy':
            reverse_value = True
        elif policy == 's3_outside_in_subsidy':
            reverse_value = False
        else:
            raise ValueError('Did not recognise stipulated policy')

        subsidised_assets = get_all_assets_ranked(
            system_assets, 'total_potential_bcr', asset_variable, technology, reverse_value
        )

        # # get the bottom third of the distribution cutoff point
        # subsidy_cutoff = math.floor(len(subsidised_distributions) * 0.66)

        # # get the bottom third of the distribution
        # subsidised_distributions = subsidised_distributions[subsidy_cutoff:]

        deployment_type = 'subsidy_based'
        for asset in subsidised_assets:
            if asset.id not in upgraded_ids:
                if asset.rollout_costs[technology] < (telco_match_funding + subsidy):
                    telco_match_funding -= asset.rollout_costs[technology]
                    asset.rollout_costs[technology] = \
                        asset.rollout_costs[technology]
                    built_interventions.append(
                        (
                            asset.id,
                            technology,
                            policy,
                            deployment_type,
                            asset.rollout_benefits[technology],
                            asset.rollout_costs[technology],
                            asset.rollout_bcr[technology],
                        )
                    )
                    upgraded_ids.append(asset.id)
                    premises_passed += asset.total_prems
                else:
                    break
    else:
        raise ValueError('Did not recognise stipulated policy')

    return built_interventions
