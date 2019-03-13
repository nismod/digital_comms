
"""Decide who adopts
"""
from logging import getLogger


LOGGER = getLogger(__name__)

def update_adoption_desirability(system, annual_adoption_rate):
    """
    Given adoption parameters and a premises, return likely adoptees

    scenario - scenario name
    number_of_adopters - aggregate number wanting to adopt
    premises - premises objects
    timestep - year

    1) access list of wta for all premises
    2) rank premises based on wta
    3) select top n % of premises in ranking
    4) if premises in top n % adoption_desirability = True

    """

    distributions_not_wanting_to_adopt = [
        distribution for distribution in system._distributions
        if distribution.adoption_desirability is not True
    ]

    distributions_already_wanting_to_adopt = [
        distribution for distribution in system._distributions
        if distribution.adoption_desirability is True
    ]

    #rank distributions based on household wta
    distributions_not_wanting_to_adopt = sorted(
        distributions_not_wanting_to_adopt, key=lambda item: item.wta)
    
    #get total premises needing to be served in current system
    total_premises = 0
    for distribution in system._distributions:
        total_premises += distribution.total_prems

    raw_annual_premises_adoption = round(total_premises*(annual_adoption_rate/100))
    
    new_distributions_wanting_to_adopt = []
    premises_wanting_to_adopt = 0
    for distribution in system._distributions:
        if premises_wanting_to_adopt + distribution.total_prems <= raw_annual_premises_adoption:
            new_distributions_wanting_to_adopt.append(distribution)
            premises_wanting_to_adopt += distribution.total_prems
        else:
            break

    LOGGER.debug("-- premises not wanting to connect %s", 
        len([dist.total_prems for dist in distributions_not_wanting_to_adopt]))
    LOGGER.debug("-- premises wanting to connect %s", 
        sum([dist.total_prems for dist in new_distributions_wanting_to_adopt]))
    LOGGER.debug("-- total premises %s",
        sum([dist.total_prems for dist in distributions_already_wanting_to_adopt]) + 
        sum([dist.total_prems for dist in distributions_not_wanting_to_adopt]))

    distribution_adoption = []

    #cycle through number of premises
    for distribution in new_distributions_wanting_to_adopt:

        #turn adoption_desirability to True
        distribution.adoption_desirability = True

        #append adopted premises to list
        distribution_adoption.append((distribution.id, distribution.adoption_desirability))

    return distribution_adoption
