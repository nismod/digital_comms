import os
from pprint import pprint
import configparser
import csv
import fiona
import numpy as np

from shapely.geometry import shape, Point, mapping
from shapely.ops import unary_union
from pyproj import Proj, transform
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from rtree import index

from collections import OrderedDict

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################
# setup file locations
#####################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'raw')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'processed')

def read_premises():

    """
    Reads in premises points from the OS AddressBase data (.csv)

    Data Schema
    ----------
    * id: :obj:`int`
        Unique Premises ID
    * oa: :obj:`str`
        ONS output area code
    * residential address count: obj:'str'
        Number of residential addresses
    * non-res address count: obj:'str'
        Number of non-residential addresses
    * postgis geom: obj:'str'
        Postgis reference
    * E: obj:'float'
        Easting coordinate
    * N: obj:'float'
        Northing coordinate

    Returns
    -------
    array: with GeoJSON dicts containing shapes and attributes
    """

    premises_data = []

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'layer_5_premises', 'cambridge_points.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            premises_data.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [float(line[5]), float(line[6])]
                },
                'properties': {
                    'id': line[0],
                    'oa': line[1],
                    'residential_address_count': line[2],
                    'non_residential_address_count': line[3],
                    'postgis_geom': line[4]
                }
            })

    # remove 'None' and replace with '0'
    for idx, premise in enumerate(premises_data):
        if premise['properties']['residential_address_count'] == 'None':
            premises_data[idx]['properties']['residential_address_count'] = '0'
        if premise['properties']['non_residential_address_count'] == 'None':
            premises_data[idx]['properties']['non_residential_address_count'] = '0'

    return premises_data


def write_premises(premises_data):
    """
    Writes premises points from premises_data to premises_points_data.shp
    """

    # write to shapefile
    sink_driver = 'ESRI Shapefile'
    sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

    setup_point_schema = {
        'geometry': 'Point',
        'properties': OrderedDict([('postcode', 'str'), ('id', 'int'), ('oa', 'str'), ('residential_address_count', 'int'),
                                    ('non_residential_address_count', 'int'), ('postgis_geom', 'str')])
    }

    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'premises_points_data.shp'), 'w', driver=sink_driver, crs=sink_crs, schema=setup_point_schema) as sink:
        for premise in premises_data:
            sink.write(premise)

def read_postcode_areas():

    postcode_areas = []

    # Initialze Rtree
    idx = index.Index()

    with fiona.open(os.path.join(SYSTEM_INPUT_FIXED, 'postcode_shapes', 'cb.shp'), 'r') as source:

        # Store shapes in Rtree
        for src_shape in source:
            idx.insert(int(src_shape['id']), shape(src_shape['geometry']).bounds, src_shape)

        # Split list in regular and vertical postcodes
        postcodes = {}
        vertical_postcodes = {}

        for x in source:

            if x['properties']['POSTCODE'].startswith('V'):
                vertical_postcodes[x['id']] = x
            else:
                postcodes[x['id']] = x

        for key, f in vertical_postcodes.items():

            vpost_geom = shape(f['geometry'])
            best_neighbour = {'id': 0, 'intersection': 0}

            # Find best neighbour
            for n in idx.intersection((vpost_geom.bounds), objects=True):
                if shape(n.object['geometry']).intersection(vpost_geom).length > best_neighbour['intersection'] and n.object['id'] != f['id']:
                    best_neighbour['id'] = n.object['id']
                    best_neighbour['intersection'] = shape(n.object['geometry']).intersection(vpost_geom).length

            # Merge with best neighbour
            neighbour = postcodes[best_neighbour['id']]
            merged_geom = unary_union([shape(neighbour['geometry']), vpost_geom])

            merged_postcode = {
                'id': neighbour['id'],
                'properties': neighbour['properties'],
                'geometry': mapping(merged_geom)
            }

            try:
                postcodes[merged_postcode['id']] = merged_postcode
            except:
                raise Exception

        for key, p in postcodes.items():
            p.pop('id')
            postcode_areas.append(p)

    return postcode_areas


def read_cabinets():

    cabinets_data = []

    with open(os.path.join(SYSTEM_INPUT_FIXED,'cambridge_shape_file_analysis', 'pcd_2_cab_2_exchange_data_cambridge.csv'), 'r') as system_file:
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

def join_premises_with_postcode_areas(premises, postcode_areas):

    joined_premises = []

    # Initialze Rtree
    idx = index.Index()

    for rtree_idx, premise in enumerate(premises):
        idx.insert(rtree_idx, shape(premise['geometry']).bounds, premise)

    # Join the two
    for postcode_area in postcode_areas:
        for n in idx.intersection((shape(postcode_area['geometry']).bounds), objects=True):
            postcode_area_shape = shape(postcode_area['geometry'])
            premise_shape = shape(n.object['geometry'])
            if postcode_area_shape.contains(premise_shape):
                n.object['properties']['postcode'] = postcode_area['properties']['POSTCODE']
                joined_premises.append(n.object)

    return joined_premises



def estimate_dist_points(premises):
    """Estimate distribution point locations.

    Parameters
    ----------
    cabinets: list of dict
        List of cabinets, each providing a dict with properties and location of the cabinet

    Returns
    -------
    dist_point: list of dict
                List of dist_points
    """
    print('start dist point estimation')

    points = np.vstack([[float(premise['northings']), float(premise['eastings'])] for premise in premises])
    number_of_clusters = int(points.shape[0] / 8)

    kmeans = KMeans(n_clusters=number_of_clusters, random_state=0, max_iter=1).fit(points)

    print('end dist point estimation')

    dist_points = []
    for idx, dist_point_location in enumerate(kmeans.cluster_centers_):
        dist_points.append({
            'id': idx,
            'northings': dist_point_location[0],
            'eastings': dist_point_location[1]
        })
    return dist_points


def write_dist_points(dist_points):
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

    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'dist_point_data.shp'), 'w', driver=sink_driver, crs=sink_crs, schema=setup_point_schema) as sink:
        for dist_point in dist_points:
            xx, yy = transform(osgb36, wgs84, float(dist_point['eastings']), float(dist_point['northings']))
            sink.write({
                #'geometry': {'type': "Point", 'coordinates': [float(dist_point['eastings']), float(dist_point['northings'])]},
                'geometry': {'type': "Point", 'coordinates': [xx, yy]},
                'properties': OrderedDict([('Name', dist_point['id'])])
            })


def read_exchanges():
    exchanges_data = []

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'layer_2_exchanges', 'final_exchange_pcds.csv'), 'r') as system_file:
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

    print('read postcode_areas')
    postcode_areas = read_postcode_areas()

    # print('read cabinets')
    # cabinets = read_cabinets()

    print('join premises with postcode areas')
    premises = join_premises_with_postcode_areas(premises, postcode_areas)

    # print('estimate dist_points')
    # dist_points = estimate_dist_points(premises)

    # print('read exchanges')
    # exchanges = read_exchanges()

    print('write premises')
    write_premises(premises)

    # print('write cabinets')
    # write_cabinets(cabinets)

    # print('write dist_points')
    # write_dist_points(dist_points)

    # print('write exchanges')
    # write_exchanges(exchanges)















