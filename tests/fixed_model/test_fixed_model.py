import pytest
import os

from digital_comms.fixed_model.fixed_model import ICTManager

def test_init(setup_fixed_network, assets, links):

    assert len(assets['premises']) == len(setup_fixed_network.assets['premises'])
    assert len(assets['distributions']) == len(setup_fixed_network.assets['distributions'])
    assert len(assets['cabinets']) == len(setup_fixed_network.assets['cabinets'])
    assert len(assets['exchanges']) == len(setup_fixed_network.assets['exchanges'])

        
