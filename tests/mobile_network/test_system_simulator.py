import pytest
import os
import numpy as np
from shapely.geometry import shape, Point

from digital_comms.mobile_network.system_simulator import NetworkManager
from scripts.mobile_simulator_run import (
    read_postcode_sector,
    get_local_authority_ids,
    determine_environment,
    get_sites,
    generate_receivers,
    find_and_deploy_new_site,
    )

@pytest.fixture
def setup_simulation_parameters():
    return {
    'iterations': 100,
    'tx_baseline_height': 30,
    'tx_upper_height': 40,
    'tx_power': 40,
    'tx_gain': 20,
    'tx_losses': 2,
    'rx_gain': 4,
    'rx_losses': 4,
    'rx_misc_losses': 4,
    'rx_height': 1.5,
    'network_load': 50,
    'percentile': 95,
    'desired_transmitter_density': 10,
    'sectorisation': 3,
    }

@pytest.fixture
def base_system(setup_cb41_postcode_sector, setup_simulation_parameters):

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
                "ue_height": 1.5,
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
                "ue_height": 1.5,
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
                "ue_height": 1.5,
                "indoor": True,
            }
        }
    ]

    geojson_postcode_sector = setup_cb41_postcode_sector

    geojson_postcode_sector['properties']['local_authority_ids'] = [
        'E07000008'
        ]

    system = NetworkManager(geojson_postcode_sector, TRANSMITTERS,
        RECEIVERS, setup_simulation_parameters)

    return system


@pytest.fixture
def postcode_sector_lut():

    yield {
        'postcode_sector': 'CB11',
        'indoor_probability': 100,
        'outdoor_probability': 0,
        'residential_count': 20,
        'non_residential_count': 20,
        'estimated_population': 50,
        'area': 200,
    }


@pytest.fixture
def modulation_coding_lut():

    yield [
        # CQI Index	Modulation	Coding rate
        # Spectral efficiency (bps/Hz) SINR estimate (dB)
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

def test_determine_environment(postcode_sector_lut):

    test_urban_1 = {
        'estimated_population': 10000,
        'area': 1,
    }

    assert determine_environment(test_urban_1) == 'urban'

    test_suburban_1 = {
        'estimated_population': 7000,
        'area': 1,
    }

    assert determine_environment(test_suburban_1) == 'suburban'

    test_suburban_2 = {
        'estimated_population': 1000,
        'area': 1,
    }

    assert determine_environment(test_suburban_2) == 'suburban'

    test_rural_1 = {
        'estimated_population': 500,
        'area': 1,
    }

    assert determine_environment(test_rural_1) == 'rural'

    test_rural_2 = {
        'estimated_population': 100,
        'area': 1,
    }

    assert determine_environment(test_rural_2) == 'rural'

    test_rural_3 = {
        'estimated_population': 50,
        'area': 1,
    }

    assert determine_environment(test_rural_3) == 'rural'

    actual_results = determine_environment(postcode_sector_lut)

    expected_result = 'rural'

    assert actual_results == expected_result


def test_get_sites(setup_postcode_sector, setup_simulation_parameters):

    postcode_sector = setup_postcode_sector

    actual_sites = get_sites(postcode_sector, 'synthetic',
        setup_simulation_parameters)

    geom = shape(postcode_sector['geometry'])

    actual_sites_in_shape = []

    for site in actual_sites:
        if geom.contains(Point(site['geometry']['coordinates'])):
            actual_sites_in_shape.append(site)

    assert len(actual_sites_in_shape) == 1


def test_generate_receivers(setup_postcode_sector,
    postcode_sector_lut, setup_simulation_parameters):

    actual_receivers = generate_receivers(
        setup_postcode_sector, postcode_sector_lut,
        setup_simulation_parameters
        )

    receiver_1 = actual_receivers[0]

    assert len(actual_receivers) == 100
    assert receiver_1['properties']['ue_id'] == 'id_0'
    assert receiver_1['properties']['misc_losses'] == 4
    assert receiver_1['properties']['gain'] == 4
    assert receiver_1['properties']['losses'] == 4
    assert receiver_1['properties']['indoor'] == True


def test_find_and_deploy_new_site(base_system,
    setup_postcode_sector, setup_simulation_parameters):

    new_transmitter = find_and_deploy_new_site(
        base_system.sites, 1, setup_postcode_sector, 1,
        setup_simulation_parameters
        )

    expected_transmitter = [
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [545393.3136180863, 258614.45929655718]
            },
            'properties': {
                    "operator": 'unknown',
                    "sitengr": '{new}{GEN1.1}',
                    "ant_height": 30,
                    "tech": 'LTE',
                    "freq": 700,
                    "type": 17,
                    "power": 40,
                    "gain": 20,
                    "losses": 2,
                }
        }
    ]

    assert len(new_transmitter) == 1
    assert new_transmitter == expected_transmitter

    new_transmitter = find_and_deploy_new_site(
        base_system.sites, 1, setup_postcode_sector, 1,
        setup_simulation_parameters
        )

    expected_transmitter = [
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [545311.9353406072, 258483.37922303876]
            },
            'properties': {
                    "operator": 'unknown',
                    "sitengr": '{new}{GEN1.1}',
                    "ant_height": 30,
                    "tech": 'LTE',
                    "freq": 700,
                    "type": 17,
                    "power": 40,
                    "gain": 20,
                    "losses": 2,
                }
        }
    ]

    assert len(new_transmitter) == 1
    assert new_transmitter == expected_transmitter


