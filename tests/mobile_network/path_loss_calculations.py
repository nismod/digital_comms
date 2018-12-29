"""Test Path Loss Calculations
"""

import pytest
from digital_comms.mobile_network.path_loss_calculations import path_loss_calc_module, check_applicability

@pytest.mark.parametrize("frequency, distance, ant_height, ant_type, building_height, street_width, settlement_type, type_of_sight, ue_height, expected", [
    (3.5,500,10,'micro','-','-','urban','los',1.5, 98),
    (3.5,1000,10,'micro','-','-','urban','los',1.5, 108),
    (3.5,500,10,'micro','-','-','urban','nlos',1.5, 136),
    (3.5,500,25, 'macro',20,20,'urban','los',1.5, 98),
    (3.5,2000,25,'macro',20,20,'urban','los',1.5, 113),
    (3.5,1000,25,'macro',20,20,'urban','nlos',1.5, 142),
    (3.5,1000,35,'macro',10,20,'suburban','los',1.5, 108),
    (3.5,4000,35,'macro',10,20,'suburban','los',1.5, 127),
    (3.5,500,35,'macro',10,20,'suburban','nlos',1.5, 121),
    (3.5,1000,35,'macro',10,20,'rural','los',1.5, 108),
    (3.5,4000,35,'macro',10,20,'rural','los',1.5, 127),
    (3.5,500,35,'macro',10,20,'rural','nlos',1.5, 121),
])

def test_eval_path_loss_calc(frequency, distance, ant_height, ant_type, building_height, street_width, settlement_type, type_of_sight, ue_height, expected):
    assert (path_loss_calc_module(frequency, distance, ant_height, ant_type, building_height, street_width, settlement_type, type_of_sight, ue_height)) == expected

@pytest.mark.parametrize("building_height, street_width, ant_height, ue_height, expected", [
    (20, 20, 20, 1.5, True),
    (5, 20, 8, 1.5, False), ])
 
def test_eval_applicability(building_height, street_width, ant_height, ue_height, expected):
    assert (check_applicability(building_height, street_width, ant_height, ue_height)) == expected

