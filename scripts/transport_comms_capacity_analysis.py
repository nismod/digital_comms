import os
from pprint import pprint
import configparser
import csv
import fiona
import numpy as np

from itertools import groupby
from operator import itemgetter


CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# SETUP FILE LOCATIONS
#####################################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'raw')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'processed')

OS_DATA_IN = os.path.join('D:\\open_signal')
OS_DATA_OUT = os.path.join('D:\\open_signal\\chunks')

#####################################
# IMPORT SUPPLY SIDE DATA
#####################################

reader = csv.DictReader(open(os.path.join(OS_DATA_IN, 'core_gbr_all_opensignal_20170201_20170301.csv'), 'r', encoding='utf8', errors='ignore'))
#reader = csv.reader(open(os.path.join(CAMBRIDGE_OS_DATA, 'chunk_1.csv'), 'r'))

def gen_chunks(reader, chunksize=1000000):
    """ 
    Chunk generator. Take a CSV `reader` and yield
    `chunksize` sized slices. 
    """
    chunk = []

    for i, line in enumerate(reader):
        if (i % chunksize == 0 and i > 0):
            yield chunk
            del chunk[:]
        chunk.append(line)
    
    yield chunk

unique_site_data = []

def write_chunks(data_structure):
    
    i = 0
    for chunk in gen_chunks(reader):
        for line in chunk[1:]:
            #print(line)
            #if line[64] != 'null':# and line[21] != 'null' and line[64] != 'null' and line[67] != 'null':
            data_structure.append({
                'latitude': (line['latitude']),
                'longitude': (line['longitude']),
                'lte_ci': line['lte_ci'],
                'lte_pci': line['lte_pci'],
                })

        data_structure = list({v['lte_ci']:v for v in data_structure}.values())
        
        with open(os.path.join(OS_DATA_OUT, 'chunk_{}.csv'.format(i)), 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
            writer.writeheader()
            writer.writerows(data_structure)
            i += 1

fieldnames = ['latitude', 'longitude', 'lte_ci', 'lte_pci']
write_chunks(unique_site_data)





# #####################################
# # IMPORT SUPPLY SIDE DATA
# #####################################

# CAMBRIDGE_OS_DATA = os.path.join(SYSTEM_INPUT_FIXED, 'received_signal_data', 'Cambridge', 'subset')

# #reader = csv.reader(open(os.path.join(OS_DATA_IN, 'core_gbr_all_opensignal_20170201_20170301.csv'), 'r'))
# reader = csv.reader(open(os.path.join(CAMBRIDGE_OS_DATA, 'chunk_1.csv'), 'r'))

# def gen_chunks(reader, chunksize=1000):
#     """ 
#     Chunk generator. Take a CSV `reader` and yield
#     `chunksize` sized slices. 
#     """
#     chunk = []

#     for i, line in enumerate(reader):
#         if (i % chunksize == 0 and i > 0):
#             yield chunk
#             del chunk[:]
#         chunk.append(line)
    
#     yield chunk

# unique_site_data = []

# def write_chunks(data_structure):
    
#     i = 0
#     for chunk in gen_chunks(reader):
#         for line in chunk[1:]:
#             #print(line)
#             #if line[64] != 'null':# and line[21] != 'null' and line[64] != 'null' and line[67] != 'null':
#             data_structure.append({
#                 'latitude': (line[21]),
#                 'longitude': (line[22]),
#                 'lte_ci': line[65],
#                 'lte_pci': line[68],
#                 })

#         data_structure = list({v['lte_ci']:v for v in data_structure}.values())
#         #print(data_structure)
#         with open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'chunk_{}.csv'.format(i)), 'w') as csv_file:
#             writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
#             writer.writeheader()
#             writer.writerows(data_structure)
#             i += 1

# fieldnames = ['latitude', 'longitude', 'lte_ci', 'lte_pci']
# write_chunks(unique_site_data)






















# def import_data():

#     unique_site_data = []

#     CAMBRIDGE_OS_DATA = os.path.join(SYSTEM_INPUT_FIXED, 'received_signal_data', 'Cambridge', 'subset')

#     for x in os.listdir(CAMBRIDGE_OS_DATA):
#         with open(os.path.join(CAMBRIDGE_OS_DATA, x), 'r', encoding='utf8', errors='replace') as system_file:
#             reader = csv.DictReader(system_file)
#             for row in reader:
#                 unique_site_data.append({
#                     'latitude': float(row['latitude']),
#                     'longitude': float(row['longitude']),
#                     'lte_ci': row['lte_ci'],
#                     'lte_pci': row['lte_pci'],
#                     })
            
#             unique_site_data = list({v['lte_ci']:v for v in unique_site_data}.values())

#     return unique_site_data


# unique_sites = import_data()






# print(lte_pci)
# def getstuff(filename):
    
#     unique_site_data = []
    
#     with open(os.path.join(SYSTEM_INPUT_FIXED, 'received_signal_data', 'Cambridge', filename), 'r', encoding='utf8', errors='replace') as system_file:
#             reader = csv.DictReader(system_file)
#             next(reader)
#             for line in reader:              
#                 #print(line)
#                 # if line['lte_pci'] == 'null':
#                 #     pass
#                 # else:
#                 for site in unique_site_data:
#                     #print(line)
#                     for index in range(len(unique_site_data)):   
#                         if not any (line['lte_pci'] == site[index]['lte_pci'] for site in unique_site_data):
#                         #elif not any (line['lte_pci'] == line[index]['lte_pci'] for line in unique_site_data):
#                             unique_site_data.append({
#                                 'latitude': float(line['latitude']),
#                                 'longitude': float(line['longitude']),
#                                 'lte_ci': line['lte_ci'],
#                                 'lte_pci': line['lte_pci'],
#                                 #'network_id': line[90],
#                                 #'network_name': line[92],
#                                 })
#                         else:
#                             pass
                                
#     return unique_site_data



# print('write unique sites')
# fieldnames = ['latitude', 'longitude', 'lte_ci', 'lte_pci']#, 'network_id', 'network_name']
# csv_writer(unique_sites, 'unique_os_sites.csv')

# def write_shapefile(data, path):

#     # Translate props to Fiona sink schema
#     prop_schema = []
    
#     for name, value in data[0]['properties'].items():
#         fiona_prop_type = next((fiona_type for fiona_type, python_type in fiona.FIELD_TYPES_MAP.items() if python_type == type(value)), None)
#         prop_schema.append((name, fiona_prop_type))
    
#     sink_driver = 'ESRI Shapefile'
#     sink_crs = {'init': 'epsg:27700'}
#     sink_schema = {
#         'geometry': data[0]['geometry']['type'],
#         'properties': OrderedDict(prop_schema)
#     }

#     with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, path), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
#         for datum in data:
#             sink.write(datum)

# unique_sites = getstuff('final.csv')

# print('write unique sites')
# write_shapefile(unique_sites, 'unique_os_sites.shp')

# def remove_missing_counts(data):

#     my_data = []

#     for road in data:
#         if int(road['length']) >= 0:
#             my_data.append({
#                 'road': road['road'],
#                 'length': road['length'],
#                 'function': road['function'],         
#             })
#         else:
#             pass

#     return my_data

# print("remove any missing counts")
# aggegated_road_statistics = remove_missing_counts(aggegated_road_statistics)   

# #####################################
# # 
# #####################################

# def length_of_road_by_type(data):

#     roads = defaultdict(list)
#     length_of_roads = defaultdict(dict)

#     for road in data:
#         roads[road['properties']['formOfWay']].append(road['properties']['length'])

#     for road in roads.keys():
#         summed_length_of_road = sum(roads[road])

#         length_of_roads[road] = {
#             'type_of_road': road,
#             'length_of_road': summed_length_of_road
#         }

#     return length_of_roads

# def calculate_road_length(data):

#     roads = defaultdict(list)
#     length_of_roads = defaultdict(dict)

#     for road in data:
          
#         roads[road['properties']['roadNumber']].append(road['properties']['length'])

#     for road in roads.keys():

#         summed_length_of_road = sum(roads[road])

#         length_of_roads[road] = {
#             'length_of_road': summed_length_of_road
#         }

#     return length_of_roads

# def add_buffer_to_road_network(data):

#     buffered_road_network = []

#     for road in data:
#         #print(road['geometry'])
        
#         buffered_road_network.append({
#             'properties': {
#             'class': road['properties']['class'],
#             'roadNumber': road['properties']['roadNumber'],
#             'formOfWay': road['properties']['formOfWay'],
#             'length': road['properties']['length'],
#             'primary': road['properties']['primary'],
#             'trunkRoad': road['properties']['trunkRoad'],
#             'loop': road['properties']['loop'],
#             'startNode': road['properties']['startNode'],            
#             'endNode': road['properties']['endNode'],
#             'function': road['properties']['function'],
#             },
#             'geometry': mapping(shape(road['geometry']).buffer(0.0005))
#         })

#     return buffered_road_network

# #####################################
# # IMPORT DEMAND SIDE DATA
# #####################################

# def read_in_received_signal_data(data, network):

#     received_signal_data = []

#     with open(os.path.join(SYSTEM_INPUT_FIXED, 'received_signal_data', 'Cambridge', data), 'r', encoding='utf8', errors='replace') as system_file:
#         reader = csv.reader(system_file)
#         next(reader)
#         for line in reader:
#             #select O2, Voda, EE and 3
#             if line[69] != 'null': 
#                 if line[90] == network:
#                     received_signal_data.append({
#                         'type': "Feature",
#                         'geometry': {
#                             "type": "Point",
#                             "coordinates": [float(line[23]), float(line[22])]
#                         },
#                         'properties': {
#                             'time': line[16],
#                             'altitude': line[19],
#                             'loc_bearing': line[20],
#                             'loc_speed': line[21],           
#                             'loc_provider': line[24],                 
#                             'loc_sat': line[25], 
#                             'lte_rsrp': line[36],                 
#                             'lte_rsrq': line[37],                 
#                             'lte_rssnr': line[38],
#                             'lte_ci': line[66],
#                             'lte_mcc': line[67],
#                             'lte_mnc': line[68],
#                             'lte_pci': line[69],
#                             'lte_tac': line[70],
#                             'network_type': line[84],
#                             'network_id': line[90],
#                             'network_id_sim': line[91],
#                             'network_name': line[92],
#                             'network_name_sim': line[93]
#                         }
#                         })
    
#     return received_signal_data


# def add_road_id_to_points(recieved_signal_data, road_polygons):

#     joined_points = []

#     # Initialze Rtree
#     idx = index.Index()

#     for rtree_idx, received_point in enumerate(recieved_signal_data):
#         idx.insert(rtree_idx, shape(received_point['geometry']).bounds, received_point)

#     # Join the two
#     for road in road_polygons:
#         for n in idx.intersection((shape(road['geometry']).bounds), objects=True):
#             road_area_shape = shape(road['geometry'])
#             road_shape = shape(n.object['geometry'])
#             if road_area_shape.contains(road_shape):
#                 n.object['properties']['roadNumber'] = road['properties']['roadNumber']
#                 joined_points.append(n.object)

#     return joined_points

# def calculate_unique_sites_per_road(data):

#     sites_per_road = defaultdict(list)
#     unique_sites = defaultdict(dict)

#     for point in data:
          
#         sites_per_road[point['properties']['roadNumber']].append(point['properties']['lte_pci'])
    
#     for road in sites_per_road.keys():

#         number_of_unique_sites = len(set(sites_per_road[road])) 

#         if number_of_unique_sites > 0:
        
#             unique_sites[road] = {
#                 'unique_sites': number_of_unique_sites
#             }

#         else:
#             unique_sites[road] = {
#                 'unique_sites': 0
#             }

#     return unique_sites

# def calculate_site_densities(data):

#     for road in data:
        
#         try:
#             road['site_density'] =  round(road['length_of_road'] / road['unique_sites'], 1) 
        
#         except:
#             print("did not match {}".format(road))

#     return data 

# #####################################
# # 
# #####################################

# print('summing length by groups')
# road_length_by_type = grouper(road_network, length, )

# print("calculate distance by road type")
# road_length_by_type = length_of_road_by_type(road_network)

# print("calculating length of roads in road network")
# road_lengths = calculate_road_length(road_network)

# print('converting road network projection into wgs84')
# road_network = convert_projection(road_network)

# print('write road network')
# write_shapefile(road_network, 'road_network.shp')

# print("converting road lengths to list of dicts structure")
# road_lengths = covert_data_into_list_of_dicts(road_lengths, 'roadName', 'length_of_road')

# print("adding buffer to road network")
# road_network = add_buffer_to_road_network(road_network)



# for network, name in [
#         ('23410', 'O2'),
#         #('23415', 'Voda'),
#         #('23430', 'EE'),
#         #('23420', '3')
#     ]:

#     print("Running:", name)

#     print('read in data')
#     received_signal_points = read_in_received_signal_data('final.csv', network)

#     print("adding road ids to points along the strategic road network ")
#     received_signal_points = add_road_id_to_points(received_signal_points, road_network)

#     print("calculating unique sites per road")
#     unique_sites = calculate_unique_sites_per_road(received_signal_points)

#     print('converting site densities to list of dicts structure')
#     unique_sites = covert_data_into_list_of_dicts(unique_sites, 'roadName', 'unique_sites')

#     print('merging site densities and road lengths')
#     road_site_density = merge_two_list_of_dicts(unique_sites, road_lengths, 'roadName')
    
#     print('calculating site densities per km2')
#     road_site_density = calculate_site_densities(road_site_density)

#     print('write data points')
#     fieldnames = ['roadName', 'length_of_road', 'unique_sites', 'site_density']
#     csv_writer(road_site_density, fieldnames, 'road_site_densities.csv')

