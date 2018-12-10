from pprint import pprint
from shapely.geometry import shape, Point

class NetworkManager(object):

    def __init__(self, transmitters, receivers):

        self.transmitters = {}
        self.receivers = {}

        for transmitter in transmitters:
            transmitter_id = transmitter['properties']["id"]
            self.transmitters[transmitter_id] = Transmitter(transmitter)

        for receiver_data in receivers:
            transmitter_id = receiver_data['properties']["transmitter_id"]
            receiver_id = receiver_data['properties']["id"]
            receiver = Receiver(receiver_data)
            self.receivers[receiver_id] = receiver

            transmitter_containing_receiver = self.transmitters[transmitter_id]
            transmitter_containing_receiver.add_receiver(receiver)

    def calc_link_budget(self):

        for transmitter in self.transmitters.values(): 
            transmitter_geom = Point(transmitter.coordinates)
            
            receivers = []

            for id, receiver in self.receivers.items():
                if transmitter.id == receiver.transmitter_id:
                    receivers.append(receiver)
                else:
                    pass

            for receiver in receivers:
                receiver_geom = Point(receiver.coordinates)
                strt_distance = round(transmitter_geom.distance(receiver_geom), 2)

                #do path_loss calc

                #pass coordinates to a separate module that does the distance calc?
                #pass coordinates to a separate module that does the LOS or NLOS?
                #pass coordinates to a separate module that does the path loss equation?

        
        return 

class Transmitter(object):

    def __init__(self, data):
        #id and geographic info
        self.id = data['properties']["id"]
        self.coordinates = data['geometry']["coordinates"]
        #antenna properties
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
        self.id = data['properties']['id']
        self.transmitter_id = data['properties']['transmitter_id']
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
                "coordinates": [3, 5]
            },
            'properties': {
                "id": 1,
                "power": 46,
                "gain": 18,
                "losses": 2,
                "name": "Cambridge",
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [1, 4]
            },
            'properties': {
                "id": 2,
                "power": 46,
                "gain": 18,
                "losses": 2,
                "name": "Cambridge",
            }
        }
    ]

    RECEIVERS = [
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [1, 2]
            },
            'properties': {
                "id": "AB1",
                "transmitter_id": 1,
                "misc_losses": 4,
                "gain": 4,
                "losses": 4,
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [2, 3]
            },
            'properties': {
                "id": "AB2",
                "transmitter_id": 1,
                "misc_losses": 4,
                "gain": 4,
                "losses": 4,
            }
        },
        {
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [4, 3]
            },
            'properties': {
                "id": "AB3",
                "transmitter_id": 2,
                "misc_losses": 4,
                "gain": 4,
                "losses": 4,

            }
        }
    ]

MANAGER = NetworkManager(TRANSMITTERS, RECEIVERS)
MANAGER.calc_link_budget()
# for transmitter in MANAGER.transmitters.values():
#     pprint(transmitter)
#     for receiver in transmitter._receivers.values():
#         print(" ", receiver, "gain: {}, losses:{}".format(receiver.gain, receiver.losses))
