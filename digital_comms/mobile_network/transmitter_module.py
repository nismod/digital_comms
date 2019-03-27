import os, sys, configparser
import csv
from rtree import index
import fiona
from shapely.geometry import shape, Point, Polygon
import numpy as np
from pyproj import Proj, transform, Geod
from geographiclib.geodesic import Geodesic
from collections import OrderedDict
import matplotlib.pyplot as plt

from digital_comms.mobile_network.path_loss_module import path_loss_calculator

# from built_env_module import find_line_of_sight

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..',  '..', 'scripts','script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#data locations
DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_RESULTS = os.path.join(BASE_PATH, '..' ,'results', 'system_simulator')

def read_postcode_sector(postcode_sector):
    postcode_area = ''.join([i for i in postcode_sector[:2] if not i.isdigit()])
    with fiona.open(os.path.join(DATA_RAW, 'd_shapes', 'postcode_sectors', postcode_area + '.shp'), 'r') as source:

        return [sector for sector in source if sector['properties']['postcode'].replace(" ", "") == postcode_sector][0]

def get_transmitters(postcode_sector):

    potential_transmitters = []

    geom = shape(postcode_sector['geometry'])
    geom_box = geom.bounds

    with open(os.path.join(DATA_RAW, 'b_mobile_model', 'sitefinder', 'sitefinder.csv'), 'r') as system_file:
            reader = csv.reader(system_file)
            next(reader)
            for line in reader:
                if (geom_box[0] <= float(line[0]) and geom_box[1] <= float(line[1]) and geom_box[2] >= float(line[0]) and geom_box[3] >= float(line[1])):
                    potential_transmitters.append({
                        'type': "Feature",
                        'geometry': {
                            "type": "Point",
                            "coordinates": [float(line[0]), float(line[1])]
                        },
                        'properties': {
                            "operator": line[2],
                            "sitengr": line[4],
                            "ant_height": line[5],
                            "tech": line[6],
                            "freq": line[7],
                            "type": line[9],
                            "power": 30,
                            "gain": 18,
                            "losses": 2,
                        }
                    })

    transmitters = []

    # Initialze Rtree
    idx = index.Index()
    [idx.insert(0, shape(transmitter['geometry']).bounds, transmitter) for transmitter in potential_transmitters]

    # Join the two
    for n in idx.intersection((shape(postcode_sector['geometry']).bounds), objects=True):
        postcode_sector_shape = shape(postcode_sector['geometry'])
        transmitter_shape = shape(n.object['geometry'])
        if postcode_sector_shape.contains(transmitter_shape):
            transmitters.append(n.object)

    return transmitters

def generate_receivers(postcode_sector, quantity):

    coordinates = []

    geom = shape(postcode_sector['geometry'])
    geom_box = geom.bounds

    minx = geom_box[0]
    miny = geom_box[1]
    maxx = geom_box[2]
    maxy = geom_box[3]

    receivers = []

    id_number = 0
    np.random.seed(42)

    while len(receivers) < quantity:

        x_coord = np.random.uniform(low=minx, high=maxx, size=1)
        y_coord = np.random.uniform(low=miny, high=maxy, size=1)

        coordinates = list(zip(x_coord, y_coord))

        # Join the two
        postcode_sector_shape = shape(postcode_sector['geometry'])
        receiver = Point((x_coord, y_coord))
        if postcode_sector_shape.contains(receiver):
            receivers.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [coordinates[0][0],coordinates[0][1]],
                },
                'properties': {
                    'ue_id': "id_{}".format(id_number),
                    #"sitengr": 'TL4454059600',
                    "misc_losses": 4,
                    "gain": 4,
                    "losses": 4,
                }
            })
            id_number += 1
        else:
            pass

    return receivers