def test_network_manager(base_system):

    assert len(base_system.area) == 1
    assert len(base_system.sites) == 4
    assert len(base_system.receivers) == 3


def test_build_new_assets(base_system, setup_simulation_parameters):

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

    base_system.build_new_assets(
        build_this_transmitter, 'CB11', setup_simulation_parameters
        )

    assert len(base_system.sites) == 5


# def test_estimate_link_budget(base_system, modulation_coding_lut):

#     actual_result = base_system.estimate_link_budget(
#         0.7, 10, 'urban', modulation_coding_lut
#         )
#     print(actual_result)
#     # find closest_transmitters
#     # <Receiver id:AB1>
#     # [<Transmitter id:TL4454059600>, <Transmitter id:TL4515059700>,
#     # <Transmitter id:TL4529059480>, <Transmitter id:TL4577059640>]
#     # <Receiver id:AB3>
#     # [<Transmitter id:TL4454059600>, <Transmitter id:TL4515059700>,
#     # <Transmitter id:TL4529059480>, <Transmitter id:TL4577059640>]
#     # <Receiver id:AB2>
#     # [<Transmitter id:TL4454059600>, <Transmitter id:TL4529059480>,
#     # <Transmitter id:TL4515059700>, <Transmitter id:TL4577059640>]

#     # find path_loss

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

#     # find received_power (self.calc_received_power)

#     # find interference (self.calculate_interference)

#     # find noise (self.calculate_noise)

#     # find sinr (self.calculate_sinr)

#     #find spectral efficiency (self.modulation_scheme_and_coding_rate)

#     # find (self.estimate_capacity)

#     expected_result = 0

#     assert expected_result == actual_result


def test_find_closest_available_sites(base_system):

    receiver = base_system.receivers['AB3']

    transmitter, interfering_transmitters = (
        base_system.find_closest_available_sites(receiver)
        )

    assert transmitter.id == 'TL4454059600'

    interfering_transmitter_ids = [t.id for t in interfering_transmitters]

    expected_result = [
        'TL4515059700', 'TL4529059480', 'TL4577059640'
        ]

    assert interfering_transmitter_ids == expected_result


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

    transmitter, interfering_transmitters = (
        base_system.find_closest_available_sites(receiver)
        )

    actual_result = base_system.calculate_path_loss(
        transmitter, receiver, frequency, ant_height, 'urban'
        )

    #model requires frequency in MHz rather than GHz.
    frequency = frequency*1000
    #model requires distance in kilometers rather than meters.
    distance = interference_strt_distance/1000

    #find smallest value
    hm = min(ant_height, ue_height)
    #find largest value
    hb = max(ant_height, ue_height)

    alpha_hm = (1.1*np.log10(frequency) - 0.7) * min(10, hm) - \
        (1.56*np.log10(frequency) - 0.8) + max(0, (20*np.log10(hm/10)))

    beta_hb = min(0, (20*np.log10(hb/30)))

    alpha_exponent = 1

    path_loss = round((
        69.6 + 26.2*np.log10(frequency) -
        13.82*np.log10(max(30, hb)) +
        (44.9 - 6.55*np.log10(max(30, hb))) *
        (np.log10(distance))**alpha_exponent - alpha_hm - beta_hb), 2
    )

    #stochastic component for geometry/distance 0.64
    #stochastic component for building penetration loss 3.31
    path_loss = path_loss + 3.31 + 0.64

    assert actual_result == round(path_loss,2)


