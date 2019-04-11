import pytest
import os
import numpy as np

from digital_comms.mobile_network.transmitter_module import (
    read_postcode_sector,
    get_local_authority_ids,
    get_transmitters,
    generate_receivers,
    NetworkManager,
    find_and_deploy_new_transmitter,
    randomly_select_los,
    transform_coordinates
    )

@pytest.fixture
def get_postcode_sector():

   yield read_postcode_sector('CB11')

@pytest.fixture
def base_system(get_postcode_sector):

    TRANSMITTERS = [
            {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [544655.1049227581, 259555.22477912105],
            },
            'properties': {
                "operator":'voda',
                "opref": 31742,
                "sitengr": 'TL4454059600',
                "ant_height": 14.9,
                "type": 'macro',
                "power": 40,
                "gain": 20,
                "losses": 2,
                "pcd_sector": "CB1 2",
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [545265.1768673284, 259655.21841664566]
            },
            'properties': {
                "operator":'voda',
                "opref": 46497,
                "sitengr": 'TL4515059700',
                "ant_height": 13.7,
                "type": 'macro',
                "power": 40,
                "gain": 20,
                "losses": 2,
                "pcd_sector": "CB1 1",
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [545285.5165949427, 259483.84577720467],
            },
            'properties': {
                "operator":'voda',
                "opref": 31746,
                "sitengr": 'TL4529059480',
                "ant_height": 14.9,
                "type": 'macro',
                "power": 40,
                "gain": 20,
                "losses": 2,
                "pcd_sector": "CB1 2",
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [545885.2027838879, 259595.2986071491]
            },
            'properties': {
                "operator":'voda',
                "opref": 31745,
                "sitengr": 'TL4577059640',
                "ant_height": 14.9,
                "type": 'macro',
                "power": 40,
                "gain": 20,
                "losses": 2,
                "pcd_sector": "CB1 2",
            }
        }
    ]

    RECEIVERS = [
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [544750.2222151064, 259926.76048813056]
            },
            'properties': {
                "ue_id": "AB1",
                "sitengr": 'TL4454059600',
                "misc_losses": 4,
                "gain": 4,
                "losses": 4,
                "indoor": True,
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [544809.5557435964, 259520.0001617251]
            },
            'properties': {
                "ue_id": "AB3",
                "sitengr": 'TL4454059600',
                "misc_losses": 4,
                "gain": 4,
                "losses": 4,
                "indoor": True,
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [544712.9242233046, 259378.04413438193]
            },
            'properties': {
                "ue_id": "AB2",
                "sitengr": 'TL4454059600',
                "misc_losses": 4,
                "gain": 4,
                "losses": 4,
                "indoor": True,
            }
        }
    ]

    system = NetworkManager(get_postcode_sector, TRANSMITTERS, RECEIVERS)

    return system

# def test_get_transmitters(get_postcode_sector):

#     actual_receivers = get_transmitters(get_postcode_sector)

#     assert len(actual_receivers) == 21

def test_generate_receivers(get_postcode_sector):

    postcode_sector_lut ={
        'postcode_sector': 'CB11',
        'indoor_probability': 100,
        'outdoor_probability': 0,
        'residential_count': 20,
        'non_residential_count': 20,
        'area': 200,
    }

    actual_receivers = generate_receivers(
        get_postcode_sector, postcode_sector_lut, 100
        )

    receiver_1 = actual_receivers[0]

    assert len(actual_receivers) == 100
    assert receiver_1['properties']['ue_id'] == 'id_0'
    assert receiver_1['properties']['misc_losses'] == 4
    assert receiver_1['properties']['gain'] == 4
    assert receiver_1['properties']['losses'] == 4
    assert receiver_1['properties']['indoor'] == True

def test_find_and_deploy_new_transmitter(base_system, get_postcode_sector):

    new_transmitter = find_and_deploy_new_transmitter(
        base_system.transmitters, 1, get_postcode_sector
        )

    expected_transmitter = [
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [545478.632082053, 259578.12093366645]
            },
            'properties': {
                    "operator": 'unknown',
                    "sitengr": '{new}{GEN1}',
                    "ant_height": 20,
                    "tech": 'LTE',
                    "freq": 700,
                    "type": 17,
                    "power": 30,
                    "gain": 18,
                    "losses": 2,
                }
        }
    ]

    assert len(new_transmitter) == 1
    assert new_transmitter == expected_transmitter

def test_network_manager(base_system):

    assert len(base_system.area) == 1
    assert len(base_system.transmitters) == 4
    assert len(base_system.receivers) == 3

