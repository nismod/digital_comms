"""Calculate path loss
"""

import numpy as np
from math import pi

def path_loss_calculator(frequency, distance, ant_height, ant_type, building_height, street_width,
                            settlement_type, type_of_sight, ue_height, above_roof):

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

    if frequency <= 2:
        free_space_path_loss = free_space(
            frequency, distance, ant_height, ue_height
        )

        extended_hata_path_loss = extended_hata(
            frequency, distance, ant_height, ant_type, building_height, street_width,
            settlement_type, type_of_sight, ue_height, above_roof
        )

        if extended_hata_path_loss < free_space_path_loss:
            path_loss = free_space_path_loss
        else:
            path_loss = extended_hata_path_loss

    if 2 <= frequency < 6:
        path_loss = e_utra_3gpp_tr36_814(
            frequency, distance, ant_height, ant_type, building_height,
            street_width, settlement_type, type_of_sight, ue_height
        )

    else:
        raise ValueError (
            "frequency of {} is NOT within correct range of 2-6 GHz".format(frequency)
        )

    return path_loss

def free_space(frequency, distance, ant_height, ue_height):
    """Implements the free space attentuation path loss model.

    Parameters
    ----------
    f : int
        Carrier band (f) required in MHz.
    d : int
        Distance (d) between transmitter and receiver (km).
    h1 : int
        Transmitter antenna height (ant_height) (m, above ground).
    h2 : int
        Receiver antenna height (ue_height) (m, above ground).
    sigma : int
        Variation in path loss (dB) which is 2.5dB for free space.

    """
    #model requires frequency in MHz rather than GHz.
    frequency = frequency*1000
    #model requires distance in kilometers rather than meters.
    distance = distance/1000

    random_variation = generate_log_normal_dist_value(0,2.5,1)

    path_loss = (
        32.4 + 10*np.log10((((ant_height - ue_height)/1000)**2 + \
        distance**2)) + (20*np.log10(frequency) + random_variation)
    )

    return round(path_loss)

