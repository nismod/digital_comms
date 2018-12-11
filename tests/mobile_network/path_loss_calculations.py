"""Test Path Loss Calculations
"""

from digital_comms.mobile_network.path_loss_calculations import path_loss_calc_module

class TestPathLossCalcModule():

    def test_path_loss_module(self):

        frequency = 3.5 #in GHz
        distance = 1000 #in meters
        ant_height = 25 #in meters
        ant_type = 'macro'
        settlement_type = 'urban'
        type_of_sight = 'los'
        ue_height = 1.5

        path_loss = round(path_loss_calc_module(frequency, distance, ant_height, ant_type, settlement_type, type_of_sight, ue_height),0)

        assert path_loss == 101


