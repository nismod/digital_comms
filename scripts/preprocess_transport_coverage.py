import os
from pprint import pprint
import configparser
import csv
import fiona
import numpy as np

from rtree import index
from shapely.geometry import shape, Point, LineString, Polygon, mapping
from collections import OrderedDict, defaultdict
from pyproj import Proj, transform

#import pyproj
# from functools import partial
# import pyproj
# from shapely.ops import transform

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# SETUP FILE LOCATIONS
#####################################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'raw')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'processed')

#####################################
# IMPORT DATA
#####################################

def read_in_received_signal_data(data, network):

    received_signal_data = []

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'received_signal_data', 'Cambridge', data), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            #select O2, Voda, EE and 3
            if line[90] == network: 
                received_signal_data.append({
                    'type': "Feature",
                    'geometry': {
                        "type": "Point",
                        "coordinates": [float(line[23]), float(line[22])]
                    },
                    'properties': {
                        'time': line[16],
                        'altitude': line[19],
                        'loc_bearing': line[20],
                        'loc_speed': line[21],           
                        'loc_provider': line[24],                 
                        'loc_sat': line[25], 
                        'lte_rsrp': line[36],                 
                        'lte_rsrq': line[37],                 
                        'lte_rssnr': line[38],
                        'lte_ci': line[66],
                        'lte_mcc': line[67],
                        'lte_mnc': line[68],
                        'lte_pci': line[69],
                        'lte_tac': line[70],
                        'network_type': line[84],
                        'network_id': line[90],
                        'network_id_sim': line[91],
                        'network_name': line[92],
                        'network_name_sim': line[93]
                    }
                    })
    
    return received_signal_data

    # with open(os.path.join(SYSTEM_INPUT_FIXED, 'layer_2_exchanges', 'final_exchange_pcds.csv'), 'r') as system_file:
    #     reader = csv.reader(system_file)
    #     next(reader)
    
    #     for line in reader:
    #         exchanges.append({
    #             'type': "Feature",
    #             'geometry': {
    #                 "type": "Point",
    #                 "coordinates": [float(line[5]), float(line[6])]
    #             },
    #             'properties': {
    #                 'id': 'exchange_' + line[1],
    #                 'Name': line[2],
    #                 'pcd': line[0],
    #                 'Region': line[3],
    #                 'County': line[4]
    #             }
    #         })

    # return exchanges

def read_in_os_open_roads():

    open_roads_network = []

    with fiona.open(os.path.join(SYSTEM_INPUT_FIXED, 'os_open_roads', 'open-roads_2438901_cambridge', 'TL_RoadLink_cambridge_city.shp'), 'r') as source:
        for src_shape in source:   
            open_roads_network.extend([src_shape for src_shape in source if src_shape['properties']['class'] == 'Motorway' or src_shape['properties']['class'] == 'A Road' or src_shape['properties']['class'] == 'B Road']) 

        for element in open_roads_network:
            del element['properties']['name1'],
            del element['properties']['name1_lang'],
            del element['properties']['name2'],
            del element['properties']['name2_lang'],
            del element['properties']['structure'],
            del element['properties']['nameTOID'],
            del element['properties']['numberTOID'],

    return open_roads_network

def convert_projection(data):

    converted_data = []

    projOSGB1936 = Proj(init='epsg:27700')
    projWGS84 = Proj(init='epsg:4326')

    for feature in data:

        new_geom = []
        coords = feature['geometry']['coordinates']

        for coordList in coords:
            

            coordList = list(transform(projOSGB1936, projWGS84, coordList[0], coordList[1]))

            new_geom.append(coordList)
               
        feature['geometry']['coordinates'] = new_geom

        converted_data.append(feature)
        
    return converted_data

def add_buffer_to_road_network(data):

    buffered_road_network = []

    for road in data:
        #print(road['geometry'])
        
        buffered_road_network.append({
            'properties': {
            'class': road['properties']['class'],
            'roadNumber': road['properties']['roadNumber'],
            'formOfWay': road['properties']['formOfWay'],
            'length': road['properties']['length'],
            'primary': road['properties']['primary'],
            'trunkRoad': road['properties']['trunkRoad'],
            'loop': road['properties']['loop'],
            'startNode': road['properties']['startNode'],            
            'endNode': road['properties']['endNode'],
            'function': road['properties']['function'],
            },
            'geometry': mapping(shape(road['geometry']).buffer(0.0005))
        })

    return buffered_road_network

def add_road_id_to_points(recieved_signal_data, road_polygons):

    joined_points = []

    # Initialze Rtree
    idx = index.Index()

    for rtree_idx, received_point in enumerate(recieved_signal_data):
        idx.insert(rtree_idx, shape(received_point['geometry']).bounds, received_point)

    # Join the two
    for road in road_polygons:
        for n in idx.intersection((shape(road['geometry']).bounds), objects=True):
            road_area_shape = shape(road['geometry'])
            road_shape = shape(n.object['geometry'])
            if road_area_shape.contains(road_shape):
                n.object['properties']['roadNumber'] = road['properties']['roadNumber']
                joined_points.append(n.object)

    return joined_points

#####################################
# WRITE LOOK UP TABLE (LUT) DATA
#####################################

def csv_writer(data, output_fieldnames, filename):
    """
    Write data to a CSV file path
    """
    fieldnames = data[0].keys()
    with open(os.path.join(SYSTEM_OUTPUT_FILENAME, filename),'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)

def write_shapefile(data, path):

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

    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, path), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        for datum in data:
            sink.write(datum)

#####################################
# RUN SCRIPTS
#####################################

print('read in road network')
road_network = read_in_os_open_roads()

print('converting road network projection into wgs84')
road_network = convert_projection(road_network)

print("adding buffer to road network")
road_network = add_buffer_to_road_network(road_network)

print('write road network')
write_shapefile(road_network, 'road_network.shp')

for network, name in [
        ('23410', 'O2'),
        ('23415', 'Voda'),
        ('23430', 'EE'),
        ('23420', '3')
    ]:

    print("Running:", name)

    print('read in data')
    received_signal_points = read_in_received_signal_data('final.csv', network)

    print("adding road ids to points along the strategic road network ")
    received_signal_points = add_road_id_to_points(received_signal_points, road_network)

    print('write data points')
    write_shapefile(received_signal_points, '{}_received_signal_points.shp'.format(name))

print("script finished")

print("now check the column integer slices were correct for desired columns")