def extended_hata(frequency, distance, ant_height, ant_type, building_height,
    street_width, settlement_type, type_of_sight, ue_height, above_roof):
    """Implements the Extended Hata attentuation path loss model.

    Parameters
    ----------
    f : int
        Carrier band (f) required in MHz
    h1 : int
        Transmitter antenna height (m, above ground)
    h2 : int
        Receiver antenna height (m, above ground)
    d : int
        Distance (d) between transmitter and receiver (km)
    env : string
        General environment
    L : int
        Median path loss (dB)
    sigma : int
        Variation in path loss (dB)

    """
    #model requires frequency in MHz rather than GHz.
    frequency = frequency*1000
    #model requires distance in kilometers rather than meters.
    distance = distance/1000
    print('distance is {}'.format(distance))
    #find smallest value
    hm = min(ant_height, ue_height)
    #find largest value
    hb = max(ant_height, ue_height)
    print('hm is {}'.format(hm))
    print('hb is {}'.format(hb))
    alpha_hm = round((1.1*np.log(frequency) - 0.7) * min(10, hm) - \
        (1.56*np.log(frequency) - 0.8) + max(0, (20*np.log(hm/10))))

    beta_hb = round(min(0, (20*np.log(hb/30))))
    print('alpha_hm is {}'.format(alpha_hm))
    print('beta_hb is {}'.format(beta_hb))

    if distance <= 20: #units : km
        alpha_exponent = 1
    elif 20 < distance < 100: #units : km
        alpha_exponent = 1 + (0.14 + 1.87*10**-4 * frequency + 1.07*10**-3 * hb)*(np.log(distance/20))**0.8
    else:
        raise ValueError('Distance over 100km not compliant')

    if distance > 0.1:

        if 30 < frequency <= 150:

            path_loss = round((
                69.6 + 26.2*np.log(150) - 20*np.log(150/frequency) -
                13.82*np.log(max(30, hb)) +
                (44.9 - 6.55*np.log(max(30, hb))) *
                (np.log(distance))**alpha_exponent - alpha_hm - beta_hb
            ))
            
        elif 150 < frequency <= 1500:

            path_loss = round((
                69.6 + 26.2*np.log(frequency) -
                13.82*np.log(max(30, hb)) +
                (44.9 - 6.55*np.log(max(30, hb))) *
                (np.log(distance))**alpha_exponent - alpha_hm - beta_hb
            ))
            print('150-1500MHz path_loss is {}'.format(path_loss))
        elif 1500 < frequency <= 2000:

            path_loss = round((
                46.3 + 33.9*np.log(frequency) -
                13.82*np.log(max(30, hb)) +
                (44.9 - 6.55*np.log(max(30, hb))) *
                (np.log(distance))**alpha_exponent - alpha_hm - beta_hb
            ))
            print('1500-2000MHz path_loss is {}'.format(path_loss))
        elif 2000 < frequency <= 3000:

            path_loss = round((
                46.3 + 33.9*np.log(2000) +
                10*np.log(frequency/2000) -
                13.82*np.log(max(30, hb)) +
                (44.9 - 6.55*np.log(max(30, hb))) *
                (np.log(distance))**alpha_exponent - alpha_hm - beta_hb
            ))
            print('2000-3000MHz path_loss is {}'.format(path_loss))
        else:
            raise ValueError('Carrier frequency incorrect for Extended HATA')

        if settlement_type == 'suburban':

            path_loss = round((
                path_loss - 2 * \
                (np.log((min(max(150, frequency), 2000)/28)))**2 - 5.4
            ))
            print('Suburban path_loss is {}'.format(path_loss))
        elif settlement_type == 'rural': #also called 'open area'
            print('Pre path_loss is {}'.format(path_loss))
            path_loss = round((
                path_loss - 4.78 * \
                (np.log(min(max(150, frequency), 2000)))**2 + 18.33 * \
                    np.log(min(max(150, frequency), 2000)) - 40.94
            ))
            print('Rural path_loss is {}'.format(path_loss))

        else:
            pass

    elif distance < 0.04:
        
        path_loss = (
            32.4 + (20*np.log(frequency)) + (10*np.log((distance**2) +    
            ((hb - hm)**2) / (10**6)))
        )

    elif 0.04 <= distance < 0.1:

        #distance set at 0.1
        l_fixed_distance_upper = (
            32.4 + (20*np.log(frequency)) + (10*np.log(0.1**2 +
            (hb - hm)**2 / 10**6))
        )

        #distance set at 0.04
        l_fixed_distance_lower = (
            32.4 + (20*np.log(frequency)) + (10*np.log(0.04**2 +
            (hb - hm)**2 / 10**6))
        )

        path_loss = (l_fixed_distance_lower +
            (np.log(distance) - np.log(0.04) / \
            (np.log(0.1) - np.log(0.04))) *
            (l_fixed_distance_upper - l_fixed_distance_lower)
        )

        path_loss = (l_fixed_distance_lower + \
            (np.log(distance) - np.log(0.04) / \
            (np.log(0.1) - np.log(0.04))) *
            (l_fixed_distance_upper - l_fixed_distance_lower)
        )
        print(path_loss)

    else:
        raise ValueError('Distance over 100km not compliant')

    #determine variation in path loss using stochastic component
    if distance < 0.04:
        
        path_loss = path_loss + generate_log_normal_dist_value(0,3.5,1)

    elif 0.04 < distance < 0.1:

        if above_roof == 1:
            print(path_loss)
            sigma = (3.5 + ((12-3.5)/0.1-0.04) * (distance - 0.04))
            random_quantity = generate_log_normal_dist_value(0,sigma,1)
            path_loss = (
                path_loss + random_quantity 
            )
            print(sigma)
            print(path_loss)
            
        elif above_roof == 0:
            random_quantity = generate_log_normal_dist_value(0,3.5,1)
            path_loss = (
                path_loss + random_quantity +
                ((17-3.5)/0.1-0.04) * (distance - 0.04)
            )
        else:
            raise ValueError('Could not determine if cell is above or below roof line')

    elif 0.1 < distance <= 0.2:

        if above_roof == 1:

            random_quantity = generate_log_normal_dist_value(0,12,1)
            print(generate_log_normal_dist_value(0,12,1))
            path_loss = (
                path_loss + random_quantity
            )

        elif above_roof == 0:

            random_quantity = generate_log_normal_dist_value(0,17,1)
            print(generate_log_normal_dist_value(0,17,1))
            path_loss = (
                path_loss + random_quantity
            )

        else:
            raise ValueError('Could not determine if cell is above or below roof line')

    elif 0.2 < distance <= 0.6:
        if above_roof == 1:
            print(path_loss)
            sigma = (12 + ((9-12)/0.6-0.2) * (distance - 0.02))
            random_quantity = generate_log_normal_dist_value(0,sigma,1)
            path_loss = (
                path_loss + random_quantity 
            )
            print(sigma)
            print(path_loss)

        elif above_roof == 0:
            print(path_loss)
            sigma = (17 + ((9-17)/0.6-0.2) * (distance - 0.02))
            random_quantity = generate_log_normal_dist_value(0,sigma,1)
            path_loss = (
                path_loss + random_quantity
            )
            print(random_quantity)
            print(path_loss)
        else:
            raise ValueError('Could not determine if cell is above or below roof line')

    elif 0.6 < distance:
            random_quantity = generate_log_normal_dist_value(0,12,1)
            path_loss = (
                path_loss + random_quantity
            )

    else:
        raise ValueError('Did not recognise distance')

    return round(path_loss)

