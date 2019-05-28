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
    'tx_gain': 16,
    'tx_losses': 1,
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
def base_system(setup_cb41_postcode_sector, setup_simulation_parameters,
    setup_transmitters, setup_receivers):

    geojson_postcode_sector = setup_cb41_postcode_sector

    geojson_postcode_sector['properties']['local_authority_ids'] = [
        'E07000008'
        ]

    system = NetworkManager(geojson_postcode_sector, setup_transmitters,
        setup_receivers, setup_simulation_parameters)

    return system

@pytest.fixture
def system_single_receiver(setup_cb41_postcode_sector, setup_simulation_parameters,
    setup_transmitters, setup_single_receiver):

    geojson_postcode_sector = setup_cb41_postcode_sector

    geojson_postcode_sector['properties']['local_authority_ids'] = [
        'E07000008'
        ]

    system = NetworkManager(geojson_postcode_sector, setup_transmitters,
        setup_single_receiver, setup_simulation_parameters)

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
                    "gain": 16,
                    "losses": 1,
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
                    "gain": 16,
                    "losses": 1,
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
                    "gain": 16,
                    "losses": 1,
                }
        }
    ]

    base_system.build_new_assets(
        build_this_transmitter, 'CB11', setup_simulation_parameters
        )

    assert len(base_system.sites) == 5

def test_estimate_link_budget(system_single_receiver, setup_modulation_coding_lut,
    setup_simulation_parameters):

    actual_result = system_single_receiver.estimate_link_budget(
        0.7, 10, '5G', 30, 'urban', setup_modulation_coding_lut,
        setup_simulation_parameters
        )
    # print(actual_result)
    # find closest_transmitters
    # <Receiver id:AB1>
    # [<Transmitter id:TL4454059600>, <Transmitter id:TL4515059700>,
    # <Transmitter id:TL4529059480>, <Transmitter id:TL4577059640>]
    # <Receiver id:AB3>
    # [<Transmitter id:TL4454059600>, <Transmitter id:TL4515059700>,
    # <Transmitter id:TL4529059480>, <Transmitter id:TL4577059640>]
    # <Receiver id:AB2>
    # [<Transmitter id:TL4454059600>, <Transmitter id:TL4529059480>,
    # <Transmitter id:TL4515059700>, <Transmitter id:TL4577059640>]

    # find path_loss for AB3
    # path loss for AB3 to nearest cell TL4454059600 is 99.44
    # distance 0.475
    # interference path loss for AB3 to TL4515059700 is 119.96
    # distance 0.477
    # interference path loss for AB3 to TL4529059480 is 120.02
    # distance 1.078
    # interference path loss for AB3 to TL4577059640 is 132.4
    # received_power is -45.44
    # interference is [-65.96, -66.02, -78.4]
    # noise is -102.47722915699805
    # sinr is 20.07

    # find spectral efficiency (self.modulation_scheme_and_coding_rate)

    # find (self.estimate_capacity)

    assert actual_result[0]['capacity_mbps'] == 62.266


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
    expected_received_power = ((40 + 16 - 1) - 173.94 - 4 + 4 - 4)

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

    #AB3
    #eirp = power + gain - losses
    #received_power = eirp - path_loss - misc_losses + gain - losses
    #interference 1
    #path loss(0.7 475 20 macro 20 20 urban nlos 1.5 0)
    #-65.89 = (40 + 16 - 1) - 119.96 - 4 + 4 - 4
    #interference 2
    #path_loss(0.7 477 20 macro 20 20 urban nlos 1.5 0)
    #-66.02 = (40 + 16 - 1) - 120.02 - 4 + 4 - 4
    #interference 3
    #path_loss(0.7 1078 20 macro 20 20 urban nlos 1.5 0)
    #-78.4 = (40 + 16 - 1) - 132.4 - 4 + 4 - 4

    expected_interference = [
        -68.96, -69.02, -81.4
        ]

    assert actual_interference == expected_interference


def test_calculate_noise(base_system):

    bandwidth = 100

    actual_result = round(base_system.calculate_noise(bandwidth),2)

    expected_result = -92.48

    assert actual_result == expected_result


def test_calculate_sinr(base_system, setup_simulation_parameters):

    #calculation in link_budget_validation.xlsx

    actual_sinr = base_system.calculate_sinr(-45.44, [-65.96, -66.02, -78.4], -102.48,
        setup_simulation_parameters)

    assert actual_sinr == 20.07


def test_modulation_scheme_and_coding_rate(base_system, setup_modulation_coding_lut):

    actual_result = base_system.modulation_scheme_and_coding_rate(
        10, '4G', setup_modulation_coding_lut
        )

    expected_result = 1.9141

    assert actual_result == expected_result

    actual_result = base_system.modulation_scheme_and_coding_rate(
        10, '5G', setup_modulation_coding_lut
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


def test_energy_consumption(base_system, setup_simulation_parameters):

    # sites = 2
    # power = 40 dBm
    actual_energy_consumption = base_system.energy_consumption(
        setup_simulation_parameters
        )

    assert actual_energy_consumption == 60
