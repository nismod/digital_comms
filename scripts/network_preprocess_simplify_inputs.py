import os
import sys
import configparser
import csv
import re
from collections import defaultdict
import fiona
import glob
import itertools
from shapely.geometry import shape, Polygon, MultiPolygon, mapping
from shapely.ops import unary_union
from collections import OrderedDict
from rtree import index
from tqdm import tqdm 

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW_INPUTS = os.path.join(BASE_PATH, 'raw', 'a_fixed_model')
DATA_INTERMEDIATE_INPUTS = os.path.join(BASE_PATH, 'intermediate')
DATA_RAW_SHAPES = os.path.join(BASE_PATH, 'raw', 'd_shapes')

#####################################################################################
# 1) generate unique postcode to exchange lut and export as one .csv per exchange
#####################################################################################

def get_unique_postcodes_by_exchanges(lower_units):
    """
    Function to get unique postcodes by exchange. 
    Produce a dict with the key being the grouping variable and the value being a list.  
    """

    all_data = []

    for item in lower_units:
        all_data.append(item['exchange_id'])

    all_unique_exchanges = set(all_data)

    data_by_exchange = defaultdict(list)

    for exchange in all_unique_exchanges:
        for unit in lower_units:
            if exchange == unit['exchange_id']:
                data_by_exchange[exchange].append({
                    'postcode': unit['postcode']
                    })

    return data_by_exchange

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
    
    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data', 'January 2013 PCP to Postcode File Part One.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0].replace("/", ""),
                'postcode': line[2].replace(" ", "")
            })

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','January 2013 PCP to Postcode File Part Two.csv'), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0].replace("/", ""),
                'postcode': line[2].replace(" ", "")
            })

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','pcp.to.pcd.dec.11.one.csv'), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0].replace("/", ""),
                'postcode': line[2].replace(" ", "")
            })

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','pcp.to.pcd.dec.11.two.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0].replace("/", ""),
                'postcode': line[2].replace(" ", "")
            })

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','from_tomasso_valletti.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0].replace("/", ""),
                'postcode': line[1].replace(" ", "")
            })

    ### find unique values in list of dicts
    return list({pcd['postcode']:pcd for pcd in pcd_to_exchange_data}.values())

#####################################################################################
# 2) generate unique postcode to cabinet lut and export as one .csv per exchange
#####################################################################################

def read_pcd_to_cabinet_lut():
    """
    Produces all postcode-to-cabinet-to-exchange combinations from available data, including:

        - January 2013 PCP to Postcode File Part One.csv
        - January 2013 PCP to Postcode File Part Two.csv
        - pcp.to.pcd.dec.11.one.csv'
        - pcp.to.pcd.dec.11.two.csv'

    Data Schema
    -----------
    * exchange_id: 'string'
        Unique Exchange ID
    * name: 'string'
        Unique Exchange Name
    * cabinet_id: 'string'
        Unique Cabinet ID
    * exchange_only_flag: 'int'
        Exchange only binary

    Returns
    -------
    pcp_data: Dict of dicts
    """

    pcp_data = []

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','January 2013 PCP to Postcode File Part One.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcp_data.append({
                'exchange_id': line[0].replace("/", ""),
                'name': line[1],
                'postcode': line[2],
                'cabinet': line[3],
                'exchange_only_flag': line[4]
            })

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','January 2013 PCP to Postcode File Part Two.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcp_data.append({
                'exchange_id': line[0].replace("/", ""),
                'name': line[1],
                'postcode': line[2],
                'cabinet': line[3],
                'exchange_only_flag': line[4]
            })

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','pcp.to.pcd.dec.11.one.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcp_data.append({
                'exchange_id': line[0].replace("/", ""),
                'name': line[1],
                'postcode': line[2],
                'cabinet': line[3],
                'exchange_only_flag': line[4]
            })

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','pcp.to.pcd.dec.11.two.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcp_data.append({
                'exchange_id': line[0].replace("/", ""),
                'name': line[1],
                'postcode': line[2],
                'cabinet': line[3],
                'exchange_only_flag': line[4]
            })

    return pcp_data

