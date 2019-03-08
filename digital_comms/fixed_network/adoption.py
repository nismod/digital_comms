
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
    #rank premises based on household wta
    distributions_not_wanting_to_adopt = sorted(
        distributions_not_wanting_to_adopt, key=lambda item: item.wta)

    #get number of premises to select = convert adopt rate into raw premises
    to_adopt = (len(system._distributions) * annual_adoption_rate) / 100

    #select number of premises ready to adopt
    new_distributions_wanting_to_adopt = distributions_not_wanting_to_adopt[1:int(to_adopt)]

    LOGGER.debug("-- distributions not wanting to connect %s", len(distributions_not_wanting_to_adopt))
    LOGGER.debug("-- distributions wanting to connect %s", len(new_distributions_wanting_to_adopt))
    LOGGER.debug("-- total distributions %s",
                 len(distributions_already_wanting_to_adopt) + len(distributions_not_wanting_to_adopt))

    distribution_adoption = []

    #cycle through number of premises
    for distribution in new_distributions_wanting_to_adopt:

        #turn adoption_desirability to True
        distribution.adoption_desirability = True

        #append adopted premises to list
        distribution_adoption.append((distribution.id, distribution.adoption_desirability))

    return distribution_adoption
