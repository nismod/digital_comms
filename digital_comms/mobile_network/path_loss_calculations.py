"""Calculate path loss 
"""

import numpy as np
from math import pi

def path_loss_calc_module(frequency, distance, ant_height, ant_type, building_height, street_width, 
                            settlement_type, type_of_sight, ue_height):

    """Calculate the correct path loss given a range of critera

    Parameters
    ----------
    frequency : float
        Frequency band given in GHz (f)
    distance : float
        Distance between the transmitter and receiver (d)
    ant_height:
        Height of the antenna (hBS)
    ant_type : string
        Indicates the type of cell (hotspot, micro, macro)
    settlement_type : string
        Gives the type of settlement (urban, suburban or rural) 
    type_of_sight : string
        Indicates whether the path is (Non) Line of Sight (LOS or NLOS) 
    ue_height : float
        Height of the User Equipment (hUT)
    street_width : float
        Width of street (W)

    Returns
    -------
    float: path_loss (dB)

    """
    #######################
    # check frequency
    #######################

    if 2 < frequency < 6: 
        pass
    else:
        print("frequency is NOT within correct range")
    
    #######################
    # calc breakpoint dist (d'BP)
    #######################

    #d’BP  = 4 h’BS h’UT fc/c, where fc is the centre frequency in Hz, c = 3.0108 m/s 
    #f is in Hz and c is the speed of light (3*10^8)
    breakpoint_urban = 4 * ant_height * ue_height * (int(frequency*1000000000)) / 300000000

    #dBP  = 2π hBS hUT fc/c, where fc is the centre frequency in Hz, c = 3.0108 m/s  
    #f is in Hz and c is the speed of light (3*10^8)
    breakpoint_suburban_rural = 2 * pi * ant_height * ue_height * (int(frequency*1000000000)) / 300000000

    #######################
    # set applicability function
    #######################

    def check_applicability(building_height, street_width, ant_height, ue_height):
        if 5 <= building_height < 50 : 
            building_height_compliant = True
        else:
            building_height_compliant = False
            print('building_height not compliant')
        if 5 <= street_width < 50:
            street_width_compliant = True
        else:
            street_width_compliant = False
            print('street_width not compliant')
        if 10 <= ant_height < 150:
            ant_height_compliant = True
        else:
            ant_height_compliant = False
            print('ant_height not compliant')
        if 1 <= ue_height < 10:
            ue_height_compliant = True
        else:
            ue_height_compliant = False 
            print('ue_height not compliant')

        if (building_height_compliant + street_width_compliant +
        ant_height_compliant + ue_height_compliant) == 4:
            overall_compliant = True    
        else:
            overall_compliant = False

        return overall_compliant

    #######################
    # indoor hotspot
    #######################
    
    #pass

    #######################
    # micro cells
    #######################

    if ant_type == 'micro' and settlement_type == 'urban' and type_of_sight == 'los': 
        if distance < breakpoint_urban:
            path_loss = 22 * np.log10(distance) + 28 + 20*np.log10(frequency)
        elif breakpoint_urban < distance < 5000:
            path_loss = 40 * np.log10(distance) + 7.8 - 18*np.log10(ant_height) - 18*np.log10(ue_height) + 2*np.log10(frequency)
        else:
            print("distance is out of cell range at {}m".format(distance))
            #fallback value needs refining
            path_loss = 100

    if ant_type == 'micro' and settlement_type == 'urban' and type_of_sight == 'nlos':  
        path_loss = (36.7*np.log10(distance) + 22.7 + 26*np.log10(frequency))
        
    # add outside-to-inside calculations for urban microcell

    #######################
    # macro cells
    #######################

    if ant_type == 'macro' and settlement_type == 'urban' and type_of_sight == 'los': 
        if 10 < distance < breakpoint_urban:
            path_loss = 22 * np.log10(distance) + 28 + 20*np.log10(frequency)
        elif breakpoint_urban < distance < 5000:
            path_loss = (40*np.log10(distance) + 7.8 - 18*np.log10(ant_height) - 
                        18*np.log10(ue_height) + 2*np.log10(frequency))
        else:
            print("distance is out of cell range at {}m".format(distance))
            #fallback value needs refining
            path_loss = 100

    if ant_type == 'macro' and settlement_type == 'urban' and type_of_sight == 'nlos':
        
        if (10 < distance < 5000 and check_applicability(building_height, street_width, ant_height, ue_height)):

            path_loss = (161.04-7.1*np.log10(street_width)+ 7.5*np.log10(building_height)-(24.37-3.7*
                    (building_height/ant_height)**2)*np.log10(ant_height)+(43.42-3.1*
                    np.log10(ant_height))*(np.log10(distance)-3)+ 20*np.log10(frequency)-
                    (3.2*(np.log10(11.75*ue_height))**2-4.97))
        else:
            print("parameters not in 3GPP applicability ranges")
            #fallback value needs refining
            path_loss = 100

    if ant_type == 'macro' and settlement_type != 'urban' and type_of_sight == 'los':
     
        def suburban_los_pl1(input_distance): 

            pl1 = (20*np.log10(40*pi*input_distance*frequency/3) + min(0.03*building_height**1.72,10) * 
            np.log10(input_distance) - min(0.044*building_height**1.72, 14.77) + 
            0.002*np.log10(building_height)*input_distance)

            return pl1

        def suburban_los_pl2(input_distance):

            pl2 =  40*np.log10(input_distance / breakpoint_suburban_rural)

            return pl2

        if (10 < distance < breakpoint_suburban_rural and 
        check_applicability(building_height, street_width, ant_height, ue_height)):

            path_loss = suburban_los_pl1(distance)

        elif (breakpoint_suburban_rural < distance < 5000 and 
        check_applicability(building_height, street_width, ant_height, ue_height)):
            
            pl1 = suburban_los_pl1(breakpoint_suburban_rural)
            path_loss = pl1 + suburban_los_pl2(distance)

        else:
            print("parameters not in 3GPP applicability ranges")
            #fallback value needs refining
            path_loss = 100

    if ant_type == 'macro' and settlement_type != 'urban' and type_of_sight == 'nlos':

        path_loss = (161.04-7.1*np.log10(street_width)+ 7.5*np.log10(building_height)-(24.37-3.7*
                    (building_height/ant_height)**2)*np.log10(ant_height)+(43.42-3.1*
                    np.log10(ant_height))*(np.log10(distance)-3)+ 20*np.log10(frequency)-
                    (3.2*(np.log10(11.75*ue_height))**2-4.97))
    
    return round(path_loss,0)