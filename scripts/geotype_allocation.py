
import os
import configparser
import csv
import fiona
import numpy as np
import sys
import glob

from shapely.geometry import shape, Point, LineString, Polygon, MultiPolygon, mapping
from shapely.ops import unary_union, cascaded_union
from pyproj import Proj, transform
from scipy.spatial import Voronoi, voronoi_plot_2d
from rtree import index

from collections import OrderedDict, defaultdict


CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# SETUP FILE LOCATIONS
#####################################

DATA_RAW_INPUTS = os.path.join(BASE_PATH, 'raw', 'a_fixed_model')
DATA_RAW_SHAPES = os.path.join(BASE_PATH, 'raw', 'd_shapes')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')

#####################################
# FUNCTIONS
#####################################

def read_exchange_area(exchange_name):
    with fiona.open(os.path.join(DATA_RAW_SHAPES, 'exchange_areas', '_exchange_areas.shp'), 'r') as source:
        return [exchange for exchange in source if exchange['properties']['id'] == exchange_name][0]

def read_lads(exchange_area):
    with fiona.open(os.path.join(DATA_RAW_SHAPES, 'lad_uk_2016-12', 'lad_uk_2016-12.shp'), 'r') as source:
        exchange_geom = shape(exchange_area['geometry'])
        return [lad for lad in source if exchange_geom.intersection(shape(lad['geometry']))]

def get_lad_area_ids(lad_areas):
    lad_area_ids = []
    for lad in lad_areas:
        lad_area_ids.append(lad['properties']['name'])
    return lad_area_ids


def read_premises_data(exchange_area):
    """
    Reads in premises points from the OS AddressBase data (.csv).

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

    """
    premises_data = []

    pathlist = glob.iglob(os.path.join(DATA_RAW_INPUTS, 'layer_5_premises', 'blds_with_functions_EO_2018_03_29') + '/*.csv', recursive=True)

    exchange_geom = shape(exchange_area['geometry'])
    exchange_bounds = shape(exchange_area['geometry']).bounds

    for path in pathlist:
        with open(os.path.join(path), 'r') as system_file:
            reader = csv.reader(system_file)
            next(reader)
            [premises_data.append({
                'uid': line[0],
                'oa': line[1],
                'gor': line[2],
                'residential_address_count': line[3],
                'non_residential_address_count': line[4],
                #'function': line[5],
                #'postgis_geom': line[6],
                'N': line[7],
                'E':line[8],
            })
                for line in reader
                if (exchange_bounds[0] <= float(line[8]) and exchange_bounds[1] <= float(line[7]) and exchange_bounds[2] >= float(line[8]) and exchange_bounds[3] >= float(line[7]))
            ]

    # remove 'None' and replace with '0'
    for idx, row in enumerate(premises_data):
        if row['residential_address_count'] == 'None':
            premises_data[idx]['residential_address_count'] = '0'
        if row['non_residential_address_count'] == 'None':
            premises_data[idx]['non_residential_address_count'] = '0'

    for row in premises_data:
        row['residential_address_count']  = int(row['residential_address_count'])

    return premises_data

def premises_to_geojson(premises, exchange_area):

    geo_prems = []
    idx = index.Index()

    exchange_geom = shape(exchange_area['geometry'])
    exchange_bounds = shape(exchange_area['geometry']).bounds

    for prem in premises:
        if (exchange_bounds[0] <= float(prem['E']) and exchange_bounds[1] <= float(prem['N']) and 
            exchange_bounds[2] >= float(prem['E']) and exchange_bounds[3] >= float(prem['N'])):
            geo_prems.append({
                            'type': "Feature",
                            'geometry': {
                                "type": "Point",
                                "coordinates": [float(prem['E']), float(prem['N'])]
                            },
                            'properties': {
                                'id': 'premise_' + prem['uid'],
                                'oa': prem['oa'],
                                'residential_address_count': int(prem['residential_address_count']),
                                'non_residential_address_count': int(prem['non_residential_address_count']),
                                #'function': line[5],
                                #'postgis_geom': line[6],
                                # 'HID': prem['HID'],
                                # 'lad': prem['lad'],
                                # 'year': prem['year'],
                                # 'wta': prem['wta'],
                                # 'wtp': prem['wtp'],
                            }
                        })
    
    geo_prems = [premise for premise in geo_prems if exchange_geom.contains(shape(premise['geometry']))]

    for prem in geo_prems:

        if prem['properties']['residential_address_count'] == 'None':
            prem['properties']['residential_address_count'] = '0'
        if prem['properties']['non_residential_address_count'] == 'None':
            prem['properties']['non_residential_address_count'] = '0'
    
    return geo_prems

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


