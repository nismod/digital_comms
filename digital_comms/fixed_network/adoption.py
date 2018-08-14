"""Decide who adopts
"""
################################################################
# Decide who adopts
################################################################

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

    non_adopted_premises = [
        premise
        for premise in system._premises
        if not premise.adoption_desirability
    ]

    #rank premises based on household wta
    non_adopted_premises = sorted(non_adopted_premises, key=lambda item: item.wta)

    #get number of premises to select = convert adopt rate into raw premises
    to_adopt = len(system._premises) * annual_adoption_rate / 100

    #select number of premises ready to adopt
    premises_to_be_adopting = non_adopted_premises[1:int(to_adopt)]

    premises_adoption = []

    #cycle through number of premises
    for premises in premises_to_be_adopting:

        #turn adoption_desirability to True
        premises.adoption_desirability = True

        #append adopted premises to list
        premises_adoption.append((premises.id, premises.adoption_desirability))

    return premises_adoption