def testassert_build_new_assets(base_system):

    build_this_transmitter = [
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [0.124896, 52.215965]
            },
            'properties': {
                    "operator": 'unknown',
                    "sitengr": '{new}{GEN1}',
                    "ant_height": 20,
                    "tech": 'LTE',
                    "freq": 700,
                    "type": 17,
                    "power": 30,
                    "gain": 18,
                    "losses": 2,
                }
        }
    ]

    base_system.build_new_assets(build_this_transmitter, 'CB11')

    assert len(base_system.transmitters) == 5

# def test_estimate_link_budget(base_system):

#     actual_result = base_system.estimate_link_budget(0.7, 10)

#     #find closest_transmitters
#     # <Receiver id:AB1>
#     # [<Transmitter id:TL4454059600>, <Transmitter id:TL4515059700>, <Transmitter id:TL4529059480>, <Transmitter id:TL4577059640>]
#     # <Receiver id:AB3>
#     # [<Transmitter id:TL4454059600>, <Transmitter id:TL4515059700>, <Transmitter id:TL4529059480>, <Transmitter id:TL4577059640>]
#     # <Receiver id:AB2>
#     # [<Transmitter id:TL4454059600>, <Transmitter id:TL4529059480>, <Transmitter id:TL4515059700>, <Transmitter id:TL4577059640>]

#     #find path_loss (self.calculate_path_loss)

#     # type_of_sight is nlos
#     # 0.7 383.56170453174326 20 macro 20 20 urban nlos 1.5 0
#     # 0.7 869 20 macro 20 20 urban nlos 1.5 0
#     # 0.7 961 20 macro 20 20 urban nlos 1.5 0
#     # 0.7 1856 20 macro 20 20 urban nlos 1.5 0
#     # type_of_sight is nlos
#     # 0.7 158.43465782386215 20 macro 20 20 urban nlos 1.5 0
#     # 0.7 753 20 macro 20 20 urban nlos 1.5 0
#     # 0.7 770 20 macro 20 20 urban nlos 1.5 0
#     # 0.7 1744 20 macro 20 20 urban nlos 1.5 0
#     # type_of_sight is nlos
#     # 0.7 186.39733937494557 20 macro 20 20 urban nlos 1.5 0
#     # 0.7 935 20 macro 20 20 urban nlos 1.5 0
#     # 0.7 943 20 macro 20 20 urban nlos 1.5 0
#     # 0.7 1915 20 macro 20 20 urban nlos 1.5 0

#     #find received_power (self.calc_received_power)

#     #find interference (self.calculate_interference)

#     #find noise

#     #find sinr (self.calculate_sinr)

#     #find (self.estimate_capacity)


#     expected_result = 0

#     assert expected_result == actual_result

def test_find_closest_available_transmitters(base_system):

    receiver = base_system.receivers['AB3']

    actual_result = base_system.find_closest_available_transmitters(receiver)

    actual_transmitter_ids = [t.id for t in actual_result]

    expected_result = ['TL4454059600', 'TL4515059700', 'TL4529059480', 'TL4577059640']

    assert actual_transmitter_ids == expected_result


def test_calculate_path_loss(base_system):

    #path_loss
    frequency = 0.7
    interference_strt_distance = 158
    ant_height = 20
    # ant_type = 'macro'
    # building_height = 20
    # street_width = 20
    # settlement_type = 'urban'
    # type_of_sight = 'nlos'
    ue_height = 1.5
    # above_roof = 0

    receiver = base_system.receivers['AB3']

    closest_transmitters = base_system.find_closest_available_transmitters(receiver)[0]

    actual_result = base_system.calculate_path_loss(closest_transmitters, receiver, frequency)

    #model requires frequency in MHz rather than GHz.
    frequency = frequency*1000
    #model requires distance in kilometers rather than meters.
    distance = interference_strt_distance/1000

    #find smallest value
    hm = min(ant_height, ue_height)
    #find largest value
    hb = max(ant_height, ue_height)

    alpha_hm = round((1.1*np.log(frequency) - 0.7) * min(10, hm) - \
        (1.56*np.log(frequency) - 0.8) + max(0, (20*np.log(hm/10))),3)

    beta_hb = round(min(0, (20*np.log(hb/30))),3)

    alpha_exponent = 1

    path_loss = round(
        69.6 + 26.2*np.log(frequency) -
        13.82*np.log(max(30, hb)) +
        (44.9 - 6.55*np.log(max(30, hb))) *
        (np.log(distance))**alpha_exponent - alpha_hm - beta_hb
    )

    #stochastic component for geometry/distance 4808
    #stochastic component for building penetration loss 8655567
    path_loss = path_loss + 4648 + 8655567

    assert actual_result == path_loss


