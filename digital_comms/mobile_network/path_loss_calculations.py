"""Calculate path loss 
"""

import numpy as np

def path_loss_calc_module(frequency, distance, ant_height, ant_type, settlement_type, type_of_sight, ue_height):

    """Calculate the correct path loss given a range of critera

    Parameters
    ----------
    frequency : float
        Frequency band given in GHz
    distance : float
        Distance between the transmitter and receiver
    ant_height:
        Height of the antenna
    ant_type : string
        Indicates the type of cell (hotspot, micro, macro)
    settlement_type : string
        Gives the type of settlement (urban, suburban or rural) 
    type_of_sight : string
        Indicates whether the path is (Non) Line of Sight (LOS or NLOS) 
    ue_height : float
        Height of the User Equipment

    Returns
    -------
    float: path_loss (dB)

    """

    if 2 < frequency < 6: 
        pass
    else:
        print("frequency is NOT within correct range")

    if ant_type == 'macro' and settlement_type == 'urban' and type_of_sight == 'los':

        path_loss = (40*np.log10(distance) + 7.8-18*np.log10(ant_height) - 18*np.log10(ue_height) + 2*np.log10(frequency))

    return round(path_loss,2)