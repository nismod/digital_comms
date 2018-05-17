import os
from pprint import pprint
import configparser
import csv
import fiona
import numpy as np
import random 

from shapely.geometry import shape, Point, LineString, Polygon, MultiPolygon, mapping
from rtree import index

from collections import OrderedDict, defaultdict

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# SETUP FILE LOCATIONS
#####################################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'raw')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'processed')
SYSTEM_INPUT_NETWORK = os.path.join(SYSTEM_INPUT_FIXED, 'network_hierarchy_data')

#####################################
# SPECIFY FUNCTIONS
#####################################

def read_exchange_boundaries():
    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, '_exchange_areas.shp'), 'r') as source:
        return [boundary for boundary in source]

def read_postcode_boundaries():

    postcode_shapes = []
    
    for dirpath, subdirs, files in os.walk(os.path.join(SYSTEM_INPUT_FIXED, 'codepoint', 'codepoint-poly_2429451', 'cambridge_city')):
        for x in files:
            #print(files)
            if x.endswith(".shp"):
                with fiona.open(os.path.join(dirpath, x), 'r') as source:
                    postcode_shapes.extend([boundary for boundary in source])

    for postcode in postcode_shapes:
            centroid = shape(postcode['geometry']).centroid
            postcode['geometry'] = mapping(centroid)

    return postcode_shapes


def read_codepoint_lut():

    codepoint_lut_data = []

    SYSTEM_INPUT_NETWORK = os.path.join(SYSTEM_INPUT_FIXED,'codepoint', 'codepoint_2429650', 'cambridge')

    for filename in os.listdir(SYSTEM_INPUT_NETWORK):
        with open(os.path.join(SYSTEM_INPUT_NETWORK, filename), 'r', encoding='utf8', errors='replace') as system_file:
            reader = csv.reader(system_file)
            next(reader)    
            for line in reader:
                if line[18] == 'S':
                    codepoint_lut_data.append({
                        'POSTCODE': line[0],          #.replace(' ', ''),
                        'delivery_points': int(line[3]),
                        #'type': line[18],
                    })
                else:
                    pass

    return codepoint_lut_data


def add_codepoint_lut_to_postcode_shapes(data, lut):

    # Process lookup into dictionary
    codepoint_lut_data = {}
    for area in lut:
        codepoint_lut_data[area['POSTCODE']] = area
        del codepoint_lut_data[area['POSTCODE']]['POSTCODE']

    # Add properties
    for datum in data:        
        if datum['properties']['POSTCODE'] in codepoint_lut_data:
            datum['properties'].update({
                'delivery_points': codepoint_lut_data[datum['properties']['POSTCODE']]['delivery_points']
            })
        else:
            datum['properties'].update({
                'delivery_points': 0, 
            })
    
    return data

############################################
# ADD INTERSECTING EXCHANGE IDs TO POSTCODES
############################################

def add_exchange_to_postcodes(postcodes, exchanges):
    
    joined_postcodes = []

    # Initialze Rtree
    idx = index.Index()

    for rtree_idx, postcode in enumerate(postcodes):
        idx.insert(rtree_idx, shape(postcode['geometry']).bounds, postcode)

    # Join the two
    for exchange in exchanges:
        for n in idx.intersection((shape(exchange['geometry']).bounds), objects=True):
            exchange_shape = shape(exchange['geometry'])
            postcode_shape = shape(n.object['geometry'])
            if exchange_shape.contains(postcode_shape):
                n.object['properties']['id'] = exchange['properties']['id']
                joined_postcodes.append(n.object)

    return joined_postcodes

#####################################
# SUM PREMISES BY EXCHANGE
#####################################

def sum_premises_by_exchange():
    
    #group premises by lads
    premises_per_exchange = defaultdict(list)

    for postcode in postcode_centroids:
        """
        'exchange1': [
            postcode1,
            postcode2
        ]
        """
        #print(postcode)
        premises_per_exchange[postcode['properties']['id']].append(postcode['properties']['delivery_points'])

    # run statistics on each lad
    premises_results = defaultdict(dict)
    for exchange in premises_per_exchange.keys():

        #print(lad)
        sum_of_delivery_points = sum([premise for premise in premises_per_exchange[exchange]]) # contain  list of premises objects in the lad

        if sum_of_delivery_points >= 20000:
            geotype = '>20k lines'

        elif sum_of_delivery_points >= 10000 and sum_of_delivery_points < 20000:
            geotype = '>10k lines'            

        elif sum_of_delivery_points >= 3000 and sum_of_delivery_points <= 10000:
            geotype = '>3k lines'     

        elif sum_of_delivery_points >= 1000 and sum_of_delivery_points <= 30000:
            geotype = '>1k lines' 

        elif sum_of_delivery_points < 1000:
            geotype = '<1k lines' 

        premises_results[exchange] = {
            'delivery_points': sum_of_delivery_points,
            'geotype': geotype
        }

    return premises_results

##########################################
# CONVERT DATA INTO LIST OF DICT STRUCTURE 
##########################################

def covert_data_into_list_of_dicts():
    my_data = []

    # output and report results for this timestep
    for exchange in premises_by_exchange:
        my_data.append({
        'exchange_id': exchange,
        'delivery_points': premises_by_exchange[exchange]['delivery_points'],
        'geotype': premises_by_exchange[exchange]['geotype']
        })

    return my_data

#####################################
# WRITE DATA - SINGLE FILE FOR ALL
#####################################

def csv_writer(data, output_fieldnames, filename):
    """
    Write data to a CSV file path
    """
    with open(os.path.join(SYSTEM_OUTPUT_FILENAME, filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, output_fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)

################################################
# run scripts
################################################

print("reading exchange boundaries")
exchange_boundaries = read_exchange_boundaries()

print("reading postcode boundaries")
postcode_centroids = read_postcode_boundaries()

print("reading codepoint lut")
codepoint_lut = read_codepoint_lut()

print("adding codepoint lut to postcode shapes")
postcode_centroids = add_codepoint_lut_to_postcode_shapes(postcode_centroids, codepoint_lut)

print("adding intersecting exchange IDs to postcode points")
postcode_centroids = add_exchange_to_postcodes(postcode_centroids, exchange_boundaries)

print("summing delivery points by exchange area")
premises_by_exchange = sum_premises_by_exchange()

print("convert exchange areas to list of dicts")
premises_by_exchange = covert_data_into_list_of_dicts()

# # Write LUTs
print('write geotype lut')
geotype_lut_fieldnames = ['exchange_id', 'delivery_points', 'geotype']
csv_writer(premises_by_exchange, geotype_lut_fieldnames, 'exchange_geotype_lut.csv')

print("script finished")