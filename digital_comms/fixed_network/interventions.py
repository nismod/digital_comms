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
    return sorted(system._distributions, key=lambda item: item.rollout_bcr[technology], reverse=reverse_value)

def decide_interventions(strategy_tech, strategy_policy, budget, service_obligation_capacity,
                         system, timestep, adoption_cap, telco_match_funding, subsidy):
    """Given strategy parameters and a system return some next best intervention
    """
    # Build to meet demand most beneficial demand
    built, budget, spend, match_funding_spend, subsidised_spend = meet_most_beneficial_demand(
        budget, strategy_tech, strategy_policy, timestep, system, adoption_cap, telco_match_funding, subsidy)

    return built, budget, spend, match_funding_spend, subsidised_spend

def meet_most_beneficial_demand(budget, strategy_tech, strategy_policy, timestep, system, adoption_cap, telco_match_funding, subsidy):
    return _suggest_interventions(
        budget, strategy_tech, strategy_policy, system, timestep, adoption_cap, telco_match_funding, subsidy)

def _suggest_interventions(budget, strategy_tech, strategy_policy, system, timestep, adoption_cap, telco_match_funding, subsidy, threshold=None):

    built_interventions = []
    spend = []
    match_funding_spend = []
    premises_passed = 0
    subsidised_spend = []
    
    if strategy_policy == 's1_market_based_roll_out':
        distributions = get_distributions(system, strategy_tech, False)
        for distribution in distributions:
            if (premises_passed + len(distribution._clients)) < adoption_cap:
                if distribution.rollout_costs[strategy_tech] < budget:
                    budget -= distribution.rollout_costs[strategy_tech]
                    built_interventions.append((distribution.id, strategy_tech, distribution.rollout_costs[strategy_tech]))
                    spend.append((distribution.id, strategy_policy, distribution.rollout_costs[strategy_tech]))
                    premises_passed += len(distribution._clients)
                else:
                    break
            else:
                break

    elif strategy_policy == 's2_rural_based_subsidy' or 's3_outside_in_subsidy':
        distributions = get_distributions(system, strategy_tech, False)  
        for distribution in distributions:
            if (premises_passed + len(distribution._clients)) < adoption_cap:
                if distribution.rollout_costs[strategy_tech] < budget:
                    budget -= distribution.rollout_costs[strategy_tech]
                    built_interventions.append((distribution.id, strategy_tech, distribution.rollout_costs[strategy_tech]))
                    spend.append((distribution.id, strategy_policy, distribution.rollout_costs[strategy_tech]))
                    premises_passed += len(distribution._clients)
                else:
                    break
            else:
                break
        
        if strategy_policy == 's2_rural_based_subsidy':
            reverse_value = True
        elif strategy_policy == 's3_outside_in_subsidy':
            reverse_value = False
        else:
            print('strategy_policy not recognised')

        subsidised_distributions = get_distributions(system, strategy_tech, reverse_value)  
        # subsidy_cutoff = math.floor(len(subsidised_distributions) * 0.66) # get the bottom third of the distribution cutoff point
        # subsidised_distributions = subsidised_distributions[subsidy_cutoff:] # get the bottom third of the distribution
        for distribution in subsidised_distributions:
            if distribution.rollout_costs[strategy_tech] < telco_match_funding:
                subsidy_required_per_distribution_point = distribution.rollout_costs[strategy_tech] - distribution.rollout_benefits[strategy_tech]
                telco_match_funding -= distribution.rollout_costs[strategy_tech]
                distribution.rollout_costs[strategy_tech] = distribution.rollout_costs[strategy_tech] + subsidy_required_per_distribution_point               
                built_interventions.append((distribution.id, 'subsidised_{}'.format(strategy_tech), distribution.rollout_costs[strategy_tech]))
                match_funding_spend.append((distribution.id, strategy_policy, distribution.rollout_costs[strategy_tech]))
                subsidised_spend.append((distribution.id, strategy_policy, distribution.rollout_costs[strategy_tech], subsidy_required_per_distribution_point))
                premises_passed += len(distribution._clients)
            else:
                break

    else:
        print("'Strategy_policy not recognised. No upgrades built")

    return built_interventions, budget, spend, match_funding_spend, subsidised_spend