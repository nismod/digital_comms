from pprint import pprint
from shapely.geometry import shape, Point

from digital_comms.mobile_network.path_loss_calculations import path_loss_calc_module

class NetworkManager(object):

    def __init__(self, transmitters, receivers):

        self.transmitters = {}
        self.receivers = {}

        for transmitter in transmitters:
            transmitter_id = transmitter['properties']["sitengr"]
            self.transmitters[transmitter_id] = Transmitter(transmitter)
        for receiver_data in receivers:
            transmitter_id = receiver_data['properties']["sitengr"]
            receiver_id = receiver_data['properties']["ue_id"]
            receiver = Receiver(receiver_data)
            self.receivers[receiver_id] = receiver
            transmitter_containing_receiver = self.transmitters[transmitter_id]
            transmitter_containing_receiver.add_receiver(receiver)
    
    def calc_link_budget(self, frequency):
        for transmitter in self.transmitters.values(): 
            ant_type = transmitter.type
            ant_height = transmitter.ant_height
            transmitter_geom = Point(transmitter.coordinates)

            receivers = []
            for id, receiver in self.receivers.items():
                if transmitter.id == receiver.transmitter_id:
                    receivers.append(receiver)
                else:
                    pass

            for receiver in receivers:
                receiver_geom = Point(receiver.coordinates)
                #strt_distance = round(transmitter_geom.distance(receiver_geom), 2)
                strt_distance = 100
                type_of_sight = 'nlos'
                ue_height = 1.5

                #print(strt_distance)
                path_loss = path_loss_calc_module(frequency, strt_distance, 25, 'macro', 'urban', type_of_sight, ue_height)
                
                print(path_loss)

                #do path_loss calc
                #pass coordinates to a separate module that does the distance calc?
                #pass coordinates to a separate module that does the LOS or NLOS?
                #pass coordinates to a separate module that does the path loss equation?
         
        return 

class Transmitter(object):
    
    def __init__(self, data):
        #id and geographic info
        self.id = data['properties']["sitengr"]
        self.coordinates = data['geometry']["coordinates"]
        #antenna properties
        self.type = data['properties']['type']
        self.ant_height = data['properties']['ant_height']
        self.power = data['properties']["power"]
        self.gain = data['properties']["gain"]
        self.losses = data['properties']["losses"]
        #connections
        self._receivers = {}
    
    def add_receiver(self, receiver):
        self._receivers[receiver.id] = receiver

class Receiver(object):
    def __init__(self, data):
         #id and geographic info
        self.id = data['properties']['ue_id']
        self.transmitter_id = data['properties']['sitengr']
        self.coordinates = data['geometry']["coordinates"]
        #parameters
        self.misc_losses = data['properties']['misc_losses']
        self.gain = data['properties']['gain']
        self.losses = data['properties']['losses']
    
if __name__ == '__main__':
    
    TRANSMITTERS = [
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [52.205323, 0.134546]
            },
            'properties': {
                "operator":'voda',
                "opref": 46497,
                "sitengr": 'TL4584458536',
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
                "coordinates": [52.195027, 0.132019]
            },
            'properties': {
                "operator":'voda',
                "opref": 31745,
                "sitengr": 'TL4570557386',
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
                "coordinates": [52.22, 0.19]
            },
            'properties': {
                "ue_id": "AB1",
                "sitengr": 'TL4584458536',
                "misc_losses": 4,
                "gain": 4,
                "losses": 4,
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [52.29, 0.19]
            },
            'properties': {
                "ue_id": "AB2",
                "sitengr": 'TL4584458536',
                "misc_losses": 4,
                "gain": 4,
                "losses": 4,
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [52.2, 0.2]
            },
            'properties': {
                "ue_id": "AB3",
                "sitengr": 'TL4584458536',
                "misc_losses": 4,
                "gain": 4,
                "losses": 4,
            }
        }
    ]

MANAGER = NetworkManager(TRANSMITTERS, RECEIVERS)
MANAGER.calc_link_budget(3.5)
# for transmitter in MANAGER.transmitters.values():
#     pprint(transmitter)
#     for receiver in transmitter._receivers.values():
#         print(" ", receiver, "gain: {}, losses:{}".format(receiver.gain, receiver.losses))