def test_calc_received_power(base_system):

    receiver = base_system.receivers['AB3']

    transmitter, interfering_transmitters = (
        base_system.find_closest_available_sites(receiver)
        )

    actual_received_power = base_system.calc_received_power(
        transmitter,
        receiver,
        173.94
        )

    #eirp = power + gain - losses
    #58 = 40 + 20 - 2
    #received_power = eirp - path_loss - misc_losses + gain - losses
    #-119.94 = 58 - 173.94 - 4 + 4 - 4
    expected_received_power = ((40 + 20 - 2) - 173.94 - 4 + 4 - 4)

    assert actual_received_power == expected_received_power


def test_calculate_interference(base_system):

    frequency = 0.7

    receiver = base_system.receivers['AB3']

    transmitter, interfering_transmitters = (
        base_system.find_closest_available_sites(receiver)
        )

    actual_interference = base_system.calculate_interference(
        interfering_transmitters,
        receiver,
        frequency,
        'urban'
        )

    #eirp = power + gain - losses
    #received_power = eirp - path_loss - misc_losses + gain - losses
    #interference 1
    #path loss(0.7 475 20 macro 20 20 urban nlos 1.5 0)
    #-65.89 = (40 + 20 - 2) - 119.96 - 4 + 4 - 4
    #interference 2
    #path_loss(0.7 477 20 macro 20 20 urban nlos 1.5 0)
    #-66.02 = (40 + 20 - 2) - 120.02 - 4 + 4 - 4
    #interference 3
    #path_loss(0.7 1078 20 macro 20 20 urban nlos 1.5 0)
    #-78.4 = (40 + 20 - 2) - 132.4 - 4 + 4 - 4

    expected_interference = [
        -65.96, -66.02, -78.4
        ]

    assert actual_interference == expected_interference


def test_calculate_noise(base_system):

    bandwidth = 100

    actual_result = round(base_system.calculate_noise(bandwidth),2)

    expected_result = -92.48

    assert actual_result == expected_result


def test_calculate_sinr(base_system, setup_simulation_parameters):

    # receiver = base_system.receivers['AB3']

    # closest_transmitter = base_system.find_closest_available_sites(
    #     receiver
    #     )[0]

    # actual_received_power = base_system.calc_received_power(
    #     closest_transmitter,
    #     receiver,
    #     173.94
    #     )

    # closest_transmitters = base_system.find_closest_available_sites(
    #     receiver
    #     )

    # actual_interference = base_system.calculate_interference(
    #     closest_transmitters,
    #     receiver,
    #     0.7,
    #     'urban'
    #     )

    # def convert_to_raw(my_list):
    #     interference = []
    #     for value in my_list:
    #         final_value = 10**value
    #         interference.append(final_value)
    #     final_interference = np.log10(sum(interference))

    #     return round(final_interference, 2)

    # actual_raw_interference = convert_to_raw(actual_interference)

    # actual_raw_noise = base_system.calculate_noise(10)

    # actual_sinr = round(
    #     actual_received_power / (actual_interference + actual_noise), 1
    #     )

    # expected_received_power = ((40 + 20 - 2) - 173.94 - 4 + 4 - 4)

    # expected_interference = [
    #     -144.92, -145.02, -163.44
    #     ]

    # expected_interference = convert_to_dbm(expected_interference)

    # expected_noise = -104.5

    # #expected_sinr = 8.9
    # #expected_sinr = ((40 + 20 - 2) - 4808 - 4 + 4 - 4) / sum(-349, -346, -538) + 5
    # # 8.9 = -4764 / -1233 +5
    # expected_sinr = round(
    #     expected_received_power / (expected_interference + expected_noise), 1
        # )

    actual_sinr = round(
        base_system.calculate_sinr(-20, [-65.96, -66.02, -78.4], -80,
        setup_simulation_parameters), 2,

        )

    assert actual_sinr == 45.51