class NetworkManager(object):

    def __init__(self, area, transmitters, receivers):

        self.area = {}
        self.transmitters = {}
        self.receivers = {}

        area_id = area['properties']['postcode']
        self.area[area_id] = Area(area)

        for transmitter in transmitters:
            transmitter_id = transmitter['properties']["sitengr"]
            transmitter = Transmitter(transmitter)
            self.transmitters[transmitter_id] = transmitter

            area_containing_transmitters = self.area[area_id]
            area_containing_transmitters.add_transmitter(transmitter)

        for receiver in receivers:
            receiver_id = receiver['properties']["ue_id"]
            receiver = Receiver(receiver)
            self.receivers[receiver_id] = receiver

            area_containing_receivers = self.area[area_id]
            area_containing_receivers.add_receiver(receiver)

    def calc_link_budget(self, frequency, bandwidth, iterations):
        """
        Takes propagation parameters and calculates capacity.

        """

        results = []

        for receiver in self.receivers.values():

            closest_transmitters = self.find_closest_available_transmitters(receiver)

            path_loss = self.calculate_path_loss(closest_transmitters[0], receiver, frequency)

            received_power = self.calc_received_power(closest_transmitters[0], receiver, path_loss)

            interference = self.calculate_interference(closest_transmitters, receiver, frequency)

            noise = self.calculate_noise(bandwidth)

            sinr = self.calculate_sinr(received_power, interference, noise)

            estimated_capacity = self.estimate_capacity(bandwidth, sinr)

            data = {'sinr': sinr, 'estimated_capacity': estimated_capacity}

            results.append(data)

        return results

    def find_closest_available_transmitters(self, receiver):
        """
        Returns a list of all transmitters, ranked based on proximity to the receiver.

        """
        idx = index.Index()

        for transmitter in self.transmitters.values():
            idx.insert(0, Point(transmitter.coordinates).bounds, transmitter)

        number_of_transmitters = len(self.transmitters.values())

        all_nearest_transmitters =  list(
            idx.nearest(
                Point(receiver.coordinates).bounds, number_of_transmitters, objects='raw'))

        return all_nearest_transmitters

    def calculate_path_loss(self, closest_transmitters, receiver, frequency):

        x2_receiver = receiver.coordinates[0]
        y2_receiver = receiver.coordinates[1]

        x1_transmitter, y1_transmitter = transform_coordinates(Proj(init='epsg:27700'), Proj(init='epsg:4326'),
                                                                closest_transmitters.coordinates[0],
                                                                closest_transmitters.coordinates[1])

        x2_receiver, y2_receiver = transform_coordinates(Proj(init='epsg:27700'), Proj(init='epsg:4326'),
                                                                receiver.coordinates[0],
                                                                receiver.coordinates[1])

        Geo = Geodesic.WGS84
        i_strt_distance = Geo.Inverse(x1_transmitter, y1_transmitter, x2_receiver, y2_receiver)
        interference_strt_distance = int(round(i_strt_distance['s12'], 0))

        ant_height = 20
        ant_type =  'macro'
        settlement_type = 'urban'
        #type_of_sight, building_height, street_width = built_environment_module(transmitter_geom, receiver_geom)
        #type_of_sight = find_line_of_sight(x1_transmitter, y1_transmitter, x2_receiver, y2_receiver)
        type_of_sight = randomly_select_los()
        building_height = 20
        street_width = 20

        path_loss = path_loss_calculator(
            frequency,
            interference_strt_distance,
            ant_height,
            ant_type,
            building_height,
            street_width,
            settlement_type,
            type_of_sight,
            receiver.ue_height)

        return path_loss

    def calc_received_power(self, transmitter, receiver, path_loss):
        """
        Calculate received power based on transmitter and receiver characteristcs, and path loss.
        """

        eirp = float(transmitter.power) + float(transmitter.gain) - float(transmitter.losses)
        received_power = eirp - path_loss - receiver.misc_losses + receiver.gain - receiver.losses

        return received_power

    def calculate_interference(self, nearest_transmitters, receiver, frequency):

        """
        calculate interference from other cells.

        nearest_transmitters contains all transmitters, ranked based on distance, meaning
        we need to select cells 1-3 (as cell 0 is the actual cell in use)
        """

        three_nearest_transmitters = nearest_transmitters[1:4]

        interference = []

        x1_receiver, y1_receiver = transform_coordinates(Proj(init='epsg:27700'),
                                                        Proj(init='epsg:4326'),
                                                        receiver.coordinates[0],
                                                        receiver.coordinates[1])

        #calculate interference from other power sources
        for interference_transmitter in three_nearest_transmitters:

            #get distance
            x2_interference = interference_transmitter.coordinates[0]
            y2_interference = interference_transmitter.coordinates[1]

            x2_interference, y2_interference = transform_coordinates(Proj(init='epsg:27700'),
                                                                    Proj(init='epsg:4326'),
                                                                    interference_transmitter.coordinates[0],
                                                                    interference_transmitter.coordinates[1])

            Geo = Geodesic.WGS84
            i_strt_distance = Geo.Inverse(x2_interference, y2_interference, x1_receiver, y1_receiver)
            interference_strt_distance = int(round(i_strt_distance['s12'], 0))

            ant_height = 20
            ant_type =  'macro'
            building_height = 20
            street_width = 20
            settlement_type = 'urban'
            type_of_sight = randomly_select_los()

            path_loss = path_loss_calculator(
                frequency,
                interference_strt_distance,
                ant_height,
                ant_type,
                building_height,
                street_width,
                settlement_type,
                type_of_sight,
                receiver.ue_height)

            #calc interference from other cells
            received_interference = self.calc_received_power(interference_transmitter, receiver, path_loss)

            #add cell interference to list
            interference.append(received_interference)

        return interference

    def calculate_noise(self, bandwidth):
        #TODO
        """
        Calculate receiver noise (N  = k T B), where k is Boltzmann's constant,
        T is temperatrue in K and B is bandwidth in use.
        """
        k = 1
        T = 15
        B = bandwidth

        fake_noise = k*T*B

        noise = 5

        return noise

    def calculate_sinr(self, received_power, interference, noise):
        """
        Calculate the Signal-to-Interference-plus-Noise-Ration (SINR).
        """
        sinr = round(received_power / sum(interference) + noise, 1)

        return sinr

    def estimate_capacity(self,bandwidth, sinr):
        """
        Estimate wireless link capacity (Mbps) based on bandwidth and receiver signal.
        capacity (Mbps) = bandwidth (MHz) + log2*(1+SINR[dB])
        """
        estimated_capacity = round(bandwidth*np.log2(1+sinr), 2)

        return estimated_capacity

    def transmitter_density(self):
        """Calculate transmitter density per square kilometer (km^2)

        Returns
        -------
        obj
            Sum of transmitters

        Notes
        -----
        Function returns `0` when no transmitters are configered to the area.
        """
        if not self.transmitters:
            return 0

        summed_transmitters = len(
            self.transmitters
        )

        return summed_transmitters

    def receiver_density(self):
        """Calculate receiver density per square kilometer (km^2)

        Returns
        -------
        obj
            Sum of receiver

        Notes
        -----
        Function returns `0` when no receivers are configered to the area.
        """
        if not self.receivers:
            return 0

        summed_receivers = len(
            self.receivers
        )

        return summed_receivers

