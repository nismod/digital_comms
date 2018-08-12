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

AVAILABLE_STRATEGY_INTERVENTIONS = {
    # Intervention Strategy 1
    # Minimal Intervention 'Do Nothing Scenario'
    # Build no more additional fibre 
    'minimal': (),

    # Intervention Strategy 2
    'FTTP_most_beneficial_distributions': (),

    # Intervention Strategy 3.
    'FTTP_most_beneficial_cabinets': (),

    # Intervention Strategy 2
    'FTTDP_most_beneficial_distributions': (),

    # Intervention Strategy 3.
    'FTTDP_most_beneficial_cabinets': (),
}

def decide_interventions(strategy, budget, service_obligation_capacity,
                         system, timestep, adoption_cap):
    """Given strategy parameters and a system return some next best intervention
    """

    # Build to meet demand most beneficial demand
    built, budget, spend = meet_most_beneficial_demand(
        budget, strategy, timestep, system, adoption_cap)

    return built, budget, spend

def meet_most_beneficial_demand(budget, available_interventions, timestep, system, adoption_cap):
    return _suggest_interventions(
        budget, available_interventions, system, timestep, adoption_cap)


def _suggest_interventions(budget, strategy, system, timestep, adoption_cap, threshold=None):
    built_interventions = []
    spend = []
    premises_passed = 0
    if strategy == 'rollout_fttp_per_distribution':
        distributions = sorted(system._distributions, key=lambda item: True if item.rollout_bcr['fttp'] > 1 == 0 else False, reverse=True)
        for distribution in distributions:
            if (premises_passed + len(distribution._clients)) < adoption_cap:
                if distribution.rollout_costs['fttp'] < budget:
                    budget -= distribution.rollout_costs['fttp']
                    built_interventions.append((distribution.id, 'rollout_fttp', distribution.rollout_costs['fttp']))
                    spend.append((distribution.id, strategy, distribution.rollout_costs['fttp']))
                    premises_passed += len(distribution._clients)
                else:
                    break
            else:
                break

    # elif strategy == 'rollout_fttp_per_cabinet':
    #     cabinets = sorted(system._cabinets, key=lambda item: item.rollout_bcr['fttp'], reverse=True)

    #     for cabinet in cabinets:

    #         if cabinet.rollout_costs['fttp'] < budget:
    #             budget -= cabinet.rollout_costs['fttp']
    #             built_interventions.append((cabinet.id, 'rollout_fttp', cabinet.rollout_costs['fttp']))
    #             spend.append((cabinet.id, strategy, cabinet.rollout_costs['fttp']))
    #         else:
    #             break

    # elif strategy == 'rollout_fttdp_per_distribution':
    #     distributions = sorted(system._distributions, key=lambda item: item.rollout_bcr['fttdp'], reverse=True)

    #     for distribution in distributions:

    #         if distribution.rollout_costs['fttdp'] < budget:
    #             budget -= distribution.rollout_costs['fttdp']
    #             built_interventions.append((distribution.id, 'rollout_fttdp', distribution.rollout_costs['fttdp']))
    #             spend.append((distribution.id, strategy, distribution.rollout_costs['fttdp']))
    #         else:
    #             break

    # elif strategy == 'rollout_fttdp_per_cabinet':
    #     cabinets = sorted(system._cabinets, key=lambda item: item.rollout_bcr['fttdp'], reverse=True)

    #     for cabinet in cabinets:

    #         if cabinet.rollout_costs['fttdp'] < budget:
    #             budget -= cabinet.rollout_costs['fttdp']
    #             built_interventions.append((cabinet.id, 'rollout_fttdp', cabinet.rollout_costs['fttdp']))
    #             spend.append((cabinet.id, strategy, cabinet.rollout_costs['fttdp']))
    #         else:
    #             break

    return built_interventions, budget, spend