def get_unique_postcodes_to_cabs_by_exchange(lower_units):
    """
    Function to get unique postcodes by exchange. 
    Produce a dict with the key being the grouping variable and the value being a list.  
    """

    all_data = []

    for item in lower_units:
        all_data.append(item['exchange_id'])

    all_unique_exchanges = set(all_data)

    data_by_exchange = defaultdict(list)

    for exchange in all_unique_exchanges:
        for unit in lower_units:
            if exchange == unit['exchange_id']:
                data_by_exchange[exchange].append({
                    'postcode': unit['postcode'],
                    'cabinet': unit['cabinet'],  
                    'exchange_only_flag': unit['exchange_only_flag']                  
                    })

    return data_by_exchange

#####################################################################################
# 3) add necessary properties (postcode) to exchange polygons
#####################################################################################

def read_exchange_areas():
    """Read all exchange area shapes

    Data Schema
    -----------
    * id: 'string'
        Unique exchange id
    """    
 
    with fiona.open(os.path.join(DATA_RAW_SHAPES, 'all_exchange_areas', '_exchange_areas.shp'), 'r') as source:
        return [feature for feature in source]

def load_exchange_properties():
    """Read all exchange properties data

    Data Schema
    -----------
    * postcode: 'string'
        Unique exchange postcode
    * id: 'string'
        Unique exchange id

    """    
    exchange_postcodes_path = os.path.join(DATA_RAW_INPUTS, 'layer_2_exchanges', 'final_exchange_pcds.csv')

    output = []

    with open(exchange_postcodes_path, 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            output.append({                            
                'postcode': line[0],
                'id': 'exchange_' + line[1].replace("/", ""),
                # 'Name': line[2],
                # 'Region': line[3],
                # 'County': line[4]
            })
    
    return output

def add_properties_to_exchanges(exchanges, properties):

    """
    Takes exchange polygons, adds required data from properties.

    Data Schema
    -----------
    * postcode: 'string'
        Unique exchange postcode
    * id: 'string'
        Unique exchange id
    """

    output = []

    for exchange in exchanges:
        for exchange_property in properties:
            if exchange['properties']['id'] == exchange_property['id']:
                output.append({
                    'type': exchange['type'],
                    'geometry': exchange['geometry'],
                    'properties': {
                        'id': exchange['properties']['id'],
                        'postcode': exchange_property['postcode'],
                    }
                })

    return output

def write_shapefile(data, directory):

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
    folder_directory = os.path.join(DATA_RAW_SHAPES, directory)
    if not os.path.exists(folder_directory):
        os.makedirs(folder_directory)

    for exchange in data:
        filename = exchange['properties']['id']
        # Write all elements to output file
        with fiona.open(os.path.join(folder_directory, filename + '.shp'), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
            sink.write(exchange)

#####################################################################################
# 4) intersect postcode_areas with exchanges to get exchange_to_pcd_area_lut
#####################################################################################

def read_postcode_areas():
    with fiona.open(os.path.join(DATA_RAW_SHAPES, 'postcode_areas', '_postcode_areas.shp'), 'r') as source:
        return [area for area in source]

def intersect_pcd_areas_and_exchanges(exchanges, areas):
    
    exchange_to_pcd_area_lut = defaultdict(list)

    # Initialze Rtree
    idx = index.Index()
    [idx.insert(0, shape(exchange['geometry']).bounds, exchange) for exchange in exchanges]

    for area in areas:
        for n in idx.intersection((shape(area['geometry']).bounds), objects=True):
            area_shape = shape(area['geometry'])
            exchange_shape = shape(n.object['geometry'])
            if area_shape.contains(exchange_shape):             
                exchange_to_pcd_area_lut[n.object['properties']['exchange_id']].append({
                    'postcode_area': area['properties']['postcode_area'],
                    })

    return exchange_to_pcd_area_lut

#####################################################################################
# Write out data
#####################################################################################

def write_to_csv(data, folder, file_prefix, fieldnames):
    """
    Write data to a CSV file path
    """

    # Create path
    directory = os.path.join(DATA_INTERMEDIATE_INPUTS, folder)
    if not os.path.exists(directory):
        os.makedirs(directory)

    for key, value in data.items():

        print('finding prem data for {}'.format(key))
        filename = key

        if len(value) > 0:
            with open(os.path.join(directory, file_prefix + filename + '.csv'), 'w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
                writer.writerows(value)
        else:
            pass


def write_lut_to_csv(data, folder, file_prefix, fieldnames):
    """
    Write data to a CSV file path
    """

    # Create path
    directory = os.path.join(DATA_INTERMEDIATE_INPUTS, folder)
    if not os.path.exists(directory):
        os.makedirs(directory)

    for key, value in data.items():

        print('finding data for {}'.format(key))
        filename = key

        if len(value) > 0:
            with open(os.path.join(directory, file_prefix + filename + '.csv'), 'w') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
                writer.writerows(value)
        else:
            pass

# def write_shapefile(data, filename):

#     # Translate props to Fiona sink schema
#     prop_schema = []
#     for name, value in data[0]['properties'].items():
#         fiona_prop_type = next((fiona_type for fiona_type, python_type in fiona.FIELD_TYPES_MAP.items() if python_type == type(value)), None)
#         prop_schema.append((name, fiona_prop_type))

#     sink_driver = 'ESRI Shapefile'
#     sink_crs = {'init': 'epsg:27700'}
#     sink_schema = {
#         'geometry': data[0]['geometry']['type'],
#         'properties': OrderedDict(prop_schema)
#     }

#     #print(os.path.join(directory, shapefile_filename))
#     # Write all elements to output file
#     with fiona.open(os.path.join(DATA_RAW_SHAPES, 'postcode_areas', filename), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
#         [sink.write(feature) for feature in data]

###############################################################################

# #Run functions
# # 1) generate unique postcode to exchange lut and export as one .csv per exchange
# pcd_to_exchange_data = read_pcd_to_exchange_lut()
# pcd_to_exchange_data = get_unique_postcodes_by_exchanges(pcd_to_exchange_data)
# fieldnames = ['postcode']
# write_to_csv(pcd_to_exchange_data, 'pcd_2_exchange_luts', 'pcd_to_ex_', fieldnames)

# # 2) generate unique postcode to cabinet lut and export as one .csv per exchange
# pcd_to_cabinet_data = read_pcd_to_cabinet_lut()
# pcd_to_cabinet_data = get_unique_postcodes_to_cabs_by_exchange(pcd_to_cabinet_data)
# fieldnames = ['postcode','cabinet','exchange_only_flag']
# write_to_csv(pcd_to_cabinet_data, 'pcd_to_cabinet_by_exchange', 'pcd_to_cab_', fieldnames)

# 3) add necessary properties (postcode) to exchange polygons
exchange_areas = read_exchange_areas()
# exchange_properties = load_exchange_properties()
# exchange_areas = add_properties_to_exchanges(exchange_areas, exchange_properties)
# write_shapefile(exchange_areas, 'individual_exchange_areas')

# 4) intersect postcode_areas with exchanges to get exchange_to_pcd_area_lut
postcode_areas = read_postcode_areas()
lut = intersect_pcd_areas_and_exchanges(postcode_areas, exchange_areas)
fieldnames = ['postcode_areas']
write_to_csv(lut, 'exchange_to_pcd_area_lut', 'exchange_to_pcd_area.csv', fieldnames)







# print('reading pcd_sectors')
# postcode_sectors = read_postcode_sectors()
# print('generating pcd_areas')
# postcode_areas = generate_postcode_areas(postcode_sectors)
# print('writing shapesfiles')
# write_shapefile(postcode_areas, '_postcode_areas_v2.shp')
