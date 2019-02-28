import time
import os, sys
import configparser
import csv
import fiona
import numpy as np
import glob
import random

#import matplotlib.pyplot as plt
from shapely.geometry import shape, Point, LineString, Polygon, MultiPolygon, mapping, MultiPoint
from shapely.ops import unary_union, cascaded_union
from shapely.wkt import loads
from shapely.prepared import prep
from pyproj import Proj, transform
from sklearn.cluster import KMeans #DBSCAN, 
from scipy.spatial import Voronoi, voronoi_plot_2d
from rtree import index
#from operator import itemgetter

from collections import OrderedDict, defaultdict, Counter

import osmnx as ox, networkx as nx, geopandas as gpd

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# setup file locations and data files
#####################################

DATA_RAW_INPUTS = os.path.join(BASE_PATH, 'raw', 'a_fixed_model')
DATA_RAW_SHAPES = os.path.join(BASE_PATH, 'raw', 'd_shapes')
DATA_BUILDING_DATA = os.path.join(BASE_PATH, 'raw', 'e_dem_and_buildings')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')

#####################################
# READ MAIN DATA
#####################################

def read_exchange_area(exchange_name):
    """Read exchange polygon

    Yields
    ------
    exchange_area : iterable[dict]
    """

    dirname = os.path.join(DATA_RAW_SHAPES, 'individual_exchange_areas')
    pathlist = glob.iglob(dirname + '/*.shp', recursive=True)
    filename = os.path.join(DATA_RAW_SHAPES, 'individual_exchange_areas', exchange_name + '.shp')

    for path in pathlist:
        if path == filename: 
            with fiona.open(path, 'r') as source:
                feature = next(source)
    
    return feature

def get_area_ids(exchange_name, directory, prefix):
    """Read in existing exchange to lad lookup table

    Returns
    ------
    string
        lad values as strings
    """
    output_area_ids = []

    dirname = os.path.join(DATA_INTERMEDIATE, directory)
    pathlist = glob.iglob(dirname + '/*.csv', recursive=True)
    filename = os.path.join(DATA_INTERMEDIATE, directory, prefix + exchange_name + '.csv')

    for path in pathlist:
        if path == filename: 
            with open(path, 'r') as system_file:
                reader = csv.reader(system_file)
                for line in reader:
                    output_area_ids.append(line[0])

    unique_areas = list(set(output_area_ids))

    return unique_areas

def read_premises_data(exchange_area):

    #prepare exchange_area polygon
    prepared_area = prep(shape(exchange_area['geometry']))
    PATH = os.path.join(DATA_INTERMEDIATE, 'oa_to_ex_lut', (exchange_area['properties']['id']) + '.csv')

    lad_areas = get_area_ids((exchange_area['properties']['id']), 'lut_exchange_to_lad', 'ex_to_lad_')

    lower_areas = get_area_ids((exchange_area['properties']['id']), 'oa_to_ex_lut','')

    def premises():
        i = 0
        for lad in lad_areas:
            directory = os.path.join(DATA_BUILDING_DATA, 'prems_by_lad', lad)  
            pathlist = glob.iglob(directory + '/*.csv', recursive=True)
            for path in pathlist:
                if os.path.isfile(PATH):
                    for oa in lower_areas:
                        if os.path.basename(path[:-4]) == oa:
                            with open(path, 'r') as system_file:
                                reader = csv.reader(system_file)
                                next(reader)
                                for line in reader:
                                    geom = loads(line[8])
                                    geom_point = geom.representative_point()

                                    feature = {
                                        'type': 'Feature',
                                        'geometry': mapping(geom),
                                        'representative_point': geom_point,
                                        'properties':{
                                            #'landparcel_id': line[0],
                                            #'mistral_function': line[1],
                                            'id': line[2],
                                            #'household_id': line[4],
                                            #'res_count': line[6],
                                            #'lad': line[13],
                                            #'oa': line[17],
                                        }
                                    }
                                    yield (i, geom_point.bounds, feature)
                                    i += 1

    
    idx = index.Index(premises())

    output = []

    for n in idx.intersection((shape(exchange_area['geometry']).bounds), objects=True):
        point = n.object['representative_point']
        if prepared_area.contains(point):
            #del n.object['representative_point']
            output.append(n.object)

    return output 

def read_exchanges(exchange_area):

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

    idx = index.Index()
    postcodes_path = os.path.join(DATA_RAW_INPUTS, 'layer_2_exchanges', 'final_exchange_pcds.csv')

    with open(postcodes_path, 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader)

        [
            idx.insert(
                0,
                (
                    float(line[5]),
                    float(line[6]),
                    float(line[5]),
                    float(line[6]),
                ),
                {
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
                }
            )
            for line in reader
        ]

    exchange_geom = shape(exchange_area['geometry'])

    return [
        n for n in idx.intersection(shape(exchange_area['geometry']).bounds, objects='raw')
        if exchange_geom.intersection(shape(n['geometry']))
    ]

#####################################
# READ SUPPLEMENTARY DATA
#####################################

