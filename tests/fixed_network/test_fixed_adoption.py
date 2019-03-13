"""Skeleton test
"""
from digital_comms.fixed_network.adoption import update_adoption_desirability

def test_pass():
    """Always pass
    """
    pass

def test_update_adoption_desirability(setup_system, setup_annual_adoption_rate):
    """ update_adoption_desirability takes the system and annual adoption rate,
    returning a list of tuples, with each tuple consisting of:
    - distribution.id, distribution.adoption_desirability

    To test:
        Give function test data which contains:
        - 5 distribution points
        - 100 premises

    """
    assert len(assets['exchanges']) == len(setup_system.assets['exchanges'])


