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


def read_exchanges():
    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'assets_layer2_exchanges.shp'), 'r') as source:
        return [exchange for exchange in source]

def read_city_exchange_geotype_lut():

    exchange_geotypes = []
    with open(os.path.join(SYSTEM_INPUT_FIXED, 'exchange_geotype_lut', 'exchange_geotype_lut.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)    
        for line in reader:
            exchange_geotypes.append({
                'lad': line[0],
                'geotype': line[1],                
            })

    return exchange_geotypes

def add_urban_geotype_to_exchanges(exchanges, exchange_geotype_lut):

    # Process lookup into dictionary
    exchange_geotypes = {}
    for lad in exchange_geotype_lut:
        exchange_geotypes[lad['lad']] = lad
        del exchange_geotypes[lad['lad']]['lad']

    # Add properties
    for exchange in exchanges:
        if exchange['properties']['lad'] in exchange_geotypes:
            print(exchange)
            exchange['properties'].update({
                'geotype': exchange_geotypes[exchange['properties']['lad']]['geotype'],

            })
        else:
            exchange['properties'].update({
                'geotype': 'other', 
            })
    
    return exchanges

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


print("reading exchanges")
geojson_layer2_exchanges = read_exchanges()
#print(geojson_layer2_exchanges)

print("reading lut")
city_exchange_lad_lut = read_city_exchange_geotype_lut()
#print(exchange_geotype_lut)

print('merge geotype info by LAD to exchanges')
geojson_layer2_exchanges = add_urban_geotype_to_exchanges(geojson_layer2_exchanges, city_exchange_lad_lut)
#print(geojson_layer2_exchanges)

print('write exchanges')
# for exchange in geojson_layer2_exchanges:
#     if exchange['properties']['geotype'] != 0:
#         print(exchange)
write_shapefile(geojson_layer2_exchanges, 'assets_layer2_exchanges.shp')