def e_utra_3gpp_tr36_814(frequency, distance, ant_height, ant_type, building_height,
    street_width, settlement_type, type_of_sight, ue_height):
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

    check_applicability(building_height, street_width, ant_height, ue_height)

    #######################
    # indoor hotspot
    #######################

    #pass

    #######################
    # micro cells
    #######################

    if ant_type == 'micro' and settlement_type == 'urban' and type_of_sight == 'los':
        if distance < breakpoint_urban:
            path_loss = 22 * np.log10(distance) + 28 + 20*np.log10(frequency) + generate_log_normal_dist_value(0,3,1)
        elif breakpoint_urban < distance < 5000:
            path_loss = 40 * np.log10(distance) + 7.8 - 18*np.log10(ant_height) - 18*np.log10(ue_height) + 2*np.log10(frequency) + generate_log_normal_dist_value(0,3,1)
        else:
            print("distance is out of cell range at {}m".format(distance))
            #fallback value needs refining
            path_loss = 250

    elif ant_type == 'micro' and settlement_type == 'urban' and type_of_sight == 'nlos':
        path_loss = (36.7*np.log10(distance) + 22.7 + 26*np.log10(frequency)) + generate_log_normal_dist_value(0,4,1)

    # add outside-to-inside calculations for urban microcell

    #######################
    # macro cells
    #######################

    elif ant_type == 'macro' and settlement_type == 'urban' and type_of_sight == 'los':
        if 10 < distance < breakpoint_urban:
            path_loss = 22 * np.log10(distance) + 28 + 20*np.log10(frequency) + generate_log_normal_dist_value(0,4,1)
        elif breakpoint_urban < distance < 5000:
            path_loss = (40*np.log10(distance) + 7.8 - 18*np.log10(ant_height) -
                        18*np.log10(ue_height) + 2*np.log10(frequency)) + generate_log_normal_dist_value(0,4,1)
        else:
            print("distance is out of cell range at {}m".format(distance))
            #fallback value needs refining
            path_loss = 250

    elif ant_type == 'macro' and settlement_type == 'urban' and type_of_sight == 'nlos':

        if (10 < distance < 5000 and check_applicability(building_height, street_width, ant_height, ue_height)):
            path_loss = (161.04-7.1*np.log10(street_width)+ 7.5*np.log10(building_height)-(24.37-3.7*
                    (building_height/ant_height)**2)*np.log10(ant_height)+(43.42-3.1*
                    np.log10(ant_height))*(np.log10(distance)-3)+ 20*np.log10(frequency)-
                    (3.2*(np.log10(11.75*ue_height))**2-4.97)) + generate_log_normal_dist_value(0,6,1)
        else:
            print("parameters not in 3GPP applicability ranges")
            #fallback value needs refining
            path_loss = 250

    elif ant_type == 'macro' and settlement_type != 'urban' and type_of_sight == 'los':

        def suburban_los_pl1(input_distance):

            pl1 = (20*np.log10(40*pi*input_distance*frequency/3) + min(0.03*building_height**1.72,10) *
            np.log10(input_distance) - min(0.044*building_height**1.72, 14.77) +
            0.002*np.log10(building_height)*input_distance) + generate_log_normal_dist_value(0,4,1)

            return pl1

        def suburban_los_pl2(input_distance):

            pl2 =  40*np.log10(input_distance / breakpoint_suburban_rural) + generate_log_normal_dist_value(0,6,1)

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
            path_loss = 250

    elif ant_type == 'macro' and settlement_type != 'urban' and type_of_sight == 'nlos':

        if (10 < distance < 5000 and
            check_applicability(building_height, street_width, ant_height, ue_height)):

            path_loss = (161.04-7.1*np.log10(street_width)+ 7.5*np.log10(building_height)-(24.37-3.7*
                        (building_height/ant_height)**2)*np.log10(ant_height)+(43.42-3.1*
                        np.log10(ant_height))*(np.log10(distance)-3)+ 20*np.log10(frequency)-
                        (3.2*(np.log10(11.75*ue_height))**2-4.97)) +  generate_log_normal_dist_value(0,8,1)
        elif distance <= 10:
            pass

        else:
            print("parameters not in 3GPP applicability ranges")
            #fallback value needs refining
            path_loss = 250

    else:
        raise ValueError('Did not recognise parameter combination')

    return round(path_loss)

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

def generate_log_normal_dist_value(mu, sigma, draws):
    """
    Generates random values using a lognormal distribution, given a specific mean (mu) and standard deviation (sigma).
    """
    np.random.seed(42)
    s = np.random.lognormal(mu, sigma, draws)

    return int(round(s[0]))
