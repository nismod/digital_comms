import pytest
import os

from digital_comms.mobile_network.transmitter_module import get_transmitters
from digital_comms.mobile_network.transmitter_module import generate_receivers
from digital_comms.mobile_network.transmitter_module import NetworkManager
from digital_comms.mobile_network.transmitter_module import read_postcode_sector

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
                "coordinates": [0.124896, 52.215965]
            },
            'properties': {
                "operator":'voda',
                "opref": 46497,
                "sitengr": 'TL4515059700',
                "ant_height": 13.7,
                "type": 'macro',
                "power": 28.1,
                "gain": 18,
                "losses": 2,
                "pcd_sector": "CB1 1",
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [0.133939, 52.215263]
            },
            'properties': {
                "operator":'voda',
                "opref": 31745,
                "sitengr": 'TL4577059640',
                "ant_height": 14.9,
                "type": 'macro',
                "power": 29.8,
                "gain": 18,
                "losses": 2,
                "pcd_sector": "CB1 2",
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [0.11593, 52.215227]
            },
            'properties': {
                "operator":'voda',
                "opref": 31742,
                "sitengr": 'TL4454059600',
                "ant_height": 14.9,
                "type": 'macro',
                "power": 29.8,
                "gain": 18,
                "losses": 2,
                "pcd_sector": "CB1 2",
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [0.12512, 52.21442]
            },
            'properties': {
                "operator":'voda',
                "opref": 31746,
                "sitengr": 'TL4529059480',
                "ant_height": 14.9,
                "type": 'macro',
                "power": 29.8,
                "gain": 18,
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
                "coordinates": [0.11748, 52.21854]
            },
            'properties': {
                "ue_id": "AB1",
                "sitengr": 'TL4454059600',
                "misc_losses": 4,
                "gain": 4,
                "losses": 4,
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [0.11670, 52.21362]
            },
            'properties': {
                "ue_id": "AB2",
                "sitengr": 'TL4454059600',
                "misc_losses": 4,
                "gain": 4,
                "losses": 4,
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [0.118174, 52.214870]
            },
            'properties': {
                "ue_id": "AB3",
                "sitengr": 'TL4454059600',
                "misc_losses": 4,
                "gain": 4,
                "losses": 4,
            }
        }
    ]

    system = NetworkManager(get_postcode_sector, TRANSMITTERS, RECEIVERS)

    return system

def test_get_transmitters(get_postcode_sector):

    actual_receivers = get_transmitters(get_postcode_sector)

    assert len(actual_receivers) == 21

def test_generate_receivers(get_postcode_sector):

    actual_receivers = generate_receivers(get_postcode_sector, 100)

    receiver_1 = actual_receivers[0]

    assert len(actual_receivers) == 100
    assert receiver_1['properties']['ue_id'] == 'id_0'
    assert receiver_1['properties']['misc_losses'] == 4
    assert receiver_1['properties']['gain'] == 4
    assert receiver_1['properties']['losses'] == 4

# def test_calc_buget(base_system):

#     actual_results = base_system.calc_link_budget(3.5, 5, 1)
#     print(actual_results)
#     assert actual_results == 0
