from pprint import pprint
from rtree import index
from shapely.geometry import shape, Point
import pyproj

from path_loss_calculations import path_loss_calc_module
from built_env_module import find_line_of_sight 

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
        
        idx = index.Index()

        for transmitter in self.transmitters.values(): 
            idx.insert(0, Point(transmitter.coordinates).bounds, transmitter)

        for transmitter in self.transmitters.values():    

            all_nearest_transmitters = []
            three_nearest_transmitters = []

            ant_type = 'macro' #transmitter.ant_type
            ant_height = 20 #transmitter.ant_height
            #transmitter_geom = Point(transmitter.coordinates)

            x1_transmitter = transmitter.coordinates[0]
            y1_transmitter = transmitter.coordinates[1]

            receivers = []
            for id, receiver in self.receivers.items():
                if transmitter.id == receiver.transmitter_id:
                    receivers.append(receiver)
                else:
                    pass            

            all_nearest_transmitters =  list(
                idx.nearest(
                    Point(transmitter.coordinates).bounds, 4, objects='raw'))
            
            for nearest_transmitter in all_nearest_transmitters:
                if nearest_transmitter.id != transmitter.id:
                    three_nearest_transmitters.append(nearest_transmitter)

            for receiver in receivers:
                
                x2_receiver = receiver.coordinates[0]
                y2_receiver = receiver.coordinates[1]
                
                geod = pyproj.Geod(ellps='WGS84')
                angle1,angle2,i_strt_distance = geod.inv(x1_transmitter, y1_transmitter, 
                                                        x2_receiver, y2_receiver)
                interference_strt_distance = round(i_strt_distance, 0)

                #determine line of sight and built env parameters
                settlement_type = 'urban'
                #type_of_sight, building_height, street_width = built_environment_module(transmitter_geom, receiver_geom)  
                print('testing')
                type_of_sight = find_line_of_sight(x1_transmitter, y1_transmitter, x2_receiver, y2_receiver)  
                print(type_of_sight)
                #type_of_sight = 'los'
                building_height = 20
                street_width = 20

                #TODO - module that determines line of sight
                                
                path_loss = path_loss_calc_module(
                    frequency, 
                    interference_strt_distance, 
                    ant_height, 
                    ant_type, 
                    building_height, 
                    street_width, 
                    settlement_type, 
                    type_of_sight, 
                    receiver.ue_height)

                #calculate received power
                received_power = calc_received_power(transmitter, receiver, path_loss)
                
                interference = []

                #calculate interference from other power sources
                for interference_transmitter in three_nearest_transmitters:
                    
                    #get distance
                    x2_interference_transmitter = interference_transmitter.coordinates[0]
                    y2_interference_transmitter = interference_transmitter.coordinates[1]
                    angle1,angle2,i_strt_distance = geod.inv(x2_interference_transmitter, y2_interference_transmitter, 
                                                            x2_receiver, y2_receiver)
                    i_strt_distance = round(i_strt_distance, 0)

                    #get built env paramaters
                    building_height = 20
                    street_width = 20
                    settlement_type = 'urban' 
                    type_of_sight = 'nlos'

                    path_loss = path_loss_calc_module(
                        frequency, 
                        i_strt_distance, 
                        interference_transmitter.ant_height, 
                        interference_transmitter.ant_type, 
                        building_height, 
                        street_width, 
                        settlement_type, 
                        type_of_sight, 
                        receiver.ue_height)

                    #calc interference from other cells
                    received_interference = calc_received_power(transmitter, receiver, path_loss)

                    #add cell interference to list 
                    interference.append(received_interference)
                
                #calculation receiver noise (N  = k T B) 
                #where k is Boltzmann's constant, T is temperatrue in K and B is bandwidth in use  
                noise = 5

                #calculate SINR
                sinr = round(received_power / sum(interference) + noise, 1)

                #get block error rate (BER)

        return 

class Transmitter(object):
    
    def __init__(self, data):
        #id and geographic info
        self.id = data['properties']["sitengr"]
        self.coordinates = data['geometry']["coordinates"]
        #antenna properties
        self.ant_type = data['properties']['type']
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
        self.ue_height = 1.5
    
def calc_received_power(transmitter, receiver, path_loss):

    eirp = transmitter.power + transmitter.gain - transmitter.losses 
    received_power = eirp - path_loss - receiver.misc_losses + receiver.gain - receiver.losses

    return received_power            

if __name__ == '__main__':
    
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

MANAGER = NetworkManager(TRANSMITTERS, RECEIVERS)
MANAGER.calc_link_budget(3.5)