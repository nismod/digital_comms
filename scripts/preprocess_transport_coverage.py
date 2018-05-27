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
            if line[69] != 'null': 
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

def calculate_road_length(data):

    roads = defaultdict(list)
    length_of_roads = defaultdict(dict)

    for road in data:
          
        roads[road['properties']['roadNumber']].append(road['properties']['length'])

    for road in roads.keys():

        summed_length_of_road = sum(roads[road])

        length_of_roads[road] = {
            'length_of_road': summed_length_of_road
        }

    return length_of_roads

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

def calculate_unique_sites_per_road(data):

    sites_per_road = defaultdict(list)
    unique_sites = defaultdict(dict)

    for point in data:
          
        sites_per_road[point['properties']['roadNumber']].append(point['properties']['lte_pci'])
    
    for road in sites_per_road.keys():

        number_of_unique_sites = len(set(sites_per_road[road])) 

        if number_of_unique_sites > 0:
        
            unique_sites[road] = {
                'unique_sites': number_of_unique_sites
            }

        else:
            unique_sites[road] = {
                'unique_sites': 0
            }

    return unique_sites

def covert_data_into_list_of_dicts(data, variable1, variable2):
    my_data = []

    # output and report results for this timestep
    for datum in data:
        my_data.append({
        variable1: datum,
        variable2: data[datum][variable2]
        })

    return my_data

def merge_two_list_of_dicts(data1, data2, shared_id):

    d1 = {d[shared_id]:d for d in data1}

    result = [dict(d, **d1.get(d[shared_id], {})) for d in data2]

    return result

def calculate_site_densities(data):

    for road in data:
        
        try:
            road['site_density'] =  round(road['length_of_road'] / road['unique_sites'], 1) 
        
        except:
            print("did not match {}".format(road))

    return data 

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

print("calculating length of roads in road network")
road_lengths = calculate_road_length(road_network)

print("converting road lengths to list of dicts structure")
road_lengths = covert_data_into_list_of_dicts(road_lengths, 'roadName', 'length_of_road')

print("adding buffer to road network")
road_network = add_buffer_to_road_network(road_network)

print('write road network')
write_shapefile(road_network, 'road_network.shp')

for network, name in [
        ('23410', 'O2'),
        #('23415', 'Voda'),
        #('23430', 'EE'),
        #('23420', '3')
    ]:

    print("Running:", name)

    print('read in data')
    received_signal_points = read_in_received_signal_data('final.csv', network)

    print("adding road ids to points along the strategic road network ")
    received_signal_points = add_road_id_to_points(received_signal_points, road_network)

    print("calculating unique sites per road")
    unique_sites = calculate_unique_sites_per_road(received_signal_points)

    print('converting site densities to list of dicts structure')
    unique_sites = covert_data_into_list_of_dicts(unique_sites, 'roadName', 'unique_sites')

    print('merging site densities and road lengths')
    road_site_density = merge_two_list_of_dicts(unique_sites, road_lengths, 'roadName')
    
    print('calculating site densities per km2')
    road_site_density = calculate_site_densities(road_site_density)

    print('write data points')
    fieldnames = ['roadName', 'length_of_road', 'unique_sites', 'site_density']
    csv_writer(road_site_density, fieldnames, 'road_site_densities.csv')

print("script finished")

print("now check the column integer slices were correct for desired columns")