def test_calc_received_power(base_system):

    receiver = base_system.receivers['AB3']

    closest_transmitters = base_system.find_closest_available_transmitters(receiver)[0]

    actual_received_power = base_system.calc_received_power(
        closest_transmitters,
        receiver,
        4808
        )

    #eirp = power + gain - losses
    #58 = 40 + 20 - 2
    #received_power = eirp - path_loss - misc_losses + gain - losses
    #-4,754 = 58 - 4808 - 4 + 4 - 4
    expected_received_power = ((40 + 20 - 2) - 4808 - 4 + 4 - 4)

    assert actual_received_power == expected_received_power

def test_calculate_interference(base_system):

    frequency = 0.7

    receiver = base_system.receivers['AB3']

    closest_transmitters = base_system.find_closest_available_transmitters(
        receiver
        )

    actual_interference = base_system.calculate_interference(
        closest_transmitters,
        receiver,
        frequency
        )

    #eirp = power + gain - losses
    #received_power = eirp - path_loss - misc_losses + gain - losses
    #interference 1
    #path loss(0.7 475 20 macro 20 20 urban nlos 1.5 0)
    #-349 = (40 + 20 - 2) - 403 - 4 + 4 - 4
    #interference 2
    #path_loss(0.7 477 20 macro 20 20 urban nlos 1.5 0)
    #-346 = (40 + 20 - 2) - 400 - 4 + 4 - 4
    #interference 3
    #path_loss(0.7 1078 20 macro 20 20 urban nlos 1.5 0)
    #-538 = (40 + 20 - 2) - 592 - 4 + 4 - 4

    #distance/geometry based
    # expected_interference = [
    #     -349, -346, -538
    #     ]

    #stochastic component for building penetration loss 8655567
    expected_interference = [
        -8655916, -8655913, -8656105
        ]

    assert actual_interference == expected_interference

def test_calculate_noise(base_system):

    bandwidth = 10

    actual_result = base_system.calculate_noise(bandwidth)

    expected_result = 5

    assert actual_result == expected_result

def test_calculate_sinr(base_system):

    receiver = base_system.receivers['AB3']

    closest_transmitter = base_system.find_closest_available_transmitters(receiver)[0]

    actual_received_power = base_system.calc_received_power(
        closest_transmitter,
        receiver,
        (4808 + 8655567)
        )

    closest_transmitters = base_system.find_closest_available_transmitters(receiver)

    actual_interference = base_system.calculate_interference(
        closest_transmitters,
        receiver,
        0.7
        )

    actual_noise = base_system.calculate_noise(10)

    actual_sinr = round(
        actual_received_power / sum(actual_interference) + actual_noise, 1
        )

    expected_received_power = ((40 + 20 - 2) - (4808 + 8655567) - 4 + 4 - 4)

    expected_interference = [
        -8655916, -8655913, -8656105
        ]

    expected_noise = 5

    #expected_sinr = 8.9
    #expected_sinr = ((40 + 20 - 2) - 4808 - 4 + 4 - 4) / sum(-349, -346, -538) + 5
    # 8.9 = -4764 / -1233 +5
    expected_sinr = round(
        expected_received_power / sum(expected_interference) + expected_noise, 1
        )

    assert actual_sinr == expected_sinr

def test_modulation_scheme_and_coding_rate(base_system):

    MODULATION_AND_CODING_LUT =[
        #CQI Index	Modulation	Coding rate	Spectral efficiency (bps/Hz) SINR estimate (dB)
        (1,	'QPSK',	0.0762,	0.1523, -6.7),
        (2,	'QPSK',	0.1172,	0.2344, -4.7),
        (3,	'QPSK',	0.1885,	0.377, -2.3),
        (4,	'QPSK',	0.3008,	0.6016, 0.2),
        (5,	'QPSK',	0.4385,	0.877, 2.4),
        (6,	'QPSK',	0.5879,	1.1758,	4.3),
        (7,	'16QAM', 0.3691, 1.4766, 5.9),
        (8,	'16QAM', 0.4785, 1.9141, 8.1),
        (9,	'16QAM', 0.6016, 2.4063, 10.3),
        (10, '64QAM', 0.4551, 2.7305, 11.7),
        (11, '64QAM', 0.5537, 3.3223, 14.1),
        (12, '64QAM', 0.6504, 3.9023, 16.3),
        (13, '64QAM', 0.7539, 4.5234, 18.7),
        (14, '64QAM', 0.8525, 5.1152, 21),
        (15, '64QAM', 0.9258, 5.5547, 22.7),
        ]

    actual_result = base_system.modulation_scheme_and_coding_rate(
        10, MODULATION_AND_CODING_LUT
        )
    
    expected_result = 1.9141

    assert actual_result == expected_result

def test_estimate_capacity(base_system):

    bandwidth = 10
    spectral_effciency = 1

    actual_estimate_capacity = base_system.estimate_capacity(
        bandwidth, spectral_effciency
        )

    expected_estimate_capacity = (bandwidth/1000000)*spectral_effciency

    assert actual_estimate_capacity == expected_estimate_capacity