def geotype_exchange(exchanges, premises):


    sum_of_delivery_points = 0

    for premise in premises:      
        sum_of_delivery_points += int(premise['properties']['residential_address_count'])
    
    for exchange in exchanges:

        if sum_of_delivery_points >= 20000:
            geotype = '>20k lines'
            exchange['properties']['geotype'] = geotype

        elif sum_of_delivery_points >= 10000 and sum_of_delivery_points < 20000:
            geotype = '>10k lines' 
            exchange['properties']['geotype'] = geotype            

        elif sum_of_delivery_points >= 3000 and sum_of_delivery_points <= 10000:
            geotype = '>3k lines'   
            exchange['properties']['geotype'] = geotype       

        elif sum_of_delivery_points >= 1000 and sum_of_delivery_points <= 3000:
            geotype = '>1k lines' 
            exchange['properties']['geotype'] = geotype    

        elif sum_of_delivery_points < 1000:
            geotype = '<1k lines' 
            exchange['properties']['geotype'] = geotype  

        else:
            geotype = 'no_category'
            exchange['properties']['geotype'] = geotype  
            
    for exchange in exchanges:
        
        """
        - prems_over or prems_under refers to the distance threshold around the exchange.
        - This is 2km for all exchanges over 10,000 lines
        - This is 1km for all exchanges of 3,000 or below lines 
        """

        prems_ids_over = []
        prems_ids_under = []

        prems_over = []
        prems_under = []

        if exchange['properties']['geotype'] == '>20k lines' or exchange['properties']['geotype'] == '>10k lines':
            distance = 2000
        elif exchange['properties']['geotype'] == '>3k lines' or exchange['properties']['geotype'] == '>1k lines' or exchange['properties']['geotype'] == '<1k lines':
            distance = 1000
        else:
            print('exchange not allocated a clustering distance of 2km or 1km')  

        ex_geom = shape(exchange["geometry"])
        for premise in premises:
            prem_geom = shape(premise["geometry"])
            strt_distance = round(ex_geom.distance(prem_geom), 2)
            prem_id = premise['properties']['id']
            residential_prems = int(premise['properties']['residential_address_count'])

            if strt_distance >= distance:
                prems_ids_over.append(prem_id)
                prems_over.append(residential_prems)
            elif strt_distance < distance:
                prems_ids_under.append(prem_id)
                prems_under.append(residential_prems)
            else:
                print('distance not calculated in {} for {}'.format(exchange['properties']['id'], prem_id))
                print('exchange geotype is {}'.format(exchange['properties']['geotype']))
                print('allocated threshold distance is {}'.format(distance))
                print('str_line distance is {}'.format(strt_distance))
        
        exchange['properties']['prems_over'] = sum(prems_over)
        exchange['properties']['prems_under'] = sum(prems_under)
        
        set(prems_ids_over) 
        set(prems_ids_under)

    return exchanges, geotype, prems_ids_over, prems_ids_under


def add_urban_geotype_to_exchanges(exchanges, geotype, exchange_geotype_lut):

    # Process lookup into dictionary
    exchange_geotypes = {}
    for lad in exchange_geotype_lut:
        exchange_geotypes[lad['lad']] = lad
        del exchange_geotypes[lad['lad']]['lad']

    for exchange in exchanges:
        exchange['properties']['geotype'] == geotype
    
    # Add properties
    for exchange in exchanges:
        if exchange['properties']['lad'] in exchange_geotypes:
            exchange['properties'].update({
                'geotype': exchange_geotypes[exchange['properties']['lad']]['geotype'],

            })
        else:
            pass
            # exchange['properties'].update({
            #     'geotype': 'other',
            # })
    
    return exchanges