def test_modulation_scheme_and_coding_rate(base_system):

    MODULATION_AND_CODING_LUT =[
        #CQI Index	Modulation	Coding rate	Spectral efficiency (bps/Hz) SINR estimate (dB)
        ('4G', 1, 'QPSK',	0.0762,	0.1523, -6.7),
        ('4G', 2, 'QPSK',	0.1172,	0.2344, -4.7),
        ('4G', 3, 'QPSK',	0.1885,	0.377, -2.3),
        ('4G', 4, 'QPSK',	0.3008,	0.6016, 0.2),
        ('4G', 5, 'QPSK',	0.4385,	0.877, 2.4),
        ('4G', 6, 'QPSK',	0.5879,	1.1758,	4.3),
        ('4G', 7, '16QAM', 0.3691, 1.4766, 5.9),
        ('4G', 8, '16QAM', 0.4785, 1.9141, 8.1),
        ('4G', 9, '16QAM', 0.6016, 2.4063, 10.3),
        ('4G', 10, '64QAM', 0.4551, 2.7305, 11.7),
        ('4G', 11, '64QAM', 0.5537, 3.3223, 14.1),
        ('4G', 12, '64QAM', 0.6504, 3.9023, 16.3),
        ('4G', 13, '64QAM', 0.7539, 4.5234, 18.7),
        ('4G', 14, '64QAM', 0.8525, 5.1152, 21),
        ('4G', 15, '64QAM', 0.9258, 5.5547, 22.7),
        ('5G', 1, 'QPSK', 78, 0.1523, -6.7),
        ('5G', 2, 'QPSK', 193, 0.377, -4.7),
        ('5G', 3, 'QPSK', 449, 0.877, -2.3),
        ('5G', 4, '16QAM', 378, 1.4766, 0.2),
        ('5G', 5, '16QAM', 490, 1.9141, 2.4),
        ('5G', 6, '16QAM', 616, 2.4063, 4.3),
        ('5G', 7, '64QAM', 466, 2.7305, 5.9),
        ('5G', 8, '64QAM', 567, 3.3223, 8.1),
        ('5G', 9, '64QAM', 666, 3.9023, 10.3),
        ('5G', 10, '64QAM', 772, 4.5234, 11.7),
        ('5G', 11, '64QAM', 873, 5.1152, 14.1),
        ('5G', 12, '256QAM', 711, 5.5547, 16.3),
        ('5G', 13, '256QAM', 797, 6.2266, 18.7),
        ('5G', 14, '256QAM', 885, 6.9141, 21),
        ('5G', 15, '256QAM', 948, 7.4063, 22.7),
        ]

    actual_result = base_system.modulation_scheme_and_coding_rate(
        10, '4G', MODULATION_AND_CODING_LUT
        )

    expected_result = 1.9141

    assert actual_result == expected_result

    actual_result = base_system.modulation_scheme_and_coding_rate(
        10, '5G', MODULATION_AND_CODING_LUT
        )

    expected_result = 3.3223

    assert actual_result == expected_result


def test_link_budget_capacity(base_system):

    bandwidth = 10
    spectral_effciency = 2

    actual_estimate_capacity = base_system.link_budget_capacity(
        bandwidth, spectral_effciency
        )

    expected_estimate_capacity = (
        ((bandwidth*1000000)*spectral_effciency)/1000000
        )

    assert actual_estimate_capacity == expected_estimate_capacity


def test_find_sites_in_area(base_system):

    actual_sites = base_system.find_sites_in_area()

    assert len(actual_sites) == 2


def test_site_density(base_system):

    # CB43 area is 2,180,238 m^2
    # sites = 2
    # 0.91733 sites per km^2 = 2 / (2,180,238 / 1e6)
    actual_site_density = round(base_system.site_density(),2)

    assert actual_site_density == 0.92


def test_receiver_density(base_system):

    # CB43 area is 2,180,238 m^2
    # receivers = 3
    # 1.375 receivers per km^2 = 3 / (2,180,238 / 1e6)
    actual_receiver_density = round(base_system.receiver_density(),2)

    assert actual_receiver_density == 1.38


# def test_energy_consumption(base_system, setup_simulation_parameters):

#     # sites = 2
#     # power = 40 dBm
#     actual_energy_consumption = base_system.energy_consumption(
#         setup_simulation_parameters
#         )

#     print(actual_energy_consumption)

#     assert actual_energy_consumption == 800
