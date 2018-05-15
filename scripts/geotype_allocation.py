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
# setup file locations and data files
#####################################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'raw')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'processed')
SYSTEM_INPUT_NETWORK = os.path.join(SYSTEM_INPUT_FIXED, 'network_hierarchy_data')


def read_exchange_boundaries():
    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, '_exchange_areas.shp'), 'r') as source:
        return [boundary for boundary in source]

def read_postcode_boundaries():

    postcode_shapes = []
    
    for dirpath, subdirs, files in os.walk(SYSTEM_INPUT_FIXED, 'codepoint', 'codepoint-poly_2429451', 'cambridge_city'):
        for x in files:
            if x.endswith(".shp"):
                with fiona.open(os.path.join(dirpath, x), 'r') as source:
                    postcode_shapes.extend([boundary for boundary in source])

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
            print(datum)
            datum['properties'].update({
                'premises': codepoint_lut_data[datum['properties']['POSTCODE']]['delivery_points']
            })
        else:
            datum['properties'].update({
                'premises': 0, 
            })
    
    return data

#####################################
# SUM PREMISES BY EXCHANGE
#####################################

# # group premises by lads
# premises_per_lad = defaultdict(list)

# for premise in self._premises:
#     """
#     'Cambridge': [
#         premise1,
#         premise2
#     ]
#     """
#     premises_per_lad[premise.lad].append(premise)


# # run statistics on each lad
# coverage_results = defaultdict(dict)
# for lad in premises_per_lad.keys():

#     # return dict that looks like
#     """
#     dict of dicts
#     'Cambridge' : {
#         'premise_with_fttp': int, 
#         'premise_with_fttdp': int, 
#         'premise_with_fttc': int, 
#         'premise_with_adsl': int, 
#         'premise_with_cable': int,
#     },
#     'Oxford' : ..
#     """

#     #print(lad)
#     sum_of_fttp = sum([premise.fttp for premise in premises_per_lad[lad]]) # contain  list of premises objects in the lad
#     sum_of_gfast = sum([premise.gfast for premise in premises_per_lad[lad]]) # contain  list of premises objects in the lad
#     sum_of_fttc = sum([premise.fttc for premise in premises_per_lad[lad]]) # contain  list of premises objects in the lad
#     sum_of_adsl = sum([premise.adsl for premise in premises_per_lad[lad]]) # contain  list of premises objects in the lad
    
#     sum_of_premises = len(premises_per_lad[lad]) # contain  list of premises objects in the lad

#     coverage_results[lad] = {
#         'percentage_of_premises_with_fttp': round(sum_of_fttp / sum_of_premises, 2),
#         'percentage_of_premises_with_gfast': round(sum_of_gfast / sum_of_premises, 2),
#         'percentage_of_premises_with_fttc': round(sum_of_fttc / sum_of_premises, 2),
#         'percentage_of_premises_with_adsl': round(sum_of_adsl / sum_of_premises, 2)
#     }

# return coverage_results

#####################################
# WRITE LUTS/ASSETS/LINKS
#####################################

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

    # Write all elements to output file
    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, path), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        for feature in data:
            sink.write(feature)

################################################
# run scripts
################################################

print("reading exchange boundaries")
exchange_boundaries = read_exchange_boundaries()

print("reading postcode boundaries")
postcode_boundaries = read_postcode_boundaries()

print("reading codepoint lut")
codepoint_lut = read_codepoint_lut()

print("adding codepoint lut to postcode shapes")
postcode_boundaries = add_codepoint_lut_to_postcode_shapes(postcode_boundaries, codepoint_lut)

#print(codepoint_lut)

print("write exchanges")
write_shapefile(postcode_boundaries, 'postcode_geotype_shapes.shp')