class Area(object):

    def __init__(self, data):
        #id and geographic info
        self.id = data['properties']["postcode"]
        self.coordinates = data['geometry']["coordinates"]
        self.area = self._calculate_area(data)
        #connections
        self._transmitters = {}
        self._receivers = {}

    def _calculate_area(self, data):
        polygon = shape(data['geometry'])
        area = polygon.area
        return area

    def add_transmitter(self, transmitter):
        self._transmitters[transmitter.id] = transmitter

    def add_receiver(self, receiver):
        self._receivers[receiver.id] = receiver

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

class Receiver(object):
    def __init__(self, data):
        #id and geographic info
        self.id = data['properties']['ue_id']
        #self.transmitter_id = data['properties']['sitengr']
        self.coordinates = data['geometry']["coordinates"]
        #parameters
        self.misc_losses = data['properties']['misc_losses']
        self.gain = data['properties']['gain']
        self.losses = data['properties']['losses']
        self.ue_height = 1.5

def randomly_select_los():
    number = round(np.random.rand(1,1)[0][0], 2)
    if number > 0.5:
        los = 'los'
    else:
        los = 'nlos'
    return los

def transform_coordinates(old_proj, new_proj, x, y):

    new_x, new_y = transform(old_proj, new_proj, x, y)

    return new_x, new_y

