import os
from pprint import pprint
import configparser
import csv
import fiona
import numpy as np
from shapely.geometry import Point, mapping
from pyproj import Proj, transform
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering

from collections import OrderedDict

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################
# setup file locations
#####################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'Digital Comms - Fixed broadband model', 'Data')
SYSTEM_INPUT_CAMBRIDGE = os.path.join(BASE_PATH, 'cambridge_shape_file_analysis', 'Data')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'Digital Comms - Fixed broadband model', 'Data', 'input_shapefiles')

def read_premises():
    premises_data = []

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'OS Address Point Data from NCL', 'cambridge_points.csv'), 'r') as system_file:
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

    return premises_data


def write_premises(premises_data):
    # write to shapefile
    sink_driver = 'ESRI Shapefile'
    sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

    setup_point_schema = {
        'geometry': 'Point',
        'properties': OrderedDict([('Name', 'int'), ('oa', 'str'), ('residential_address_count', 'int'),
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
                'properties': OrderedDict([('Name', premise['id']), ('oa', premise['oa']),
                                            ('residential_address_count', premise['residential_address_count']),
                                            ('non_residential_address_count', premise['non_residential_address_count']),
                                            ('postgis_geom', premise['postgis_geom'])])
            })


def read_cabinets():
    cabinets_data = []

    with open(os.path.join(SYSTEM_INPUT_CAMBRIDGE, 'pcd_2_cab_2_exchange_data_cambridge.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader)

        for line in reader:
            if line[0] in ['EACAM', 'EACRH', 'EAHIS', 'EAMD']:
                cabinets_data.append({
                    'OLO': line[0],
                    'pcd': line[1],
                    'SAU_NODE_ID': line[2],
                    'easting': line[3],
                    'northing': line[4],
                })

    return cabinets_data


def write_cabinets(cabinets_data):
    # write to shapefile
    sink_driver = 'ESRI Shapefile'
    sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

    setup_point_schema = {
        'geometry': 'Point',
        'properties': OrderedDict([('Name', 'str'), ('OLO', 'str'), ('pcd', 'str')])
    }

    #Define a projection with Proj4 notation, in this case an Icelandic grid
    osgb36=Proj("+init=EPSG:27700") # UK Ordnance Survey, 1936 datum
    wgs84=Proj("+init=EPSG:4326") # LatLon with WGS84

    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'cabinets_points_data.shp'), 'w', driver=sink_driver, crs=sink_crs, schema=setup_point_schema) as sink:
        for cabinet in cabinets_data:
            xx, yy = transform(osgb36, wgs84, float(cabinet['easting']), float(cabinet['northing']))
            sink.write({
                #'geometry': {'type': "Point", 'coordinates': [float(cabinet['eastings']), float(cabinet['northings'])]},
                'geometry': {'type': "Point", 'coordinates': [xx, yy]},
                'properties': OrderedDict([('Name', cabinet['SAU_NODE_ID']), ('OLO', cabinet['OLO']),
                                            ('pcd', cabinet['pcd'])])
            })


def estimate_pcps(cabinets):
    """Estimate pcp locations based on the number of cabinets that are served.

    Parameters
    ----------
    cabinets: list of dict
        List of cabinets, each providing a dict with properties and location of the cabinet

    Returns
    -------
    pcp: list of dict
        List of pcps
    """
    print('start pcp estimation')

    points = np.vstack([[float(cabinet['northing']), float(cabinet['easting'])] for cabinet in cabinets])
    number_of_clusters = int(points.shape[0] / 8)

    kmeans = KMeans(n_clusters=number_of_clusters, random_state=0).fit(points)

    print('end pcp estimation')

    pcps = []
    for idx, pcp_location in enumerate(kmeans.cluster_centers_):
        pcps.append({
            'id': idx,
            'northings': pcp_location[0],
            'eastings': pcp_location[1]
        })
    return pcps


def write_pcps(pcps_data):
    # write to shapefile
    sink_driver = 'ESRI Shapefile'
    sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

    setup_point_schema = {
        'geometry': 'Point',
        'properties': OrderedDict([('Name', 'str')])
    }

    #Define a projection with Proj4 notation, in this case an Icelandic grid
    osgb36=Proj("+init=EPSG:27700") # UK Ordnance Survey, 1936 datum
    wgs84=Proj("+init=EPSG:4326") # LatLon with WGS84

    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'pcps_points_data.shp'), 'w', driver=sink_driver, crs=sink_crs, schema=setup_point_schema) as sink:
        for pcp in pcps_data:
            xx, yy = transform(osgb36, wgs84, float(pcp['eastings']), float(pcp['northings']))
            sink.write({
                #'geometry': {'type': "Point", 'coordinates': [float(pcp['eastings']), float(pcp['northings'])]},
                'geometry': {'type': "Point", 'coordinates': [xx, yy]},
                'properties': OrderedDict([('Name', pcp['id'])])
            })


def read_exchanges():
    exchanges_data = []

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'exchanges', 'final_exchange_pcds.csv'), 'r') as system_file:
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

    return exchanges_data


def write_exchanges(exchanges_data):
    # write to shapefile
    sink_driver = 'ESRI Shapefile'
    sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

    setup_point_schema = {
        'geometry': 'Point',
        'properties': OrderedDict([('Name', 'str'), ('OLO', 'str'), ('name', 'str'),
                                    ('region', 'str'), ('county', 'str')])
    }

    #Define a projection with Proj4 notation, in this case an Icelandic grid
    osgb36=Proj("+init=EPSG:27700") # UK Ordnance Survey, 1936 datum
    wgs84=Proj("+init=EPSG:4326") # LatLon with WGS84

    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'exchanges_points_data.shp'), 'w', driver=sink_driver, crs=sink_crs, schema=setup_point_schema) as sink:
        for exchange in exchanges_data:
            xx, yy = transform(osgb36, wgs84, float(exchange['eastings']), float(exchange['northings']))
            sink.write({
                #'geometry': {'type': "Point", 'coordinates': [float(exchange['eastings']), float(exchange['northings'])]},
                'geometry': {'type': "Point", 'coordinates': [xx, yy]},
                'properties': OrderedDict([('Name', exchange['exchange_pcd']), ('OLO', exchange['OLO']),
                                            ('name', exchange['name']), ('region', exchange['region']),
                                            ('county', exchange['county'])])
            })


if __name__ == "__main__":

    print('read premises')
    premises = read_premises()

    print('read cabinets')
    cabinets = read_cabinets()

    print('estimate pcps')
    pcps = estimate_pcps(cabinets)

    print('read exchanges')
    exchanges = read_exchanges()

    print('write premises')
    write_premises(premises)

    print('write cabinets')
    write_cabinets(cabinets)

    print('write pcps')
    write_pcps(pcps)

    print('write exchanges')
    write_exchanges(exchanges)















