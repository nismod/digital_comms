"""Decide on interventions
"""
# pylint: disable=C0103
#from digital_comms.mobile_model.ccam import PostcodeSector

import copy
import math
from operator import itemgetter

################################################################
# EXAMPLE COST LOOKUP TABLE
# - TODO come back to net present value or total cost of ownership for costs
################################################################

def get_distributions(system, technology, reverse_value):
    """Specifically obtain and rank Distribution Points by technology and policy.

    Parameters
    ----------
    system : object
        This is an NetworkManger object containing the whole system.
    technology : string
        The current technology being deployed.
    reverse_value : string
        Used as an argument in 'sorted' to rank how assets will be deployed. Either True or False.

    Returns
    -------
    list_of_objects
        Returns desired assets ranked based on technology benefit-cost ratio and reverse_value preference.

    """
    return sorted(system._distributions, key=lambda item: item.rollout_bcr[technology], reverse=reverse_value)

def decide_interventions(system, timestep, technology, policy, annual_budget, adoption_cap,
                        subsidy, telco_match_funding, service_obligation_capacity):
    """Given strategy parameters and a system, decide the best potential interventions.

    Parameters
    ----------
    system : object
        This is an NetworkManger object containing the whole system.
    timestep : int
        The current timestep.
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
    built_interventions = meet_most_beneficial_demand(system, timestep, technology, policy, annual_budget, adoption_cap,
                                                        subsidy, telco_match_funding, service_obligation_capacity)

    return built_interventions

def meet_most_beneficial_demand(system, timestep, technology, policy, annual_budget, adoption_cap,
                                subsidy, telco_match_funding, service_obligation_capacity):
    """Given strategy parameters and a system, meet the most beneficial demand.

    TODO: address service_obligation_capacity here.

    """
    return _suggest_interventions(
        annual_budget, technology, policy, system, timestep, adoption_cap, telco_match_funding, subsidy)

def _suggest_interventions(system, timestep, technology, policy, annual_budget, adoption_cap, subsidy, telco_match_funding, threshold=None):
    """Given strategy parameters and a system, suggest the best potential interventions.

    Parameters
    ----------
    system : object
        This is an NetworkManger object containing the whole system.
    timestep : int
        The current timestep.
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
    premises_passed = 0

    if policy == 's1_market_based_roll_out':
        distributions = get_distributions(system, technology, False)
        for distribution in distributions:
            if (premises_passed + len(distribution._clients)) < adoption_cap:
                if distribution.rollout_costs[technology] < annual_budget:
                    annual_budget -= distribution.rollout_costs[technology]
                    deployment_type = 'market_based'
                    built_interventions.append((distribution.id, technology, policy, deployment_type, distribution.rollout_costs[technology]))
                    premises_passed += len(distribution._clients)
                else:
                    break
            else:
                break

    elif policy == 's2_rural_based_subsidy' or 's3_outside_in_subsidy':
        distributions = get_distributions(system, technology, False)
        deployment_type = 'market_based'
        for distribution in distributions:
            if (premises_passed + len(distribution._clients)) < adoption_cap:
                if distribution.rollout_costs[technology] < annual_budget:
                    annual_budget -= distribution.rollout_costs[technology]
                    built_interventions.append((distribution.id, technology, policy, deployment_type, distribution.rollout_costs[technology]))
                    premises_passed += len(distribution._clients)
                else:
                    break
            else:
                break

        if policy == 's2_rural_based_subsidy':
            reverse_value = True
        elif policy == 's3_outside_in_subsidy':
            reverse_value = False
        else:
            print('policy not recognised')

        subsidised_distributions = get_distributions(system, technology, reverse_value)
        # subsidy_cutoff = math.floor(len(subsidised_distributions) * 0.66) # get the bottom third of the distribution cutoff point
        # subsidised_distributions = subsidised_distributions[subsidy_cutoff:] # get the bottom third of the distribution
        deployment_type = 'subsidy_based'
        for distribution in subsidised_distributions:
            if distribution.rollout_costs[technology] < telco_match_funding:
                subsidy_required_per_distribution_point = distribution.rollout_costs[technology] - distribution.rollout_benefits[technology]
                telco_match_funding -= distribution.rollout_costs[technology]
                distribution.rollout_costs[technology] = distribution.rollout_costs[technology] + subsidy_required_per_distribution_point
                built_interventions.append((distribution.id, technology, policy, deployment_type, distribution.rollout_costs[technology]))
                premises_passed += len(distribution._clients)
            else:
                break

    else:
        print("'policy not recognised. No upgrades built")

    return built_interventions#, spend, match_funding_spend, subsidised_spend
