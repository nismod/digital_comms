import os
import os.path
from pprint import pprint
import configparser
import csv
import fiona
import numpy as np
import random
import glob
import sys

from shapely.geometry import shape, Point, LineString, Polygon, MultiPolygon, mapping
from shapely.ops import unary_union, cascaded_union
from pyproj import Proj, transform
from rtree import index

from collections import OrderedDict, defaultdict

import osmnx as ox, networkx as nx

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# setup file locations and data files
#####################################

# DATA_RAW_DATA = os.path.join(BASE_PATH, 'raw', 'a_fixed_model')
# DATA_RAW_SHAPES = os.path.join(BASE_PATH, 'raw', 'd_shapes_cambridge_test')
DATA_RAW_DATA = os.path.join(BASE_PATH, 'raw', 'a_fixed_model')
DATA_RAW_SHAPES = os.path.join(BASE_PATH, 'raw', 'd_shapes')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')

#####################################
# READ LOOK UP TABLE (LUT) DATA
#####################################

def read_pcd_to_exchange_lut():
    """
    Produces all unique postcode-to-exchange combinations from available data, including:

    'January 2013 PCP to Postcode File Part One.csv'
    'January 2013 PCP to Postcode File Part Two.csv'
    'pcp.to.pcd.dec.11.one.csv'
    'pcp.to.pcd.dec.11.two.csv'
    'from_tomasso_valletti.csv'

    Data Schema
    ----------
    * exchange_id: 'string'
        Unique Exchange ID
    * postcode: 'string'
        Unique Postcode 

    Returns
    -------
    pcd_to_exchange_data: List of dicts
    """
    pcd_to_exchange_data = []

    with open(os.path.join(DATA_RAW_DATA, 'network_hierarchy_data', 'January 2013 PCP to Postcode File Part One.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(DATA_RAW_DATA,'network_hierarchy_data', 'January 2013 PCP to Postcode File Part One.csv'), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(DATA_RAW_DATA, 'network_hierarchy_data', 'pcp.to.pcd.dec.11.one.csv'), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(DATA_RAW_DATA, 'network_hierarchy_data', 'pcp.to.pcd.dec.11.two.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(DATA_RAW_DATA, 'network_hierarchy_data', 'from_tomasso_valletti.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    ### find unique values in list of dicts
    return list({pcd['postcode']:pcd for pcd in pcd_to_exchange_data}.values())

def read_postcode_areas():
    
    """
    Reads all postcodes shapes, removing vertical postcodes, and merging with closest neighbour.

    Data Schema
    -----------
    * POSTCODE: 'string'
        Unique Postcode

    Returns
    -------
    postcode_areas = list of dicts
    """

    postcode_areas = []

    pathlist = glob.iglob(os.path.join(DATA_RAW_SHAPES, 'codepoint', 'codepoint-poly_2429451') + '/**/*.shp', recursive=True)

    for path in pathlist:

        # Initialze Rtree
        idx = index.Index()

        print(path)
        with fiona.open(path, 'r') as source:

            # Store shapes in Rtree
            for src_shape in source:
                idx.insert(int(src_shape['id']), shape(src_shape['geometry']).bounds, src_shape)

            # Split list in regular and vertical postcodes
            postcodes = {}
            vertical_postcodes = {}

            for x in source:

                x['properties']['POSTCODE'] = x['properties']['POSTCODE'].replace(" ", "")
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

                #g = shape(pcd_area['geometry'])
                merged_geom = merged_geom.buffer(1.0)          
                merged_geom = merged_geom.simplify(0.95, preserve_topology=False)

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

def read_exchanges():

    """
    Reads in exchanges from 'final_exchange_pcds.csv'. 

    Data Schema
    ----------
    * id: 'string'
        Unique Exchange ID
    * Name: 'string'
        Unique Exchange Name
    * pcd: 'string'
        Unique Postcode
    * Region: 'string'
        Region ID
    * County: 'string'
        County IS
    
    Returns
    -------
    exchanges: List of dicts
    """

    exchanges = []

    with open(os.path.join(DATA_RAW_DATA, 'layer_2_exchanges', 'final_exchange_pcds.csv'), 'r') as system_file:
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
                    'id': 'exchange_' + line[1],
                    'Name': line[2],
                    'pcd': line[0],
                    'Region': line[3],
                    'County': line[4]
                }
            })

    return exchanges