def write_results(results, frequency, bandwidth, t_density, r_density, postcode_sector_name):

    suffix = suffix = 'freq_{}_bandwidth_{}_density_{}'.format(frequency, bandwidth, t_density)

    directory = os.path.join(DATA_RESULTS, postcode_sector_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = '{}.csv'.format(suffix)
    directory = os.path.join(directory, filename)

    if not os.path.exists(directory):
        results_file = open(directory, 'w', newline='')
        results_writer = csv.writer(results_file)
        results_writer.writerow(
            ('frequency','bandwidth','t_density','r_density','sinr','throughput'))
    else:
        results_file = open(directory, 'a', newline='')
        results_writer = csv.writer(results_file)

    # output and report results for this timestep
    for result in results:
        # Output metrics
        results_writer.writerow(
            (frequency, bandwidth, t_density, r_density, result['sinr'], result['estimated_capacity']))

    results_file.close()

def write_shapefile(data, postcode_sector_name, filename):

    # Translate props to Fiona sink schema
    prop_schema = []
    for name, value in data[0]['properties'].items():
        fiona_prop_type = next((fiona_type for fiona_type, python_type in fiona.FIELD_TYPES_MAP.items() if python_type == type(value)), None)
        prop_schema.append((name, fiona_prop_type))

    sink_driver = 'ESRI Shapefile'
    sink_crs = {'init': 'epsg:27700'}
    sink_schema = {
        'geometry': data[0]['geometry']['type'],
        'properties': OrderedDict(prop_schema)
    }

    # Create path
    directory = os.path.join(DATA_RESULTS, postcode_sector_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    print(os.path.join(directory, filename))
    # Write all elements to output file
    with fiona.open(os.path.join(directory, filename), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        [sink.write(feature) for feature in data]

def format_data(existing_data, new_data, frequency, bandwidth, postcode_sector_name):

    for datum in new_data:
        existing_data.append({
            'frequency': frequency,
            'bandwidth': bandwidth,
            'sinr': datum['sinr'],
            'capacity': datum['estimated_capacity']
        })

    return existing_data

#####################################
# VISUALISE NETWORK STATS
#####################################

def plot_data(data, frequency, bandwidth, postcode_sector_name):

    sinr = []
    capacity = []

    for datum in data:
        sinr.append(datum['sinr'])
        capacity.append(datum['estimated_capacity'])

    plt.figure()
    plt.scatter(sinr, capacity)

    plt.xlabel("SINR")
    plt.ylabel("Capacity (Mbps)")
    plt.legend(loc='upper left')

    plt.axis((0,30,0,150))

    # Create path
    directory = os.path.join(DATA_RESULTS, postcode_sector_name, 'plots')
    if not os.path.exists(directory):
        os.makedirs(directory)

    plt.savefig(os.path.join(directory, 'freq_{}_bw_{}.png'.format(frequency, bandwidth)))

def joint_plot(data, postcode_sector_name):

    sinr_2_5 = []
    sinr_2_10 = []
    sinr_2_20 = []
    sinr_3p5_5 = []
    sinr_3p5_10 = []
    sinr_3p5_20 = []
    capacity_2_5 = []
    capacity_2_10 = []
    capacity_2_20 = []
    capacity_3p5_5 = []
    capacity_3p5_10 = []
    capacity_3p5_20 = []

    for datum in data:
        if datum['frequency'] == 2 and datum['bandwidth'] == 5:
            sinr_2_5.append(datum['sinr'])
            capacity_2_5.append(datum['capacity'])
        if datum['frequency'] == 2 and datum['bandwidth'] == 10:
            sinr_2_10.append(datum['sinr'])
            capacity_2_10.append(datum['capacity'])
        if datum['frequency'] == 2 and datum['bandwidth'] == 20:
            sinr_2_20.append(datum['sinr'])
            capacity_2_20.append(datum['capacity'])
        if datum['frequency'] == 3.5 and datum['bandwidth'] == 5:
            sinr_3p5_5.append(datum['sinr'])
            capacity_3p5_5.append(datum['capacity'])
        if datum['frequency'] == 3.5 and datum['bandwidth'] == 10:
            sinr_3p5_10.append(datum['sinr'])
            capacity_3p5_10.append(datum['capacity'])
        if datum['frequency'] == 3.5 and datum['bandwidth'] == 20:
            sinr_3p5_20.append(datum['sinr'])
            capacity_3p5_20.append(datum['capacity'])

        #setup and plot
    plt.scatter(sinr_2_5, capacity_2_5, label='5@2GHz ')
    plt.scatter(sinr_2_10, capacity_2_10, label='10@2GHz')
    plt.scatter(sinr_2_20, capacity_2_20, label='20@2GHz')
    plt.scatter(sinr_3p5_5, capacity_3p5_5, label='5@3.5GHz')
    plt.scatter(sinr_3p5_10, capacity_3p5_10, label='10@3.5GHz')
    plt.scatter(sinr_3p5_20, capacity_3p5_20, label='20@3.5GHz')

    plt.xlabel("SINR")
    plt.ylabel("Capacity (Mbps)")
    plt.legend(loc='upper left')

    # Create path
    directory = os.path.join(DATA_RESULTS, postcode_sector_name, 'plots')
    if not os.path.exists(directory):
        os.makedirs(directory)

    plt.savefig(os.path.join(directory, 'panel_plot.png'))

#####################################
# APPLY METHODS
#####################################

if __name__ == "__main__":

    SYSTEM_INPUT = os.path.join('data', 'raw')

    if len(sys.argv) != 2:
        print("Error: no postcode sector provided")
        #print("Usage: {} <postcode>".format(os.path.basename(__file__)))
        exit(-1)

    print('Process ' + sys.argv[1])
    postcode_sector_name = sys.argv[1]
    postcode_sector_abbr = sys.argv[1].replace('postcode_sector_', '')

    #get postcode sector
    geojson_postcode_sector = read_postcode_sector(postcode_sector_name)

    #get list of transmitters
    TRANSMITTERS = get_transmitters(geojson_postcode_sector)

    #generate receivers
    RECEIVERS = generate_receivers(geojson_postcode_sector, 1000)

    joint_plot_data = []

    for frequency, bandwidth in [
        (2, 5),
        (2, 10),
        (2, 20),

        (3.5, 5),
        (3.5, 10),
        (3.5, 20),
        ]:
        print("Running {} GHz with {} MHz bandwidth".format(frequency, bandwidth))

        #load system model with data
        MANAGER = NetworkManager(geojson_postcode_sector, TRANSMITTERS, RECEIVERS)

        results = MANAGER.calc_link_budget(frequency, bandwidth, 10000)
        print('TODO: iterations is not currently doing anything')

        #calculate transmitter density
        t_density = MANAGER.transmitter_density()

        #calculate transmitter density
        r_density = MANAGER.receiver_density()

        write_results(results, frequency, bandwidth, t_density, r_density, postcode_sector_name)

        plot_data(results, frequency, bandwidth, postcode_sector_name)

        format_data(joint_plot_data, results, frequency, bandwidth, postcode_sector_name)

    joint_plot(joint_plot_data, postcode_sector_name)

    print('write cells')
    write_shapefile(TRANSMITTERS,  postcode_sector_name, 'transmitters.shp')

    print('write receivers')
    write_shapefile(RECEIVERS,  postcode_sector_name, 'receivers.shp')

    print('write cells')
    geojson_postcode_sector_list = []
    geojson_postcode_sector_list.append(geojson_postcode_sector)
    write_shapefile(geojson_postcode_sector_list,  postcode_sector_name, '_boundary.shp')