def read_pcd_to_exchange_lut(exchange_abbr):
    """
    Loads a preprocessed list of all postcodes linked to this exchange. 

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
    
    pathlist = glob.iglob(os.path.join(DATA_INTERMEDIATE, 'lut_pcd_to_exchange') + '/*.csv', recursive=True)

    filename = exchange_abbr + '.csv'

    for path in pathlist:
        path_partition = os.path.basename(path)[10:]
        if path_partition == filename:
            with open(path, 'r', encoding='utf8', errors='replace') as system_file:
                reader = csv.reader(system_file)
                #next(reader)
                for line in reader:
                    # print(line[0])
                    pcd_to_exchange_data.extend(line)

    return pcd_to_exchange_data

def read_pcd_to_cabinet_lut(exchange_abbr):
    """
    Reads in all postcode-to-cabinet combinations from available data, including:

    Data Schema
    -----------
    * postcode: 'string'
        Unique postcode ID
    * cabinet_id: 'string'
        Unique Cabinet ID
    * exchange_only_flag: 'int'
        Exchange only binary. 1 = exchange only line, 0 = via cabinet asset. 

    Returns
    -------
    pcp_data: list of dicts
    """
    pcp_data = defaultdict(list)
    
    pathlist = glob.iglob(os.path.join(DATA_INTERMEDIATE, 'lut_pcd_to_cabinet_by_exchange') + '/*.csv', recursive=True)

    filename = exchange_abbr + '.csv'

    for path in pathlist:
        path_partition = os.path.basename(path)[11:]
        if path_partition == filename:
            with open(path, 'r', encoding='utf8', errors='replace') as system_file:
                reader = csv.reader(system_file)
                for line in reader:
                    if line[2] == '0':
                        pcp_data[line[0]].append(line[1])

    unique_ouput = defaultdict(list)

    for key, items in pcp_data.items():
        unique_values = list(set(items))
        for item in unique_values:
            unique_ouput[key].append(item)
 
    return unique_ouput

def find_intersecting_postcode_areas(exchange_abbr):

    pcd_areas = []
    
    pathlist = glob.iglob(os.path.join(DATA_INTERMEDIATE, 'lut_exchange_to_pcd_area') + '/*.csv', recursive=True)

    filename = exchange_abbr + '.csv'

    for path in pathlist:
        path_partition = path.split("_area_")[1]
        if path_partition == filename:
            with open(path, 'r', encoding='utf8', errors='replace') as system_file:
                reader = csv.reader(system_file)
                for line in reader:
                    for item in line:
                        pcd_areas.append(item)
                        # pcd_areas.append({
                        #     'postcode_area': item,
                        #     })

    return pcd_areas

def read_postcode_areas(exchange_area):

    """
    Reads all postcodes shapes which have already been processed to 
    remove vertical postcodes, merging verticals with the closest neighbour.

    Data Schema
    -----------
    * POSTCODE: 'string'
        Unique Postcode

    Returns
    -------
    postcode_areas = list of dicts
    """
    pcd_areas = []

    exchange_geom = shape(exchange_area['geometry'])

    intersecting_areas = find_intersecting_postcode_areas(exchange_area['properties']['id'])
    intersecting_areas = list(set(intersecting_areas))

    pathlist = glob.iglob(os.path.join(DATA_RAW_SHAPES, 'codepoint', 'codepoint-poly_2429451/**/*.shp'), recursive=True)

    for area in intersecting_areas:
        area = area.lower() + '.shp'
        for path in pathlist:
            if os.path.basename(path) == area:
                with fiona.open(path, 'r') as source:
                    for postcode in source:
                        if exchange_geom.contains(shape(postcode['geometry'])):
                            pcd_areas.append({
                                'type': postcode['type'],
                                'geometry': postcode['geometry'],
                                'properties': {
                                    'POSTCODE': postcode['properties']['POSTCODE'].replace(" ", "")
                                }                               
                            })

    return pcd_areas

def read_postcode_technology_lut(exchange_abbr):

    DATA_INITIAL_SYSTEM = os.path.join(DATA_RAW_INPUTS, 'ofcom_initial_system', 'fixed-postcode-2017')

    postcode_areas = find_intersecting_postcode_areas(exchange_abbr)

    postcode_technology_lut = []
    
    for area in postcode_areas:
        pcd_area = area['postcode_area']
        for filename in os.listdir(DATA_INITIAL_SYSTEM):
            path_partition = filename.split("_r02_")[1]
            path_partition = path_partition[:-4]
            if path_partition == pcd_area:
                with open(os.path.join(DATA_INITIAL_SYSTEM, filename), 'r', encoding='utf8', errors='replace') as system_file:
                    reader = csv.reader(system_file)
                    next(reader)
                    for line in reader:
                        postcode_technology_lut.append({
                            'postcode': line[0],
                            'sfbb_availability': line[3],
                            'ufbb_availability': line[4],
                            'fttp_availability': line[36],
                            'max_download_speed': line[12],
                            'max_upload_speed': line[20],
                            'average_data_download_adsl': line[33],
                            'average_data_download_sfbb': line[34],
                            'average_data_download_ufbb': line[35],
                        })

    return postcode_technology_lut

#####################################
# PROCESS NETWORK HIERARCHY
#####################################

def add_exchange_id_to_postcode_areas(exchange, postcode_areas, exchange_to_postcode):

    """
    Either uses known data or estimates which exchange each postcode is likely attached to.

    Arguments
    ---------

    * exchange: 'list of dicts'
        List containing an exchange from read_exchanges()
    * postcode_areas: 'list of geojson dicts'
        List of ostcode areas from read_postcode_areas()
    * exchange_to_postcode: 'list'
        List of postcode to exchange data procudes from read_pcd_to_exchange_lut()

    Returns
    -------
    postcode_areas: 'list of dicts'
    """

    # Connect each postcode area to an exchange
    for postcode_area in postcode_areas:

        # Postcode-to-cabinet-to-exchange association
        postcode_area['properties']['ex_id'] = exchange['properties']['id']
        postcode_area['properties']['ex_src'] = 'existing_data'
        postcode_area['properties']['ex_pcd'] = exchange['properties']['postcode']

    return postcode_areas

def add_cabinet_id_to_postcode_areas(postcode_areas, pcd_to_cabinet):

    for postcode_area in postcode_areas:
        if postcode_area['properties']['POSTCODE'] in pcd_to_cabinet:
            pcd = postcode_area['properties']['POSTCODE']
            postcode_area['properties']['CAB_ID'] = pcd_to_cabinet[pcd][0]
        else:
            postcode_area['properties']['CAB_ID'] = ""
    
    return postcode_areas

def add_postcode_to_premises(premises, postcode_areas):

    joined_premises = []

    def prems():
        i = 0        
        for prem in premises:
            geom = shape(prem['representative_point'])
            yield (i, geom.bounds, prem)
            i += 1

    # create index from generator (see http://toblerity.org/rtree/performance.html#use-stream-loading)
    idx = index.Index(prems())

    # Join the two
    for postcode_area in postcode_areas:
        for n in idx.intersection((shape(postcode_area['geometry']).bounds), objects=True):
            postcode_area_shape = shape(postcode_area['geometry'])
            premise_shape = shape(n.object['geometry'])
            if postcode_area_shape.intersects(premise_shape):
                #print('m')
                n.object['properties']['postcode'] = postcode_area['properties']['POSTCODE']
                n.object['properties']['CAB_ID'] = postcode_area['properties']['CAB_ID']
                joined_premises.append(n.object)

    return joined_premises

#####################################
# PROCESS ASSETS
#####################################

def complement_postcode_cabinets(premises, exchange, postcode_areas, exchange_abbr):

    sum_of_delivery_points = len(premises)
    print('premises count in {} is {}'.format(exchange_abbr, sum_of_delivery_points))

    # Count number of existing cabinets
    cabinets_in_data = [postcode_area['properties']['CAB_ID'] for postcode_area in postcode_areas]
    count_cabinets_in_data = len(set(cabinets_in_data))
    print('existing cabinet count is {}'.format(count_cabinets_in_data))

    # Calculate number of expected cabinets
    if exchange['properties']['geotype'] == 'large city': #>500k
        expected_cabinets = int(round(len(premises) / 500))
    elif exchange['properties']['geotype'] == 'small city': #>200k
        expected_cabinets = int(round(len(premises) / 500))
    elif exchange['properties']['geotype'] == '>20k lines':
        expected_cabinets = int(round(len(premises) / 475))
    elif exchange['properties']['geotype'] == '>10k lines':
        expected_cabinets = int(round(len(premises) / 400))
    elif exchange['properties']['geotype'] == '>3k lines':
        expected_cabinets = int(round(len(premises) / 205))
    elif exchange['properties']['geotype'] == '>1k lines':
        expected_cabinets = int(round(len(premises) / 185))
    elif exchange['properties']['geotype'] == '<1k lines' or 'other':
        expected_cabinets = int(round(len(premises) / 100)) # TODO: according to table these premises geotypes have no internet access
    else:
        print('Geotype ' + exchange['properties']['geotype'] + ' is unknown')
        raise Exception()
    
    print('expected cabinet count is {}'.format(expected_cabinets))

    # Cluster around premises
    # Remove premises that have cabinets defined
    incomplete_postcode_areas = MultiPolygon([shape(postcode_area['geometry']) for postcode_area in postcode_areas if postcode_area['properties']['CAB_ID'] == ''])
    cluster_premises = [premise for premise in premises if incomplete_postcode_areas.contains(shape(premise['geometry']))]

    # Generate cabinets
    generate_cabinets = expected_cabinets - count_cabinets_in_data

    cabinets = []

    if generate_cabinets < 1:
        generate_cabinets = 1
        print(str(generate_cabinets) + ' missing cabinets')
    else:
        print(str(generate_cabinets) + ' missing cabinets')

    point_coords = []
    for premise in cluster_premises:
        point_geom = premise['representative_point']  
        coords = list(point_geom.coords)
        point_coords.append(coords)
    points = np.vstack(point_coords)

    kmeans = KMeans(n_clusters=generate_cabinets, n_init=1, max_iter=1, n_jobs=-1, random_state=0, ).fit(points)
    
    for idx, cab_point_location in enumerate(kmeans.cluster_centers_):
        cabinets.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [cab_point_location[0], cab_point_location[1]]
                },
                'properties': {
                    "id": "{" + exchange_abbr + "}{GEN" + str(idx) + '}'
                }
            })     

    return cabinets

def allocate_to_cabinet(data, cabinets):

    cabinets_idx = index.Index()
    [cabinets_idx.insert(0, shape(cabinet['geometry']).bounds, obj=cabinet['properties']['id']) for cabinet in cabinets]

    for datum in data:
        if datum['properties']['CAB_ID'] == '':
            datum['properties']['CAB_ID'] = [n for n in cabinets_idx.nearest(shape(datum['geometry']).bounds, objects='raw')][0]

    return data

def estimate_cabinet_locations(premises):
    '''
    Put a cabinet in the representative center of the set of premises served by it
    '''
    cabinet_by_id_lut = defaultdict(list)

    for premise in premises:
        cabinet_by_id_lut[premise['properties']['CAB_ID']].append(premise['representative_point'])
    
    cabinets = []
    for cabinet_id in cabinet_by_id_lut:
        if cabinet_id != "" and cabinet_id is not None:
            cabinet_premises_geom = MultiPoint(cabinet_by_id_lut[cabinet_id])

            cabinets.append({
                'type': "Feature",
                'geometry': mapping(cabinet_premises_geom.representative_point()),
                'properties': {
                    'id': 'cabinet_' + cabinet_id
                }
            })

    return cabinets

def estimate_dist_points(premises, exchange_name, cachefile=None):
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
    dist_points = []

    # Use previous file if specified
    if cachefile != None:
        cachefile = os.path.join(DATA_INTERMEDIATE, cachefile)
        if os.path.isfile(cachefile):
            with fiona.open(cachefile, 'r') as source:
                for f in source:
                    # Make sure additional properties are not copied
                    dist_points.append({
                        'type': "Feature",
                        'geometry': f['geometry'],
                        'properties': {
                            "id": f['properties']['id']
                        }
                    })
                return dist_points

    # Generate points
    #points = np.vstack([[float(i) for i in premise['geometry']['coordinates']] for premise in premises])
    point_coords = []
    for premise in premises:
        point_geom = premise['representative_point']  # assuming this is a shapely geometry object
        coords = list(point_geom.coords)
        point_coords.append(coords)
    points = np.vstack(point_coords)

    number_of_clusters = int(points.shape[0] / 10)

    print('number of dist point clusters is {}'.format(number_of_clusters))
    
    kmeans = KMeans(n_clusters=number_of_clusters, n_init=1, max_iter=1, n_jobs=-1, random_state=0, ).fit(points)

    for idx, dist_point_location in enumerate(kmeans.cluster_centers_):
        dist_points.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [dist_point_location[0], dist_point_location[1]]
                },
                'properties': {
                    "id": "distribution_{" + exchange_name + "}{" + str(idx) + "}"
                }
            })

    return dist_points

def add_technology_to_postcode_areas(postcode_areas, technologies_lut):

    # Process lookup into dictionary
    pcd_to_technology = {}
    for technology in technologies_lut:
        pcd_to_technology[technology['postcode']] = technology
        del pcd_to_technology[technology['postcode']]['postcode']

    # Add properties
    for postcode_area in postcode_areas:
        if postcode_area['properties']['POSTCODE'] in pcd_to_technology:
            postcode_area['properties'].update({
                'max_up_spd': pcd_to_technology[postcode_area['properties']['POSTCODE']]['max_upload_speed'],
                'max_dl_spd': pcd_to_technology[postcode_area['properties']['POSTCODE']]['max_download_speed'],
                'ufbb_avail': pcd_to_technology[postcode_area['properties']['POSTCODE']]['ufbb_availability'],
                'fttp_avail': pcd_to_technology[postcode_area['properties']['POSTCODE']]['fttp_availability'],
                'sfbb_avail': pcd_to_technology[postcode_area['properties']['POSTCODE']]['sfbb_availability'],
                'av_dl_ufbb': pcd_to_technology[postcode_area['properties']['POSTCODE']]['average_data_download_ufbb'],
                'av_dl_adsl': pcd_to_technology[postcode_area['properties']['POSTCODE']]['average_data_download_adsl'],
                'av_dl_sfbb': pcd_to_technology[postcode_area['properties']['POSTCODE']]['average_data_download_sfbb']
            })
        else:
            postcode_area['properties'].update({
                'max_up_spd': 0,
                'max_dl_spd': 0,
                'ufbb_avail': 0,
                'fttp_avail': 0,
                'sfbb_avail': 0,
                'av_dl_ufbb': 0,
                'av_dl_adsl': 0,
                'av_dl_sfbb': 0
            })

    return postcode_areas

def add_technology_to_premises(premises, postcode_areas):

    premises_by_postcode = defaultdict(list)
    for premise in premises:
        premises_by_postcode[premise['properties']['postcode']].append(premise)

    # Join the two
    joined_premises = []
    for postcode_area in postcode_areas:

        # Calculate number of fiber/coax/copper connections in postcode area
        number_of_premises = len(premises_by_postcode[postcode_area['properties']['POSTCODE']]) + 1
        fttp_avail = int(postcode_area['properties']['fttp_avail'])
        ufbb_avail = int(postcode_area['properties']['ufbb_avail'])
        sfbb_avail = int(postcode_area['properties']['sfbb_avail'])
        adsl_avail = 100 - fttp_avail - ufbb_avail - sfbb_avail

        number_of_fttp= round((fttp_avail / 100) * number_of_premises)
        number_of_ufbb = round((ufbb_avail / 100) * number_of_premises)
        number_of_fttc = round((sfbb_avail / 100) * (number_of_premises * 0.8)) # Todo calculate on national scale
        number_of_docsis3 = round((sfbb_avail / 100) * (number_of_premises * 0.2))
        number_of_adsl = round((adsl_avail / 100) * number_of_premises)

        technologies =  ['FTTP'] * number_of_fttp
        technologies += ['GFast'] * number_of_ufbb
        technologies += ['FTTC'] * number_of_fttc
        technologies += ['DOCSIS3'] * number_of_docsis3
        technologies += ['ADSL'] * number_of_adsl
        random.shuffle(technologies)

        # Allocate broadband technology and final drop to premises
        for premise, technology in zip(premises_by_postcode[postcode_area['properties']['POSTCODE']], technologies):
            premise['properties']['FTTP'] = 1 if technology == 'FTTP' else 0
            premise['properties']['GFast'] = 1 if technology == 'GFast' else 0
            premise['properties']['FTTC'] = 1 if technology == 'FTTC' else 0
            premise['properties']['DOCSIS3'] = 1 if technology == 'DOCSIS3' else 0
            premise['properties']['ADSL'] = 1 if technology == 'ADSL' else 0

            joined_premises.append(premise)

    return joined_premises

def add_technology_to_premises_link(premises, premise_links):

    premises_technology_by_id = {}
    for premise in premises:
        premises_technology_by_id[premise['properties']['id']] = premise['properties']['technology']

    for premise_link in premise_links:

        technology = premises_technology_by_id[premise_link['properties']['origin']]

        if technology in ['FTTP']:
            premise_link['properties']['technology'] = 'fiber'
        elif technology in ['GFast', 'FTTC', 'ADSL']:
            premise_link['properties']['technology'] = 'copper'
        elif technology in ['DOCSIS3']:
            premise_link['properties']['technology'] = 'coax'

    return premise_links

def add_technology_to_distributions(distributions, premises):

    premises_technology_by_distribution_id = defaultdict(set)
    for premise in premises:
        premises_technology_by_distribution_id[premise['properties']['connection']].add(premise['properties']['technology'])

    for distribution in distributions:
        technologies_serving = premises_technology_by_distribution_id[distribution['properties']['id']]

        distribution['properties']['FTTP'] = 1 if 'FTTP' in technologies_serving else 0
        distribution['properties']['GFast'] = 1 if 'GFast' in technologies_serving else 0
        distribution['properties']['FTTC'] = 1 if 'FTTC' in technologies_serving else 0
        distribution['properties']['DOCSIS3'] = 1 if 'DOCSIS3' in technologies_serving else 0
        distribution['properties']['ADSL'] = 1 if 'ADSL' in technologies_serving else 0

    return distributions

def add_technology_to_link(assets, asset_links):

    assets_technology_by_id = defaultdict(set)
    for asset in assets:
        if asset['properties']['FTTP'] == 1:
            assets_technology_by_id[asset['properties']['id']].add('FTTP')
        if asset['properties']['GFast'] == 1:
            assets_technology_by_id[asset['properties']['id']].add('GFast')
        if asset['properties']['FTTC'] == 1:
            assets_technology_by_id[asset['properties']['id']].add('FTTC')
        if asset['properties']['DOCSIS3'] == 1:
            assets_technology_by_id[asset['properties']['id']].add('DOCSIS3')
        if asset['properties']['ADSL'] == 1:
            assets_technology_by_id[asset['properties']['id']].add('ADSL')

    for asset_link in asset_links:

        technology = assets_technology_by_id[asset_link['properties']['origin']]

        if 'FTTP' in technology:
            asset_link['properties']['technology'] = 'fiber'
        elif 'GFast' or 'FTTC' or 'ADSL' in technology:
            asset_link['properties']['technology'] = 'copper'
        elif 'DOCSIS3' in technology:
            asset_link['properties']['technology'] = 'coax'

    return asset_links

def add_technology_to_assets(assets, clients):

    clients_technology_by_asset_id = defaultdict(set)
    for client in clients:
        if client['properties']['FTTP'] == 1:
            clients_technology_by_asset_id[client['properties']['connection']].add('FTTP')
        if client['properties']['GFast'] == 1:
            clients_technology_by_asset_id[client['properties']['connection']].add('GFast')
        if client['properties']['FTTC'] == 1:
            clients_technology_by_asset_id[client['properties']['connection']].add('FTTC')
        if client['properties']['DOCSIS3'] == 1:
            clients_technology_by_asset_id[client['properties']['connection']].add('DOCSIS3')
        if client['properties']['ADSL'] == 1:
            clients_technology_by_asset_id[client['properties']['connection']].add('ADSL')

    for asset in assets:
        technologies_serving = clients_technology_by_asset_id[asset['properties']['id']]

        asset['properties']['FTTP'] = 1 if 'FTTP' in technologies_serving else 0
        asset['properties']['GFast'] = 1 if 'GFast' in technologies_serving else 0
        asset['properties']['FTTC'] = 1 if 'FTTC' in technologies_serving else 0
        asset['properties']['DOCSIS3'] = 1 if 'DOCSIS3' in technologies_serving else 0
        asset['properties']['ADSL'] = 1 if 'ADSL' in technologies_serving else 0

    return assets

def connect_points_to_area(points, areas):

    idx_areas = index.Index()
    for idx, area in enumerate(areas):
        idx_areas.insert(idx, shape(area['geometry']).bounds, area)

    lut_points = {}
    for dest_point in points:
        lut_points[dest_point['properties']['id']] = dest_point['geometry']['coordinates']

    linked_points = []
    for point in points:
        point_shape = shape(point['geometry'])
        possible_matches = list(idx_areas.intersection(point_shape.bounds, objects='raw'))
        match = []
        for pm in possible_matches:
            area_shape = shape(pm['geometry'])
            if area_shape.intersects(point_shape):
                match.append(pm)

        if len(match) > 0:
            point['properties']['connection'] = match[0]['properties']['id']
            linked_points.append(point)
        else:
            print(point['properties'])
            point['properties']['connection'] = linked_points[-1]['properties']['connection']
            linked_points.append(point)

    return linked_points

#####################################

#####################################

def voronoi_finite_polygons_2d(vor, radius=None):

    """
    Reconstruct infinite voronoi regions in a 2D diagram to     -
    * vor : Voronoi
        Input diagram
    * radius : float, optional
        Distance to 'points at infinity'.
    Returns
    -------
    regions : list of tuples
        Indices of vertices in each revised Voronoi regions.
    vertices : list of tuples
        Coordinates for revised Voronoi vertices. Same as coordinates
        of input vertices, with 'points at infinity' appended to the
        end.
    """

    if vor.points.shape[1] != 2:
        raise ValueError("Requires 2D input")

    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        radius = vor.points.ptp().max()

    # Construct a map containing all ridges for a given point
    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    # Reconstruct infinite regions
    for p1, region in enumerate(vor.point_region):
        vertices = vor.regions[region]

        if all(v >= 0 for v in vertices):
            # finite region
            new_regions.append(vertices)
            continue

        # reconstruct a non-finite region
        ridges = all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]

        for p2, v1, v2 in ridges:
            if v2 < 0:
                v1, v2 = v2, v1
            if v1 >= 0:
                # finite ridge: already in the region
                continue

            # Compute the missing endpoint of an infinite ridge

            t = vor.points[p2] - vor.points[p1] # tangent
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])  # normal

            midpoint = vor.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v2] + direction * radius

            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        # sort region counterclockwise
        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:,1] - c[1], vs[:,0] - c[0])
        new_region = np.array(new_region)[np.argsort(angles)]

        # finish
        new_regions.append(new_region.tolist())

    return new_regions, np.asarray(new_vertices)


def generate_voronoi_areas(asset_points, clip_region):

    # Get Points
    idx_asset_areas = index.Index()
    points = np.empty([len(list(asset_points)), 2])
    for idx, asset_point in enumerate(asset_points):

        # Prepare voronoi lookup
        points[idx] = asset_point['geometry']['coordinates']

        # Prepare Rtree lookup
        idx_asset_areas.insert(idx, shape(asset_point['geometry']).bounds, asset_point)

    # Compute Voronoi tesselation
    vor = Voronoi(points)
    regions, vertices = voronoi_finite_polygons_2d(vor)

    # Write voronoi polygons
    asset_areas = []
    for region in regions:

        polygon = vertices[region]
        geom = Polygon(polygon)

        asset_points = list(idx_asset_areas.nearest(geom.bounds, 1, objects='raw'))
        for point in asset_points:
            if geom.contains(shape(point['geometry'])):
                asset_point = point

        asset_areas.append({
            'geometry': mapping(geom),
            'properties': {
                'id': asset_point['properties']['id']
            }
        })

    return asset_areas

def generate_exchange_area(exchanges, merge=True):

    exchanges_by_group = {}

    # Loop through all exchanges
    for f in exchanges:

        # Convert Multipolygons to list of polygons
        if (isinstance(shape(f['geometry']), MultiPolygon)):
            polygons = [p.buffer(0) for p in shape(f['geometry'])]
        else:
            polygons = [shape(f['geometry'])]

        # Extend list of geometries, create key (exchange_id) if non existing
        try:
            exchanges_by_group[f['properties']['ex_id']].extend(polygons)
        except:
            exchanges_by_group[f['properties']['ex_id']] = []
            exchanges_by_group[f['properties']['ex_id']].extend(polygons)

    # Write Multipolygons per exchange
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
        # Merge MultiPolygons into single Polygon
        removed_islands = []
        for area in exchange_areas:

            # Avoid intersections
            geom = shape(area['geometry']).buffer(0)
            cascaded_geom = unary_union(geom)

            # Remove islands
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
        # exchanges. Merge to largest intersecting exchange area.
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

#####################################
# PLACE ASSETS ON ROADS
#####################################

def estimate_asset_locations_on_road_network(origins, area):
    '''
    Put a cabinet in the representative center of the set of premises served by it
    '''
    ox.config(log_file=False, log_console=False, use_cache=True)

    projUTM = Proj(init='epsg:27700')
    projWGS84 = Proj(init='epsg:4326')

    new_asset_locations = []

    try:
        east, north = transform(projUTM, projWGS84, shape(area['geometry']).bounds[2], shape(area['geometry']).bounds[3])
        west, south = transform(projUTM, projWGS84, shape(area['geometry']).bounds[0], shape(area['geometry']).bounds[1])
        G = ox.graph_from_bbox(north, south, east, west, network_type='all', truncate_by_edge=True, retain_all=True)
        for origin in origins:
            x_utm, y_utm = tuple(origin['geometry']['coordinates'])
            x_wgs, y_wgs = transform(projUTM, projWGS84, x_utm, y_utm)
            snapped_x_wgs, snapped_y_wgs = snap_point_to_graph(x_wgs, y_wgs, G)
            snapped_coords = transform(projWGS84, projUTM, snapped_x_wgs, snapped_y_wgs)
            new_asset_locations.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": snapped_coords
                },
                'properties': {
                    "id": origin['properties']['id']
                }
            })
    except (nx.exception.NetworkXPointlessConcept, ValueError):
        # got empty graph around bbox
        new_asset_locations.extend(origins)

    return new_asset_locations


def snap_point_to_graph_node(point_x, point_y, G):
    # osmnx nearest node method
    node_id = ox.get_nearest_node(G, (point_x, point_y))
    return (G.node[node_id]['x'], G.node[node_id]['y'])


def snap_point_to_graph(point_x, point_y, G):
    edge = get_nearest_edge(point_x, point_y, G)
    point = Point((point_x, point_y))
    snap = nearest_point_on_line(point, edge)
    return (snap.x, snap.y)


def get_nearest_edge(point_x, point_y, G):
    try:
        G.edge_gdf
    except AttributeError:
        G.edge_gdf = make_edge_gdf(G)
    query = (point_x, point_y, point_x, point_y)
    matches_idx = list(G.edge_gdf.sindex.nearest(query))
    for m in matches_idx:
        match = G.edge_gdf.iloc[m]
    return match.geometry


def nearest_point_on_line(point, line):
    return line.interpolate(line.project(point))


def make_edge_gdf(G):
    edges = []
    for u, v, key, data in G.edges(keys=True, data=True):
        edge_details = {'key': key}
        # if edge doesn't already have a geometry attribute, create one now
        if 'geometry' not in data:
            point_u = Point((G.nodes[u]['x'], G.nodes[u]['y']))
            point_v = Point((G.nodes[v]['x'], G.nodes[v]['y']))
            edge_details['geometry'] = LineString([point_u, point_v])
        else:
            edge_details['geometry'] = data['geometry']

        edges.append(edge_details)
    if not edges:
        raise ValueError("No edges found")
    # create a geodataframe from the list of edges and set the CRS
    gdf_edges = gpd.GeoDataFrame(edges)
    return gdf_edges

#####################################
# PROCESS LINKS
#####################################

def generate_link_straight_line(origin_points, dest_points):

    lut_dest_points = {}
    for dest_point in dest_points:
        lut_dest_points[dest_point['properties']['id']] = dest_point['geometry']['coordinates']

    links = []
    for origin_point in origin_points:

        try:
            origin_x, origin_y = return_object_coordinates(origin_point)

            # Get length
            geom = LineString([(origin_x, origin_y), lut_dest_points[origin_point['properties']['connection']]])

            links.append({
                'type': "Feature",
                'geometry': mapping(geom),
                'properties': {
                    "origin": origin_point['properties']['id'],
                    "dest": origin_point['properties']['connection'],
                    "length": geom.length
                }
            })
        except:
            print('- Problem with straight line link for:')
            print(origin_point['properties'])

    return links

def return_object_coordinates(object):

    if object['geometry']['type'] == 'Polygon':
        origin_geom = object['representative_point']
        x = origin_geom.x
        y = origin_geom.y
    elif object['geometry']['type'] == 'Point':   
        x = object['geometry']['coordinates'][0]
        y = object['geometry']['coordinates'][1]
    else:
        print('non conforming geometry type {}'.format(object['geometry']['type']))

    return x, y

def generate_link_shortest_path(origin_points, dest_points, area):
    ox.config(log_file=False, log_console=False, use_cache=True)

    projUTM = Proj(init='epsg:27700')
    projWGS84 = Proj(init='epsg:4326')

    east, north = transform(projUTM, projWGS84, shape(area['geometry']).bounds[2], shape(area['geometry']).bounds[3])
    west, south = transform(projUTM, projWGS84, shape(area['geometry']).bounds[0], shape(area['geometry']).bounds[1])
    G = ox.graph_from_bbox(north, south, east, west, network_type='all', truncate_by_edge=True)

    links = []

    for destination in dest_points:

        origins = [
            point
            for point in origin_points
            if point['properties']['connection'] == destination['properties']['id']
        ]

        for origin in origins:

            dest_x, dest_y = return_object_coordinates(destination)
            origin_x, origin_y = return_object_coordinates(origin)

            # Find shortest path between the two
            point1_x, point1_y = transform(projUTM, projWGS84, origin_x, origin_y)
            point2_x, point2_y = transform(projUTM, projWGS84, dest_x, dest_y)

            # gotcha: osmnx needs (lng, lat)
            point1 = (point1_y, point1_x)
            point2 = (point2_y, point2_x)

            # TODO improve by finding nearest edge, routing to/from node at either end
            origin_node = ox.get_nearest_node(G, point1)
            destination_node = ox.get_nearest_node(G, point2)

            try:
                if origin_node != destination_node:
                    # Find the shortest path over the network between these nodes
                    route = nx.shortest_path(G, origin_node, destination_node, weight='length')

                    # Retrieve route nodes and lookup geographical location
                    routeline = []
                    routeline.append((origin_x, origin_y))
                    for node in route:
                        routeline.append((transform(projWGS84, projUTM, G.nodes[node]['x'], G.nodes[node]['y'])))
                    routeline.append((dest_x, dest_y))
                    line = routeline
                else:
                    line = [(origin_x, origin_y), (dest_x, dest_y)]
            except nx.exception.NetworkXNoPath:
                line = [(origin_x, origin_y), (dest_x, dest_y)]

            # Map to line
            links.append({
                'type': "Feature",
                'geometry': {
                    "type": "LineString",
                    "coordinates": line
                },
                'properties': {
                    "origin": origin['properties']['id'],
                    "dest": destination['properties']['id'],
                    "length": LineString(line).length
                }
            })

    return links

def generate_link_with_nearest(origin_points, dest_points):

    idx_dest_points = index.Index()
    for idx, dest_point in enumerate(dest_points):
        idx_dest_points.insert(idx, shape(dest_point['geometry']).bounds, dest_point)

    links = []
    for origin_point in origin_points:
        nearest = list(idx_dest_points.nearest(shape(origin_point['geometry']).bounds, objects='raw'))[0]

        links.append({
            'type': "Feature",
            'geometry': {
                "type": "LineString",
                "coordinates": [origin_point['geometry']['coordinates'], nearest['geometry']['coordinates']]
            },
            'properties': {
                "origin": origin_point['properties']['id'],
                "dest": nearest['properties']['id'],
                "length": round(LineString([origin_point['geometry']['coordinates'], nearest['geometry']['coordinates']]).length,2)
            }
        })
    return links

def copy_id_to_name(data):

    for entry in data:
        entry['properties']['name'] = entry['properties']['id']
    return data

#####################################
# WRITE LUTS/ASSETS/LINKS
#####################################

def write_shapefile(data, exchange_name, filename):

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

    # Create path
    directory = os.path.join(DATA_INTERMEDIATE, exchange_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    print(os.path.join(directory, filename))
    # Write all elements to output file
    with fiona.open(os.path.join(directory, filename), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        [sink.write(feature) for feature in data]

def csv_writer(data, filename, fieldnames):
    """
    Write data to a CSV file path
    """
    # Create path
    directory = os.path.join(DATA_INTERMEDIATE)
    if not os.path.exists(directory):
        os.makedirs(directory)

    name = os.path.join(DATA_INTERMEDIATE, filename)

    with open(name, 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)


#####################################
# APPLY METHODS
#####################################

if __name__ == "__main__":

    SYSTEM_INPUT = os.path.join('data', 'raw')

    if len(sys.argv) != 2:
        print("Error: no exchange or abbreviation provided")
        print("Usage: {} <exchange>".format(os.path.basename(__file__)))
        exit(-1)

    # Read LUTs
    print('Process ' + sys.argv[1])
    exchange_name = sys.argv[1]
    exchange_abbr = sys.argv[1].replace('exchange_', '')

    #####################################################################################################
    ### IMPORT MAIN DATA
    print('Read exchange area') 
    exchange_area = read_exchange_area(exchange_name)

    print('Reading premises data') 
    geojson_layer5_premises = read_premises_data(exchange_area)

    print('Read exchanges') 
    geojson_layer2_exchange = read_exchanges(exchange_area)

    print('Read postcode_areas') 
    geojson_postcode_areas = read_postcode_areas(exchange_area)

    #####################################################################################################
    ### IMPORT SUPPLEMETARY DATA AND PROCESS
    print('Read pcd_to_exchange_lut') 
    lut_pcd_to_exchange = read_pcd_to_exchange_lut(exchange_abbr)

    print('Read pcd_to_cabinet_lut') 
    lut_pcd_to_cabinet = read_pcd_to_cabinet_lut(exchange_abbr)

    print('Read pcd_technology_lut') 
    lut_pcd_technology = read_postcode_technology_lut(exchange_abbr)

    #####################################################################################################
    # Process/Estimate network hierarchy
    print('Add exchange id to postcode areas')
    geojson_postcode_areas = add_exchange_id_to_postcode_areas(exchange_area, geojson_postcode_areas, lut_pcd_to_exchange)

    print('Add cabinet id to postcode areas')
    geojson_postcode_areas = add_cabinet_id_to_postcode_areas(geojson_postcode_areas, lut_pcd_to_cabinet)

    print('Add postcode to premises')
    geojson_layer5_premises = add_postcode_to_premises(geojson_layer5_premises, geojson_postcode_areas)

    #####################################################################################################
    ### Process/Estimate assets
    print('complement cabinet locations as expected for this geotype')
    geojson_layer3_cabinets = complement_postcode_cabinets(geojson_layer5_premises, exchange_area, geojson_postcode_areas, exchange_abbr)

    print('allocating cabinet to premises')
    geojson_layer5_premises = allocate_to_cabinet(geojson_layer5_premises, geojson_layer3_cabinets)
  
    print('allocating cabinet to pcd_areas')
    geojson_postcode_areas = allocate_to_cabinet(geojson_postcode_areas, geojson_layer3_cabinets)

    print('estimate cabinet locations')
    geojson_layer3_cabinets = estimate_cabinet_locations(geojson_layer5_premises)

    print('estimate cabinet locations on road network')
    geojson_layer3_cabinets = estimate_asset_locations_on_road_network(geojson_layer3_cabinets, exchange_area)

    print('estimate location of distribution points')
    geojson_layer4_distributions = estimate_dist_points(geojson_layer5_premises, exchange_abbr)

    print('estimate dist points on road network')
    geojson_layer4_distributions = estimate_asset_locations_on_road_network(geojson_layer4_distributions, exchange_area)

    # Process/Estimate boundaries
    print('generate cabinet areas')
    geojson_cabinet_areas = generate_voronoi_areas(geojson_layer3_cabinets, geojson_postcode_areas)

    print('generate distribution areas')
    geojson_distribution_areas = generate_voronoi_areas(geojson_layer4_distributions, geojson_postcode_areas)

    print('generate exchange areas')
    geojson_exchange_areas = generate_exchange_area(geojson_postcode_areas)

    ##########################################################################################################
    # Connect assets
    print('connect premises to distributions')
    geojson_layer5_premises = connect_points_to_area(geojson_layer5_premises, geojson_distribution_areas)

    print('connect distributions to cabinets')
    geojson_layer4_distributions = connect_points_to_area(geojson_layer4_distributions, geojson_cabinet_areas)

    print('connect cabinets to exchanges')
    geojson_layer3_cabinets = connect_points_to_area(geojson_layer3_cabinets, geojson_exchange_areas)

    # ##########################################################################################################
    # ## Process/Estimate links
    # print('generate shortest path links layer 5')
    # geojson_layer5_premises_sp_links = generate_link_shortest_path(geojson_layer5_premises, geojson_layer4_distributions, exchange_area)

    # print('generate shortest path links layer 4')
    # geojson_layer4_distributions_sp_links = generate_link_shortest_path(geojson_layer4_distributions, geojson_layer3_cabinets, exchange_area)

    # print('generate shortest path links layer 3')
    # geojson_layer3_cabinets_sp_links = generate_link_shortest_path(geojson_layer3_cabinets, geojson_layer2_exchange, exchange_area)

    print('generate straight line links layer 5')
    geojson_layer5_premises_sl_links = generate_link_straight_line(geojson_layer5_premises, geojson_layer4_distributions)

    print('generate straight line links layer 4')
    geojson_layer4_distributions_sl_links = generate_link_straight_line(geojson_layer4_distributions, geojson_layer3_cabinets)

    print('generate straight line links layer 3')
    geojson_layer3_cabinets_sl_links = generate_link_straight_line(geojson_layer3_cabinets, geojson_layer2_exchange)

    ##########################################################################################################
    # Add technology to network and process this into the network hierachy
    print('add technology to postcode areas')
    geojson_postcode_areas = add_technology_to_postcode_areas(geojson_postcode_areas, lut_pcd_technology)

    print('add technology to premises')
    geojson_layer5_premises = add_technology_to_premises(geojson_layer5_premises, geojson_postcode_areas)

    print('add technology to distributions')
    geojson_layer4_distributions = add_technology_to_assets(geojson_layer4_distributions, geojson_layer5_premises)

    print('add technology to cabinets')
    geojson_layer3_cabinets = add_technology_to_assets(geojson_layer3_cabinets, geojson_layer4_distributions)

    print('add technology to exchanges')
    geojson_layer2_exchange = add_technology_to_assets(geojson_layer2_exchange, geojson_layer3_cabinets)

    print('add technology to premises links (finaldrop)')
    geojson_layer5_premises_links = add_technology_to_link(geojson_layer5_premises, geojson_layer5_premises_sl_links)

    print('add technology to distribution links')
    geojson_layer4_distributions_sl_links = add_technology_to_link(geojson_layer4_distributions, geojson_layer4_distributions_sl_links)

    print('add technology to cabinet links')
    geojson_layer3_cabinets_sl_links = add_technology_to_link(geojson_layer3_cabinets, geojson_layer3_cabinets_sl_links)

    # Copy id to name (required for smif outputs)
    print('copy id to name (distributions)')
    geojson_layer4_distributions = copy_id_to_name(geojson_layer4_distributions)

    print('copy id to name (cabinets)')
    geojson_layer3_cabinets = copy_id_to_name(geojson_layer3_cabinets)

    ###########################################################################################################
    # # # # Write network statistics
    # # # print('write link lengths to .csv')
    # # # loop_length_fieldnames = ['premises_id','exchange_id','geotype','cab_link_length','dist_point_link_length','premises_link_length', 
    # # #                             'd_side', 'total_link_length', 'length_type', 'premises_distance']
    # # # csv_writer(length_data, '{}_link_lengths.csv'.format(exchange_abbr), loop_length_fieldnames)

    # # # print('write link lengths to .csv')
    # # # network_stats_fieldnames = ['exchange_id','geotype','distance_type','am_ave_lines_per_ex','total_lines','am_cabinets','total_cabinets',
    # # #                             'am_ave_lines_per_cab', 'ave_lines_per_cab', 'am_distribution_points','total_dps', 
    # # #                             'am_ave_lines_per_dist_point', 'ave_lines_per_dist_point', 'am_ave_line_length','ave_line_length']
    # # # csv_writer(network_stats, '{}_network_statistics.csv'.format(exchange_abbr), network_stats_fieldnames)

    # Write lookups (for debug purposes)
    print('write postcode_areas')
    write_shapefile(geojson_postcode_areas,  exchange_name, '_postcode_areas.shp')

    print('write distribution_areas')
    write_shapefile(geojson_distribution_areas,  exchange_name, '_distribution_areas.shp')

    print('write cabinet_areas')
    write_shapefile(geojson_cabinet_areas,  exchange_name, '_cabinet_areas.shp')

    print('write exchange_area')
    write_exchange_area =[]
    write_exchange_area.append(exchange_area)
    write_shapefile(write_exchange_area,  exchange_name, '_exchange_area.shp')

    # Write assets
    print('write premises')
    write_shapefile(geojson_layer5_premises,  exchange_name, 'assets_layer5_premises.shp')

    print('write distribution points')
    write_shapefile(geojson_layer4_distributions,  exchange_name, 'assets_layer4_distributions.shp')

    print('write cabinets')
    write_shapefile(geojson_layer3_cabinets,  exchange_name, 'assets_layer3_cabinets.shp')

    print('write exchanges')
    write_shapefile(geojson_layer2_exchange,  exchange_name, 'assets_layer2_exchange.shp')

    # # Write links
    # print('write links layer5')
    # write_shapefile(geojson_layer5_premises_sp_links,  exchange_name, 'links_sp_layer5_premises.shp')

    # print('write links layer4')
    # write_shapefile(geojson_layer4_distributions_sp_links,  exchange_name, 'links_sp_layer4_distributions.shp')

    # print('write links layer3')
    # write_shapefile(geojson_layer3_cabinets_sp_links,  exchange_name, 'links_sp_layer3_cabinets.shp')

    print('write links layer5')
    write_shapefile(geojson_layer5_premises_sl_links,  exchange_name, 'links_sl_layer5_premises.shp')

    print('write links layer4')
    write_shapefile(geojson_layer4_distributions_sl_links,  exchange_name, 'links_sl_layer4_distributions.shp')

    print('write links layer3')
    write_shapefile(geojson_layer3_cabinets_sl_links,  exchange_name, 'links_sl_layer3_cabinets.shp')

    print("script finished")
    #print("script took {} minutes to complete".format(round((end - start)/60, 2)))

