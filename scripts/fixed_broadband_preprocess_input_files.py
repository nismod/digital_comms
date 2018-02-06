import os
from pprint import pprint
import configparser
import csv
import fiona
from shapely.geometry import Point, mapping
from pyproj import Proj, transform

from collections import OrderedDict

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################
# setup file locations
#####################

SYSTEM_INPUT_FILENAME = os.path.join(BASE_PATH, 'Digital Comms - Fixed broadband model', 'Data')

SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'Digital Comms - Fixed broadband model', 'initial_system')

premises_data = []

#####################
# read in OS AddressBase data
#####################

with open(os.path.join(SYSTEM_INPUT_FILENAME, 'OS Address Point Data from NCL', 'cambridge_points.csv'), 'r') as system_file:
    reader = csv.reader(system_file)
    next(reader)
    for line in reader:
        premises_data.append({
            'id': line[0],
            'oa': line[1],
            'residential_address_count': line[2],
            'non_residential_address_count': line[3],
            'postgis_geom': line[4],
            'eastings': line[5],
            'northings': line[6]
        })

# remove 'None' and replace with '0'
for idx, premise in enumerate(premises_data):
    if premise['residential_address_count'] == 'None':
        premises_data[idx]['residential_address_count'] = '0'
    if premise['non_residential_address_count'] == 'None':
        premises_data[idx]['non_residential_address_count'] = '0'

print(' ')

# write to shapefile
sink_driver = 'ESRI Shapefile'
sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

setup_point_schema = {
    'geometry': 'Point',
    'properties': OrderedDict([('id', 'int'), ('oa', 'str'), ('residential_address_count', 'int'),
                                ('non_residential_address_count', 'int'), ('postgis_geom', 'str')])
}

#Define a projection with Proj4 notation, in this case an Icelandic grid
osgb36=Proj("+init=EPSG:27700") # UK Ordnance Survey, 1936 datum
wgs84=Proj("+init=EPSG:4326") # LatLon with WGS84

with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'premises_points_data.shp'), 'w', driver=sink_driver, crs=sink_crs, schema=setup_point_schema) as sink:
    for premise in premises_data:
        xx, yy = transform(osgb36, wgs84, float(premise['eastings']), float(premise['northings']))
        sink.write({
        #    'geometry': {'type': "Point", 'coordinates': [float(premise['eastings']), float(premise['northings'])]},
            'geometry': {'type': "Point", 'coordinates': [xx, yy]},
            'properties': OrderedDict([('id', premise['id']), ('oa', premise['oa']),
                                        ('residential_address_count', premise['residential_address_count']),
                                        ('non_residential_address_count', premise['non_residential_address_count']),
                                        ('postgis_geom', premise['postgis_geom'])])
        })

#BGS coordinate systems
#27700
#7405


# Convert x, y from isn2004 to UTM27N

exchanges_data = []

#####################
# read in exchange data
#####################

with open(os.path.join(SYSTEM_INPUT_FILENAME, 'exchanges', 'final_exchange_pcds.csv'), 'r') as system_file:
    reader = csv.reader(system_file)
    next(reader)
    for line in reader:
        exchanges_data.append({
            'exchange_pcd': line[0],
            'OLO': line[1],
            'name': line[2],
            'region': line[3],
            'county': line[4],
            'eastings': line[5],
            'northings': line[6]
        })

# write to shapefile
sink_driver = 'ESRI Shapefile'
sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

setup_point_schema = {
    'geometry': 'Point',
    'properties': OrderedDict([('exchange_pcd', 'str'), ('OLO', 'str'), ('name', 'str'),
                                ('region', 'str'), ('county', 'str')])
}

with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'exchanges_points_data.shp'), 'w', driver=sink_driver, crs=sink_crs, schema=setup_point_schema) as sink:
    for exchange in exchanges_data:
        xx, yy = transform(osgb36, wgs84, float(exchange['eastings']), float(exchange['northings']))
        sink.write({
            #'geometry': {'type': "Point", 'coordinates': [float(exchange['eastings']), float(exchange['northings'])]},
            'geometry': {'type': "Point", 'coordinates': [xx, yy]},
            'properties': OrderedDict([('exchange_pcd', exchange['exchange_pcd']), ('OLO', exchange['OLO']),
                                        ('name', exchange['name']), ('region', exchange['region']),
                                        ('county', exchange['county'])])
        })



