#####################################
# PROCESS NETWORK HIERARCHY
#####################################

def add_exchange_id_to_postcode_areas(exchanges, postcode_areas, exchange_to_postcode):

    """
    Either uses known data or estimates which exchange each postcode is likely attached to.

    Arguments
    ---------

    * exchanges: 'list of dicts'
        List of Exchanges from read_exchanges()
    * postcode_areas: 'list of dicts'
        List of Postcode Areas from read_postcode_areas()
    * exchange_to_postcode: 'list of dicts'
        List of Postcode to Exchange data procudes from read_pcd_to_exchange_lut()
    
    Returns
    -------
    postcode_areas: 'list of dicts'    
    """
    idx_exchanges = index.Index()
    lut_exchanges = {}

    # Read the exchange points
    for idx, exchange in enumerate(exchanges):

        # Add to Rtree and lookup table
        idx_exchanges.insert(idx, tuple(map(int, exchange['geometry']['coordinates'])) + tuple(map(int, exchange['geometry']['coordinates'])), exchange['properties']['id'])
        lut_exchanges[exchange['properties']['id']] = {
            'Name': exchange['properties']['Name'],
            'pcd': exchange['properties']['pcd'].replace(" ", ""),
            'Region': exchange['properties']['Region'],
            'County': exchange['properties']['County'],
        }
    
    # Read the postcode-to-cabinet-to-exchange lookup file
    lut_pcb2cab = {}

    for idx, row in enumerate(exchange_to_postcode):
        lut_pcb2cab[row['postcode']] = row['exchange_id']
        
    # Connect each postcode area to an exchange
    for postcode_area in postcode_areas:

        postcode = postcode_area['properties']['POSTCODE']
        
        if postcode in lut_pcb2cab:

            # Postcode-to-cabinet-to-exchange association
            postcode_area['properties']['EX_ID'] = 'exchange_' + lut_pcb2cab[postcode]
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

def generate_exchange_area(exchanges, merge=True):
    
    exchanges_by_group = defaultdict(list)

    # Loop through all exchanges
    print('generate_exchange_area - Group polygons by exchange ID')
    for f in exchanges:

        # Convert Multipolygons to list of polygons
        if (isinstance(shape(f['geometry']), MultiPolygon)):
            polygons = [p.buffer(0) for p in shape(f['geometry'])]
        else:
            polygons = [shape(f['geometry'])]

        exchanges_by_group[f['properties']['EX_ID']].extend(polygons)

    for exchange, area in exchanges_by_group.items():
        print(exchange[0])

    # Write Multipolygons per exchange
    print('generate_exchange_area - Generate multipolygons')
    exchange_areas = []
    for exchange, area in exchanges_by_group.items():

        exchange_multipolygon = MultiPolygon(area)
        exchange_areas.append({
            'type': "Feature",
            'geometry': mapping(exchange_multipolygon),
            'properties': {
                'id': exchange
            }
        })

    if merge:
        print('generate_exchange_area - Merge multipolygons into singlepolygons')
        # Merge MultiPolygons into single Polygon
        removed_islands = []
        for area in exchange_areas:

            # Avoid intersections
            geom = shape(area['geometry']).buffer(0)
            cascaded_geom = unary_union(geom)

            # Remove islands
            # Keep polygon with largest area
            # Add removed islands to a list so that they
            # can be merged in later
            if (isinstance(cascaded_geom, MultiPolygon)):
                for idx, p in enumerate(cascaded_geom):
                    if idx == 0:
                        geom = p
                    elif p.area > geom.area:
                        removed_islands.append(geom)
                        geom = p
                    else:
                        removed_islands.append(p)
            else:
                geom = cascaded_geom

            # Write exterior to file as polygon
            exterior = Polygon(list(geom.exterior.coords))

            # Write to output
            area['geometry'] = mapping(exterior)
        
        # Add islands that were removed because they were not 
        # connected to the main polygon and were not recovered
        # because they were on the edge of the map or inbetween
        # exchanges :-). Merge to largest intersecting exchange area.
        print('generate_exchange_area - Process removed islands')
        idx_exchange_areas = index.Index()
        for idx, exchange_area in enumerate(exchange_areas):
            idx_exchange_areas.insert(idx, shape(exchange_area['geometry']).bounds, exchange_area)
        for island in removed_islands:
            intersections = [n for n in idx_exchange_areas.intersection((island.bounds), objects=True)]

            if len(intersections) > 0:
                for idx, intersection in enumerate(intersections):
                    if idx == 0:
                        merge_with = intersection
                    elif shape(intersection.object['geometry']).intersection(island).length > shape(merge_with.object['geometry']).intersection(island).length:
                        merge_with = intersection

                merged_geom = merge_with.object
                merged_geom['geometry'] = mapping(shape(merged_geom['geometry']).union(island))
                idx_exchange_areas.delete(merge_with.id, shape(merge_with.object['geometry']).bounds)
                idx_exchange_areas.insert(merge_with.id, shape(merged_geom['geometry']).bounds, merged_geom)

        exchange_areas = [n.object for n in idx_exchange_areas.intersection(idx_exchange_areas.bounds, objects=True)]

    return exchange_areas

