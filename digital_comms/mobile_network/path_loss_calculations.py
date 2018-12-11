"""Calculate path loss 
"""

import numpy as np
from math import pi

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
    street_width : float
        Width of street

    Returns
    -------
    float: path_loss (dB)

    """

    #check the frequency band is within necessary range
    if 2 < frequency < 6: 
        pass
    else:
        print("frequency is NOT within correct range")

    street_width = 10
    ave_building_height = 20
    
    if ant_type == 'macro' and settlement_type == 'urban' and type_of_sight == 'los':

        path_loss = (40*np.log10(distance) + 7.8-18*np.log10(ant_height) - 18*np.log10(ue_height) + 2*np.log10(frequency))

    if ant_type == 'macro' and settlement_type == 'urban' and type_of_sight == 'nlos':
 
        path_loss = (161.04-7.1*np.log10(street_width)+ 7.5*np.log10(ave_building_height)-(24.37-3.7*
                    (ave_building_height/ant_height)**2)*np.log10(ant_height)+(43.42-3.1*
                    np.log10(ant_height))*(np.log10(distance)-3)+ 20*np.log10(frequency)-
                    (3.2*(np.log10(11.75*ue_height))**2-4.97))

    if ant_type == 'macro' and settlement_type == 'suburban' and type_of_sight == 'los':

        path_loss = (20*np.log10(40*pi*distance*frequency/3) + min(0.03*ave_building_height**1.72,10)*log10(distance) - min(0.044*(ave_building_height**1.72, 14.77)+0.002*log10(ave_building_height)*distance))

    return round(path_loss,0)