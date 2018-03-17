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

#####################################
# setup file locations and data files
#####################################

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

def read_postcode_areas():
    '''
    Read postcodes shapes, 
    * Processing: Eliminate vertical postcodes, merge with best neighbour
    '''

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
                'id': neighbour['id'].replace(" ", ""),
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

def read_pcp():
    '''
    contains any postcode-to-cabinet-to-exchange information.

    Source: 1_fixed_broadband_network_hierachy_data.py
    '''
    return

def read_exchanges():
    '''
    '''
    exchanges = []

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'layer_2_exchanges', 'final_exchange_pcds.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader)
    
        for line in reader:
            exchanges.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [float(line[5]), float(line[6])]
                },
                'properties': {
                    'OLO': line[1],
                    'Name': line[2],
                    'pcd': line[0],
                    'Region': line[3],
                    'County': line[4]
                }
            })

    return exchanges

def read_exchange_pcd_lut(SYSTEM_INPUT):
    '''
    contains any postcode-to-exchange information.

    Source: 1_fixed_broadband_network_hierachy_data.py
    '''
    SYSTEM_INPUT_NETWORK = os.path.join(SYSTEM_INPUT, 'network_hierarchy_data')

    pcd_to_exchange_data = []

    with open(os.path.join(SYSTEM_INPUT_NETWORK, 'January 2013 PCP to Postcode File Part One.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(SYSTEM_INPUT_NETWORK, 'January 2013 PCP to Postcode File Part Two.csv'), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(SYSTEM_INPUT_NETWORK, 'pcp.to.pcd.dec.11.two.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(SYSTEM_INPUT_NETWORK, 'from_tomasso_valletti.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    ### find unique values in list of dicts
    return list({pcd['postcode']:pcd for pcd in pcd_to_exchange_data}.values())

def read_exchange_pcd_cabinet_lut():
    '''
    contains unique postcode-to-cabinet-to-exchange combinations.

    Source: 1_fixed_broadband_network_hierachy_data.py
    '''
    pcp_data = []

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'January 2013 PCP to Postcode File Part One.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcp_data.append({
                'exchange_id': line[0],
                'name': line[1],
                'postcode': line[2].replace(" ", ""),
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
            })

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'January 2013 PCP to Postcode File Part Two.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcp_data.append({
                'exchange_id': line[0],
                'name': line[1],
                'postcode': line[2].replace(" ", ""),
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
                ###skip other unwanted variables
            })

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'pcp.to.pcd.dec.11.one.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcp_data.append({
                'exchange_id': line[0],
                'name': line[1],
                'postcode': line[2].replace(" ", ""),
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
                ###skip other unwanted variables
            })

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'pcp.to.pcd.dec.11.two.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcp_data.append({
                'exchange_id': line[0],
                'name': line[1],
                'postcode': line[2].replace(" ", ""),
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
                ###skip other unwanted variables
            })

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

def add_exchange_id_to_postcodes(exchanges, postcode_areas, exchange_to_postcode):

    idx_exchanges = index.Index()
    lut_exchanges = {}

    # Read the exchange points
    for idx, exchange in enumerate(exchanges):

        # Add to Rtree and lookup table
        idx_exchanges.insert(idx, tuple(map(int, exchange['geometry']['coordinates'])) + tuple(map(int, exchange['geometry']['coordinates'])), exchange['properties']['OLO'])
        lut_exchanges[exchange['properties']['OLO']] = {
            'Name': exchange['properties']['Name'],
            'pcd': exchange['properties']['pcd'],
            'Region': exchange['properties']['Region'],
            'County': exchange['properties']['County'],
        }

    # Read the postcode-to-cabinet-to-exchange lookup file
    lut_pcb2cab = {}

    for idx, row in enumerate(exchange_to_postcode):
        lut_pcb2cab[row['postcode']] = row['exchange_id']

    # Connect each postcode area to an exchange
    for postcode_area in postcode_areas:

        postcode = postcode_area['properties']['POSTCODE'].replace(" ", "")

        if postcode in lut_pcb2cab:

            # Postcode-to-cabinet-to-exchange association
            postcode_area['properties']['EX_ID'] = lut_pcb2cab[postcode]
            postcode_area['properties']['EX_SRC'] = 'EXISTING POSTCODE DATA'

        else:

            # Find nearest exchange
            nearest = [n.object for n in idx_exchanges.nearest((shape(postcode_area['geometry']).bounds), 1, objects=True)]
            postcode_area['properties']['EX_ID'] = nearest[0]
            postcode_area['properties']['EX_SRC'] = 'ESTIMATED NEAREST'

        # Match the exchange ID with remaining exchange info
        if postcode_area['properties']['EX_ID'] in lut_exchanges:
            postcode_area['properties']['EX_NAME'] = lut_exchanges[postcode_area['properties']['EX_ID']]['Name']
            postcode_area['properties']['EX_PCD'] = lut_exchanges[postcode_area['properties']['EX_ID']]['pcd']
            postcode_area['properties']['EX_REGION'] = lut_exchanges[postcode_area['properties']['EX_ID']]['Region']
            postcode_area['properties']['EX_COUNTY'] = lut_exchanges[postcode_area['properties']['EX_ID']]['County']
        else:
            postcode_area['properties']['EX_NAME'] = ""
            postcode_area['properties']['EX_PCD'] = ""
            postcode_area['properties']['EX_REGION'] = ""
            postcode_area['properties']['EX_COUNTY'] = ""

    return postcode_areas

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


if __name__ == "__main__":

    SYSTEM_INPUT = os.path.join('data', 'raw')

    # Hierachy
    print('read_pcd_to_exchange_lut')
    lut_exchange_to_pcd = read_exchange_pcd_lut(SYSTEM_INPUT)

    # print('read_pcp_to_exchange_lut')
    # lut_exchange_pcd_cabinet = read_exchange_pcd_cabinet_lut(SYSTEM_INPUT)

    # # Shapes
    print('read premises')
    geojson_premises = read_premises()

    print('read postcode_areas')
    geojson_postcode_areas = read_postcode_areas()

    print('read exchanges')
    geojson_exchanges = read_exchanges()

    print('add exchange id to postcode areas')
    geojson_postcode_areas = add_exchange_id_to_postcodes(geojson_exchanges, geojson_postcode_areas, lut_exchange_to_pcd)

    # print('read cabinets')
    # cabinets = read_cabinets()

    # print('join premises with postcode areas')
    # premises = join_premises_with_postcode_areas(geojson_premises, geojson_postcode_areas)

    print('write premises')
    write_shapefile(geojson_premises, 'premises_data.shp')

    print('write postcode_areas')
    write_shapefile(geojson_postcode_areas, 'postcode_areas_data.shp')

    print('write exchanges')
    write_shapefile(geojson_exchanges, 'exchanges.shp')