def read_exchange_area():
    with fiona.open(os.path.join(DATA_RAW_SHAPES,'exchange_areas', '_exchange_areas.shp'), 'r') as source:
        return [exchange for exchange in source]

def write_shapefile(data, folder, path):

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

    directory = os.path.join(DATA_RAW_SHAPES, folder)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Write all elements to output file
    with fiona.open(os.path.join(directory, path), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        for feature in data:
            sink.write(feature)

def return_file_count(exchange_id):
    
    if not os.path.exists(os.path.join(DATA_INTERMEDIATE, exchange_id)):
        files = 'no files'
    else:
        files = [f for f in os.listdir(os.path.join(DATA_INTERMEDIATE, exchange_id)) if f.endswith('.shp')]

    return len(files)

####################################
#####################################

if __name__ == "__main__":

    selection = []

    SYSTEM_INPUT = os.path.join('data', 'digital_comms', 'raw')

    if not os.path.isfile(os.path.join(DATA_RAW_SHAPES,'exchange_areas','_exchange_areas.shp')):

        # Read LUTs
        print('read_pcd_to_exchange_lut')
        lut_pcd_to_exchange = read_pcd_to_exchange_lut()

        print('read postcode_areas')
        geojson_postcode_areas = read_postcode_areas()

        # Write
        print('write postcode_areas')
        write_shapefile(geojson_postcode_areas, 'postcode_areas','_postcode_areas.shp')
        
        print('read exchanges')
        geojson_layer2_exchanges = read_exchanges()
        
        # Process/Estimate network hierarchy
        print('add exchange id to postcode areas')
        geojson_postcode_areas = add_exchange_id_to_postcode_areas(geojson_layer2_exchanges, geojson_postcode_areas, lut_pcd_to_exchange)
        
        #generate exchange areas
        geojson_exchange_areas = generate_exchange_area(geojson_postcode_areas)
        
        # Write
        print('write exchange_areas')
        write_shapefile(geojson_exchange_areas, 'exchange_areas', '_exchange_areas.shp')

    
    if len(sys.argv) < 2 or sys.argv[1] == 'national':

        exchange_areas = read_exchange_area()
        selection = [(exchange['properties']['id']) for exchange in exchange_areas if return_file_count(exchange['properties']['id']) < 11] 

    elif sys.argv[1] == 'geotype_selection':
        selection = [
            'WEWPRI', # Primrose Hill (Inner London)
            'MYCHA', # Chapeltown (Major City)
            'STBNMTH', # Bournemouth (Minor City)
            'EACAM', # Cambridge (>20,000)
            'NEILB', # Ingleby Barwick(>10,000)
            'STWINCH', #Winchester (>3,000)
            'WWTORQ', #Torquay (>,1000)
            'EACOM', #Comberton (<1000)
        ]

    elif sys.argv[1] == 'sample':
        selection = [
            'exchange_LNSTF',
            'exchange_LNCNW',
            'exchange_LSPUT',
            'exchange_LVNOR',
            'exchange_LVCEN',
            'exchange_SSWES',
            'exchange_LCSSH',
            'exchange_LCPRE',
            'exchange_NDHOO',
            'exchange_MYWAK',
            'exchange_SLBCC',
            'exchange_LNBKG',
            'exchange_ESLVB',
            'exchange_LCSTA',
            'exchange_SWQJA',
            'exchange_WNOC',
            'exchange_EAWTB',
            'exchange_EMHURLE',
            'exchange_SMSC',
            'exchange_SMWHY',
            'exchange_ESDUS',
            'exchange_NSASR',
            'exchange_NSHEL',
            'exchange_ESPRM',
        ]

    elif sys.argv[1] == 'cambridge':
        selection = [
            'exchange_EAARR',
            'exchange_EABTM',
            'exchange_EABWL',
            'exchange_EACAM',
            'exchange_EACFH',
            'exchange_EACOM',
            'exchange_EACRH',
            'exchange_EACTM',
            'exchange_EAESW',
            'exchange_EAFUL',
            'exchange_EAGIR',
            'exchange_EAHIS',
            'exchange_EAHST',
            'exchange_EALNT',
            'exchange_EAMAD',
            'exchange_EAMBN',
            'exchange_EASCI',
            'exchange_EASIX',
            'exchange_EASST',
            'exchange_EASWV',
            'exchange_EATEV',
            'exchange_EATRU',
            'exchange_EAWLM',
            'exchange_EAWTB'
        ]

    elif sys.argv[1] == 'oxford':
        selection = [
            'exchange_SMSLK',
            'exchange_SMSNF',
            'exchange_SMFRD',
            'exchange_SMEY',
            'exchange_SMWC',
            'exchange_SMTAK',
            'exchange_SMCNR',
            'exchange_SMKI',
            'exchange_SMBZ',
            'exchange_SMCO',
            'exchange_SMOF',
            'exchange_SMAI',
            'exchange_SMWHY',
            'exchange_SMLW',
            'exchange_SMFH',
            'exchange_SMMCM',
            'exchange_SMSNC',
            'exchange_SMHD',
            'exchange_SMWLY',
            'exchange_SMICK',
            'exchange_SMSM',
            'exchange_SMSTJ',
            'exchange_SMBRL',
            'exchange_SMCHO',
            'exchange_SMBTN',
            'exchange_SMMSY',
            'exchange_SMBI',
            'exchange_SMWRB',
            'exchange_SMCTN',
            'exchange_SMSDM',
            'exchange_SMNHM',
            'exchange_SMGMT',
            'exchange_SMGN',
        ]

    elif sys.argv[1] == 'leeds':
        selection = [
            'exchange_MYTAD',
            'exchange_MYBOS',
            'exchange_MYDHS',
            'exchange_MYWEN',
            'exchange_MYLS',
            'exchange_MYLOF',
            'exchange_MYPON',
            'exchange_MYCHA',
            'exchange_MYSEA',
            'exchange_MYMOO',
            'exchange_MYHRW',
            'exchange_MYSPO',
            'exchange_MYOAT',
            'exchange_MYWEH',
            'exchange_MYWEH',
            'exchange_MYKKB',
            'exchange_MYSLA',
            'exchange_MYHON',
            'exchange_MYBRE',
            'exchange_MYFLO',
            'exchange_MYMIL',
            'exchange_MYHUD',
            'exchange_MYMIR',
            'exchange_MYELL',
            'exchange_MYHEC',
            'exchange_MYBRG',
            'exchange_MYSOW',
            'exchange_MYCLE',
            'exchange_MYHOB',
            'exchange_MYHAL',
            'exchange_MYBAT',
            'exchange_MYMOR',
            'exchange_MYHIP',
            'exchange_MYACO',
            'exchange_MYLOW',
            'exchange_MYILL',
            'exchange_MYTOC',
            'exchange_MYDUD',
            'exchange_MYDLT',
            'exchange_MYQUE',
            'exchange_MYRUF',
            'exchange_MYBD',
            'exchange_MYARM',
            'exchange_MYARM',
            'exchange_MYHBK',
            'exchange_MYTHT',
            'exchange_MYDEW',
            'exchange_SLADK',
            'exchange_MYSEM',
            'exchange_SLDR',
            'exchange_SLRY',
            'exchange_MYHMW',
            'exchange_SLASK',
            'exchange_MYWAK',
            'exchange_MYPUD',
            'exchange_MYSAN',
            'exchange_MYLAI',
            'exchange_MYMAN',
            'exchange_MYCUL',
            'exchange_MYNMN',
            'exchange_MYWBG',
            'exchange_MYCRF',
            'exchange_MYUND',
            'exchange_MYKNO',
            'exchange_MYHEA',
            'exchange_MYCAS',
            'exchange_MYBIN',
            'exchange_MYROT',
            'exchange_MYHSF',
            'exchange_MYSHI',
            'exchange_MYGAT',
            'exchange_MYIDL',
            'exchange_MYHLT',
            'exchange_MYRWD',
            'exchange_MYHLT',
            'exchange_MYADE',
            'exchange_MYGRF',
            'exchange_MYKEI',
            'exchange_MYSML',
            'exchange_MYGUI',
            'exchange_MYHHL',
            'exchange_MYART',
            'exchange_MYCSG',
            'exchange_MYART',
            'exchange_MYSEL',
            'exchange_MYBKA',
            'exchange_MYCAW',
            'exchange_MYSTE',
            'exchange_MYBKE',
            'exchange_MYBRW',
            'exchange_MYOTL',
            'exchange_MYTHR',
            'exchange_MYILK',
            'exchange_MYAPP',
            'exchange_MYHUB',
            'exchange_MYCOL',
            'exchange_MYADD',
        ]

    elif sys.argv[1] == 'newcastle':
        selection = [
            'exchange_NENTE',
            'exchange_NENT',
            'exchange_NEW',
            'exchange_NESS',
            'exchange_NEDB',
            'exchange_NEL',
            'exchange_NEJ',
            'exchange_NEGF',
            'exchange_NENS',
            'exchange_NEK',
            'exchange_NEB',
            'exchange_NEP',
            'exchange_NEWHP',
            'exchange_NEKI',
            'exchange_NEWB',
            'exchange_NEDUDL',
            'exchange_NESVL',
            'exchange_NEFN',
            'exchange_NESTN',
            'exchange_NEBEA',
            'exchange_NEEHN',
            'exchange_NEDP',
            'exchange_NEBR',
            'exchange_NEWAS',
            'exchange_NEHYL',
            'exchange_NESU',
            'exchange_NEBUR',
            'exchange_NERG',
            'exchange_NELF',
            'exchange_NEWK',
            'exchange_NESUN',
            'exchange_NECM',
            'exchange_NEBO',
            'exchange_NESGT',
            'exchange_NEF',
            'exchange_NEWN',
            'exchange_NED',
            'exchange_NED',
            'exchange_NEBL',
            'exchange_NEJW',
            'exchange_NERT',
            'exchange_NERT',
            'exchange_NEGHD',
            'exchange_NEWYL',
            'exchange_NEWYL',
            'exchange_NENTW',
        ]

    print(*selection, sep='\n')