def add_lad_to_exchanges(exchanges, lads):

    joined_exchanges = []

    # Initialze Rtree
    idx = index.Index()

    for rtree_idx, exchange in enumerate(exchanges):
        idx.insert(rtree_idx, shape(exchange['geometry']).bounds, exchange)

    # Join the two
    for lad in lads:
        for n in idx.intersection((shape(lad['geometry']).bounds), objects='raw'):
            lad_shape = shape(lad['geometry'])
            premise_shape = shape(n['geometry'])
            if lad_shape.contains(premise_shape):
                n['properties']['lad'] = lad['properties']['name']
                joined_exchanges.append(n)

    return joined_exchanges

def read_city_exchange_geotype_lut():

    exchange_geotypes = []
    with open(os.path.join(DATA_RAW_INPUTS, 'exchange_geotype_lut', 'exchange_geotype_lut.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            exchange_geotypes.append({
                'lad': line[0],
                'geotype': line[1],
            })

    return exchange_geotypes

def get_exchange_properties(exchanges):

    exchange_properties = []

    for exchange in exchanges:
        properties = exchange['properties']
        exchange_properties.append(properties)
    
    return exchange_properties

# def csv_writer(data, filename, fieldnames):
#     """
#     Write data to a CSV file path
#     """
#     # Create path
#     directory = os.path.join(DATA_INTERMEDIATE, 'geotypes')
#     if not os.path.exists(directory):
#         os.makedirs(directory)

#     name = os.path.join(directory, filename)

#     with open(name, 'a') as csv_file:
#         writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
#         writer.writerows(data)

def csv_writer(data, filename, fieldnames):

    # Create path
    directory = os.path.join(DATA_INTERMEDIATE, 'geotypes')
    if not os.path.exists(directory):
        os.makedirs(directory)

    name = os.path.join(directory, filename)

    file_exists = os.path.isfile(name)

    with open (name, 'a') as csvfile:

        writer = csv.DictWriter(csvfile, delimiter=',', lineterminator='\n',fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()  # file doesn't exist yet, write a header
        for item in data:

            writer.writerow({'id': item['id'], 'Name': item['Name'],'pcd': item['pcd'],
                            'Region': item['Region'],'County': item['County'], 'geotype': item['geotype'], 
                            'prems_over': item['prems_over'], 'prems_under': item['prems_under']})


############################################################
# RUN SCRIPT
############################################################

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

    print('read exchange area')
    exchange_area = read_exchange_area(exchange_name)
    
    print('read lads')
    geojson_lad_areas = read_lads(exchange_area)

    print('get lad ids')
    lad_ids = get_lad_area_ids(geojson_lad_areas)

    print('Reading premises data')
    premises = read_premises_data(exchange_area)

    print('converting prems to geojsons')
    geojson_layer5_premises = premises_to_geojson(premises, exchange_area)

    # Read Premises/Assets
    print('read exchanges')
    geojson_layer2_exchanges = read_exchanges(exchange_area)
    
    # Geotype exchange
    print('geotype exchanges')
    geojson_layer2_exchanges, geotype, prems_over_lut, prems_under_lut = geotype_exchange(geojson_layer2_exchanges, geojson_layer5_premises)

    print('add LAD to exchanges')
    geojson_layer2_exchanges = add_lad_to_exchanges(geojson_layer2_exchanges, geojson_lad_areas)

    print('read city exchange geotypes lut')
    city_exchange_lad_lut = read_city_exchange_geotype_lut()

    print('merge geotype info by LAD to exchanges')
    geojson_layer2_exchanges = add_urban_geotype_to_exchanges(geojson_layer2_exchanges, geotype, city_exchange_lad_lut)

    print('get exchange properties')
    exchange_properties = get_exchange_properties(geojson_layer2_exchanges)
   
    print('write link lengths to .csv')
    fieldnames = ['id','Name','pcd','Region','County', 'geotype', 'prems_over', 'prems_under']
    csv_writer(exchange_properties, 'exchange_properties.csv', fieldnames)
