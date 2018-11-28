import time
start = time.time()
import os
import sys
from pprint import pprint
import configparser
import csv
import fiona
import numpy as np
import random
import glob

import matplotlib.pyplot as plt
from shapely.geometry import shape, Point, LineString, Polygon, MultiPolygon, mapping, MultiPoint
from shapely.ops import unary_union, cascaded_union
from pyproj import Proj, transform
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from scipy.spatial import Voronoi, voronoi_plot_2d
from rtree import index
from operator import itemgetter

from collections import OrderedDict, defaultdict

import osmnx as ox, networkx as nx, geopandas as gpd

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

# set timesteps
BASE_YEAR = 2018
END_YEAR = 2018
TIMESTEP_INCREMENT = 1
TIMESTEPS = range(BASE_YEAR, END_YEAR + 1, TIMESTEP_INCREMENT)

#####################################
# setup file locations and data files
#####################################

DATA_RAW_INPUTS = os.path.join(BASE_PATH, 'raw', 'a_fixed_model')
DATA_RAW_SHAPES = os.path.join(BASE_PATH, 'raw', 'd_shapes')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')

#####################################
# setup test data file locations
#####################################

# DATA_RAW = os.path.join(BASE_PATH, 'network_generation_test_data_cambridgeshire', 'raw')
# DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'network_generation_test_data_cambridgeshire', 'intermediate')
# DATA_RAW = os.path.join(DATA_RAW, 'network_hierarchy_data')

#####################################
# READ EXCHANGE AREA
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

#####################################
# INTEGRATE WTP AND WTA HOUSEHOLD DATA INTO PREMIses
#####################################

def read_msoa_data(lad_ids):
    """
    MSOA data contains individual level demographic characteristics including:
        - PID - Person ID
        - MSOA - Area ID
        - DC1117EW_C_SEX - Gender
        - DC1117EW_C_AGE - Age
        - DC2101EW_C_ETHPUK11 - Ethnicity
        - HID - Household ID
        - year - year
    """

    MSOA_data = []

    msoa_lad_id_files = {
        lad: os.path.join(DATA_RAW_INPUTS,'demographic_scenario_data','msoa_2018','ass_{}_MSOA11_2018.csv'.format(lad))
        for lad in lad_ids
    }

    pathlist = glob.iglob(os.path.join(DATA_RAW_INPUTS, 'demographic_scenario_data','msoa_2018') + '/*.csv', recursive=True)

    for filename in msoa_lad_id_files.values():
        with open(os.path.join(filename), 'r') as system_file:
            year_reader = csv.reader(system_file)
            next(year_reader, None)
            # Put the values in the population dict
            for line in year_reader:
                MSOA_data.append({
                    'PID': line[0],
                    'MSOA': line[1],
                    'lad': filename[-25:-16],
                    'gender': line[2],
                    'age': line[3],
                    'ethnicity': line[4],
                    'HID': line[5],
                    'year': int(filename[-8:-4]),
                })

    return MSOA_data

def read_age_data():
    """
    Contains data on fixed broadband adoption by age :
        - Age
        - % chance of adopt
    """
    my_data = []

    with open(os.path.join(DATA_RAW_INPUTS, 'willingness_to_pay', 'age.csv'), 'r') as my_file:
        reader = csv.reader(my_file)
        next(reader, None)
        for row in reader:
            my_data.append({
                'age': row[0],
                'age_wta': int(row[1])
            })

        return my_data

def read_gender_data():
    """
    Contains data on fixed broadband adoption by socio-economic status (ses):
        - ses
        - % chance of adopt
    """
    my_data = []

    with open(os.path.join(DATA_RAW_INPUTS, 'willingness_to_pay', 'gender.csv'), 'r') as my_file:
        reader = csv.reader(my_file)
        next(reader, None)
        for row in reader:
            my_data.append({
                'gender': row[0],
                'gender_wta': int(row[1])
            })

        return my_data

def read_nation_data():
    """
    Contains data on fixed broadband adoption by nation:
        - nation
        - % chance of adopt
    """
    my_data = []

    with open(os.path.join(DATA_RAW_INPUTS, 'willingness_to_pay', 'nation.csv'), 'r') as my_file:
        reader = csv.reader(my_file)
        next(reader, None)
        for row in reader:
            my_data.append({
                'nation': row[0],
                'nation_wta': int(row[1])
            })

        return my_data

def read_urban_rural_data():
    """
    Contains data on fixed broadband adoption by urban_rural:
        - urban_rural
        - % chance of adopt
    """
    my_data = []

    with open(os.path.join(DATA_RAW_INPUTS, 'willingness_to_pay', 'urban_rural.csv'), 'r') as my_file:
        reader = csv.reader(my_file)
        next(reader, None)
        for row in reader:
            my_data.append({
                'urban_rural': row[0],
                'urban_rural_wta': int(row[1])
            })

        return my_data

def add_country_indicator(data):

    for person in data:

        if person['lad'].startswith("E"):
            person['nation'] = 'england'
        if person['lad'].startswith("S"):
            person['nation'] = 'scotland'
        if person['lad'].startswith("w"):
            person['nation'] = 'wales'
        if person['lad'].startswith("N"):
            person['nation'] = 'northern ireland'

    return data

def read_ses_data():
    """
    Contains data on fixed broadband adoption by socio-economic status (ses):
        - ses
        - % chance of adopt
    """
    my_data = []

    with open(os.path.join(DATA_RAW_INPUTS, 'willingness_to_pay', 'ses.csv'), 'r') as my_file:
        reader = csv.reader(my_file)
        next(reader, None)
        for row in reader:
            my_data.append({
                'ses': row[0],
                'ses_wta': int(row[1])
            })

        return my_data

def add_data_to_MSOA_data(consumer_data, population_data, variable):
    """
    Take the WTP lookup table for all ages. Add to the population data based on age.
    """
    d1 = {d[variable]:d for d in consumer_data}

    population_data = [dict(d, **d1.get(d[variable], {})) for d in population_data]

    return population_data

def read_oa_data():
    """
    MSOA data contains individual level demographic characteristics including:
        - HID - Household ID
        - OA - Output Area ID
        - ses - Household Socio-Economic Status
        - year - year
    """

    OA_data = []

    oa_lad_id_files = {
        lad: os.path.join(DATA_RAW_INPUTS, 'demographic_scenario_data','oa_2018','ass_hh_{}_OA11_2018.csv'.format(lad))
        for lad in lad_ids
    }

    for filename in oa_lad_id_files.values():
        # Open file
        with open(filename, 'r') as year_file:
            year_reader = csv.reader(year_file)
            next(year_reader, None)
            # Put the values in the population dict
            for line in year_reader:
                OA_data.append({
                    'HID': line[0],
                    'OA': line[1],
                    'lad': filename[-23:-14],
                    'ses': line[12],
                    'year': int(filename[-8:-4]),
                })

    return OA_data

def convert_ses_grades(data):

    for household in data:
        if household['ses'] == '1':
            household['ses'] = 'AB'
        elif household['ses'] == '2':
            household['ses'] = 'AB'
        elif household['ses'] == '3':
            household['ses'] = 'C1'
        elif household['ses'] == '4':
            household['ses'] = 'C1'
        elif household['ses'] == '5':
            household['ses'] = 'C2'
        elif household['ses'] == '6':
            household['ses'] = 'DE'
        elif household['ses'] == '7':
            household['ses'] = 'DE'
        elif household['ses'] == '8':
            household['ses'] = 'DE'
        elif household['ses'] == '9':
            household['ses'] = 'students'

    return data

def merge_two_lists_of_dicts(msoa_list_of_dicts, oa_list_of_dicts, parameter1, parameter2, parameter3):
    """
    Combine the msoa and oa dicts using the household indicator and year keys.
    """
    d1 = {(d[parameter1], d[parameter2], d[parameter3]):d for d in oa_list_of_dicts}

    msoa_list_of_dicts = [dict(d, **d1.get((d[parameter1], d[parameter2], d[parameter3]), {})) for d in msoa_list_of_dicts]

    return msoa_list_of_dicts

def get_missing_ses_key(data):

    complete_data = []
    missing_ses = []

    for prem in data:
        if 'ses' in prem and 'ses_wta' in prem:
            complete_data.append({
                'PID': prem['PID'],
                'MSOA': prem['MSOA'],
                'lad': prem['lad'],
                'gender': prem['gender'],
                'age': prem['age'],
                'ethnicity': prem['ethnicity'],
                'HID': prem['HID'],
                'year': prem['year'],
                'nation': prem['nation'],
                'age_wta': prem['age_wta'],
                'gender_wta': prem['gender_wta'],
                'OA': prem['OA'],
                'ses': prem['ses'],
                'ses_wta': prem['ses_wta'],
            })
        else:
            missing_ses.append({
                'PID': prem['PID'],
                'MSOA': prem['MSOA'],
                'lad': prem['lad'],
                'gender': prem['gender'],
                'age': prem['age'],
                'ethnicity': prem['ethnicity'],
                'HID': prem['HID'],
                'year': prem['year'],
                'nation': prem['nation']
            })

    return complete_data, missing_ses

def calculate_adoption_propensity(data):

    for person in data:
        person['wta'] = person['age_wta'] * person['gender_wta'] * person['ses_wta']

    return data

def calculate_wtp(data):

    for person in data:
        person['wta'] = person['age_wta'] * person['gender_wta'] * person['ses_wta']

        if person['wta'] < 1800000:
            person['wtp'] = 20
        elif person['wta'] > 1800000 and  person['wta'] < 2200000:
            person['wtp'] = 30
        elif person['wta'] > 2200000 and  person['wta'] < 2600000:
            person['wtp'] = 40
        elif person['wta'] > 2600000 and  person['wta'] < 3000000:
            person['wtp'] = 50
        elif person['wta'] > 3000000:
            person['wtp'] = 60
    return data


def aggregate_wtp_and_wta_by_household(data):
    """
    Aggregate wtp by household by Household ID (HID), Local Authority District (lad) and year.
    """
    d = defaultdict(lambda: defaultdict(int))

    group_keys = ['HID','lad', 'year']
    sum_keys = ['wta','wtp']

    for item in data:
        for key in sum_keys:
            d[itemgetter(*group_keys)(item)][key] += item[key]

    results = [{**dict(zip(group_keys, k)), **v} for k, v in d.items()]

    return results

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
                'function': line[5],
                'postgis_geom': line[6],
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

def expand_premises(pemises_data):
    """
    Take a single address with multiple units, and expand to get a dict for each unit.
    """
    processed_pemises_data = []

    [processed_pemises_data.extend([entry]*entry['residential_address_count']) for entry in pemises_data]

    return processed_pemises_data

def merge_prems_and_housholds(premises_data, household_data):
    """
    Merges two aligned datasets, zipping row to row.
    Deals with premises_data having multiple repeated dict references due to expand function.
    """
    result = [a.copy() for a in premises_data]

    [a.update(b) for a, b in zip(result, household_data)]

    return result

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
    exchange_id =  exchange_name.replace('exchange_', '')

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data', 'January 2013 PCP to Postcode File Part One.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','January 2013 PCP to Postcode File Part Two.csv'), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','pcp.to.pcd.dec.11.one.csv'), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','pcp.to.pcd.dec.11.two.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','from_tomasso_valletti.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    ### find unique values in list of dicts
    return list({pcd['postcode']:pcd for pcd in pcd_to_exchange_data}.values())

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

    pcp_data = {}
    exchange_id =  exchange_name.replace('exchange_', '')


    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','January 2013 PCP to Postcode File Part One.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            if line[0] == exchange_id:
                pcp_data[line[2].replace(" ", "")] = {
                    'exchange_id': line[0],
                    'name': line[1],
                    'cabinet_id': line[3],
                    'exchange_only_flag': line[4]
                }

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','January 2013 PCP to Postcode File Part Two.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            if line[0] == exchange_id:
                pcp_data[line[2].replace(" ", "")] = {
                    'exchange_id': line[0],
                    'name': line[1],
                    'cabinet_id': line[3],
                    'exchange_only_flag': line[4]
                    ###skip other unwanted variables
                }

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','pcp.to.pcd.dec.11.one.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            if line[0] == exchange_id:
                pcp_data[line[2].replace(" ", "")] = {
                    'exchange_id': line[0],
                    'name': line[1],
                    'cabinet_id': line[3],
                    'exchange_only_flag': line[4]
                    ###skip other unwanted variables
                }

    with open(os.path.join(DATA_RAW_INPUTS, 'network_hierarchy_data','pcp.to.pcd.dec.11.two.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            if line[0] == exchange_id:
                pcp_data[line[2].replace(" ", "")] = {
                    'exchange_id': line[0],
                    'name': line[1],
                    'cabinet_id': line[3],
                    'exchange_only_flag': line[4]
                    ###skip other unwanted variables
                }


    return pcp_data

def read_postcode_areas(exchange_area):

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
    exchange_geom = shape(exchange_area['geometry'])

    with fiona.open(os.path.join(DATA_RAW_SHAPES, 'postcode_areas', '_postcode_areas.shp'), 'r') as source:
        return [postcode_area for postcode_area in source if exchange_geom.contains(shape(postcode_area['geometry']))]

def read_postcode_technology_lut():

    DATA_INITIAL_SYSTEM = os.path.join(DATA_RAW_INPUTS, 'offcom_initial_system', 'fixed-postcode-2017')

    postcode_technology_lut = []
    for filename in os.listdir(DATA_INITIAL_SYSTEM):
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

#####################################
# READ PREMIses/ASSETS
#####################################

def read_premises(exchange_area, exchange_abbr):

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

    Returns
    -------
    array: with GeoJSON dicts containing shapes and attributes
    """

    premises_data = []
    idx = index.Index()

    #pathlist = glob.iglob(os.path.join(DATA_INTERMEDIATE) + '/*.csv', recursive=True)

    exchange_geom = shape(exchange_area['geometry'])
    exchange_bounds = shape(exchange_area['geometry']).bounds

    #for path in pathlist:
    with open(os.path.join(DATA_INTERMEDIATE, '{}_premises_data.csv'.format(exchange_abbr)), 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader) #skip header
        for line in reader:
            if (exchange_bounds[0] <= float(line[8]) and exchange_bounds[1] <= float(line[7]) and 
                exchange_bounds[2] >= float(line[8]) and exchange_bounds[3] >= float(line[7])):
                premises_data.append({
                    'type': "Feature",
                    'geometry': {
                        "type": "Point",
                        "coordinates": [float(line[8]), float(line[7])]
                    },
                    'properties': {
                        'id': 'premise_' + line[0],
                        'oa': line[1],
                        'residential_address_count': int(line[3]),
                        'non_residential_address_count': int(line[4]),
                        'function': line[5],
                        'postgis_geom': line[6],
                        'HID': line[9],
                        'lad': line[10],
                        'year': line[11],
                        'wta': line[12],
                        'wtp': line[13],
                    }
                })

    premises_data = [premise for premise in premises_data if exchange_geom.contains(shape(premise['geometry']))]

    # remove 'None' and replace with '0'
    for idx, premise in enumerate(premises_data):
        if premise['properties']['residential_address_count'] == 'None':
            premises_data[idx]['properties']['residential_address_count'] = '0'
        if premise['properties']['non_residential_address_count'] == 'None':
            premises_data[idx]['properties']['non_residential_address_count'] = '0'

    return premises_data

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
        n
        for n in idx.intersection(shape(exchange_area['geometry']).bounds, objects='raw')
        if exchange_geom.intersection(shape(n['geometry']))
    ]

def geotype_exchange(exchanges, premises):

    for premise in premises:
        sum_of_delivery_points = 0
        sum_of_delivery_points += int(premise['properties']['residential_address_count'])

    for exchange in exchanges:

        if sum_of_delivery_points >= 20000:
            exchange['properties']['geotype'] = '>20k lines'

        elif sum_of_delivery_points >= 10000 and sum_of_delivery_points < 20000:
            exchange['properties']['geotype'] = '>10k lines'            

        elif sum_of_delivery_points >= 3000 and sum_of_delivery_points <= 10000:
            exchange['properties']['geotype'] = '>3k lines'     

        elif sum_of_delivery_points >= 1000 and sum_of_delivery_points <= 3000:
            exchange['properties']['geotype'] = '>1k lines' 

        elif sum_of_delivery_points < 1000:
            exchange['properties']['geotype'] = '<1k lines'

        else:
            exchange['properties']['geotype'] = 'no_category'          

    for exchange in exchanges:
        
        """
        - prems_over or prems_under refers to the distance threshold around the exchange.
        - This is 2km for all exchanges over 10,000 lines
        - This is 1km for all exchanges of 3,000 or below lines 
        """

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

            if strt_distance >= distance:
                prems_over.append(prem_id)
            elif strt_distance < distance:
                prems_under.append(prem_id)
            else:
                print('distance not calculated in {} for {}'.format(exchange['properties']['id'], prem_id))
                print('exchange geotype is {}'.format(exchange['properties']['geotype']))
                print('allocated threshold distance is {}'.format(distance))
                print('str_line distance is {}'.format(strt_distance))
        
        exchange['properties']['prems_over'] = len(prems_over)
        exchange['properties']['prems_under'] = len(prems_under)
        
        set(prems_over) 
        set(prems_under)

    return exchanges, prems_over, prems_under

def get_geotype(exchanges):

    for exchange in exchanges:
        geotype = exchange['properties']['geotype']
    
    return geotype

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
            nearest = list(
                idx_exchanges.nearest(
                    shape(postcode_area['geometry']).bounds, 1, objects='raw'))
            postcode_area['properties']['EX_ID'] = nearest[0]
            postcode_area['properties']['EX_SRC'] = 'ESTIMATED NEAREST'

        # Match the exchange ID with remaining exchange info
        if postcode_area['properties']['EX_ID'] in lut_exchanges:
            ex_id = postcode_area['properties']['EX_ID']
            postcode_area['properties']['EX_NAME'] = lut_exchanges[ex_id]['Name']
            postcode_area['properties']['EX_PCD'] = lut_exchanges[ex_id]['pcd']
            postcode_area['properties']['EX_REGION'] = lut_exchanges[ex_id]['Region']
            postcode_area['properties']['EX_COUNTY'] = lut_exchanges[ex_id]['County']
        else:
            postcode_area['properties']['EX_NAME'] = ""
            postcode_area['properties']['EX_PCD'] = ""
            postcode_area['properties']['EX_REGION'] = ""
            postcode_area['properties']['EX_COUNTY'] = ""

    return postcode_areas

def add_cabinet_id_to_postcode_areas(postcode_areas, pcd_to_cabinet):

    for postcode_area in postcode_areas:
        if postcode_area['properties']['POSTCODE'] in pcd_to_cabinet:
            pcd = postcode_area['properties']['POSTCODE']
            postcode_area['properties']['CAB_ID'] = pcd_to_cabinet[pcd]['cabinet_id']
        else:
            postcode_area['properties']['CAB_ID'] = ""

    return postcode_areas

def add_postcode_to_premises(premises, postcode_areas):

    joined_premises = []

    # Initialze Rtree
    idx = index.Index()
    [idx.insert(0, shape(premise['geometry']).bounds, premise) for premise in premises]

    # Join the two
    for postcode_area in postcode_areas:
        for n in idx.intersection((shape(postcode_area['geometry']).bounds), objects=True):
            postcode_area_shape = shape(postcode_area['geometry'])
            premise_shape = shape(n.object['geometry'])
            if postcode_area_shape.contains(premise_shape):
                n.object['properties']['postcode'] = postcode_area['properties']['POSTCODE']
                n.object['properties']['CAB_ID'] = postcode_area['properties']['CAB_ID']
                joined_premises.append(n.object)

    return joined_premises


def add_lad_to_matching_area(premises, lads):

    joined_premises = []

    def generator():
        for rtree_idx, premise in enumerate(premises):
            yield (rtree_idx, shape(premise['geometry']).bounds, premise)

    # Initialze Rtree
    idx = index.Index(generator())

    # Join the two
    for lad in lads:
        for n in idx.intersection((shape(lad['geometry']).bounds), objects='raw'):
            lad_shape = shape(lad['geometry'])
            premise_shape = shape(n['geometry'])
            if lad_shape.contains(premise_shape):
                n['properties']['lad'] = lad['properties']['name']
                joined_premises.append(n)

    return joined_premises

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

def add_urban_geotype_to_exchanges(exchanges, exchange_geotype_lut):

    # Process lookup into dictionary
    exchange_geotypes = {}
    for lad in exchange_geotype_lut:
        exchange_geotypes[lad['lad']] = lad
        del exchange_geotypes[lad['lad']]['lad']

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

#####################################
# PROCESS ASSETS
#####################################

def complement_postcode_cabinets(postcode_areas, premises, exchanges, exchange_abbr):

    for exchange in exchanges:

        # Count number of existing cabinets
        cabinets_in_data = [postcode_area['properties']['CAB_ID'] for postcode_area in postcode_areas]
        count_cabinets_in_data = len(set(cabinets_in_data))

        # Calculate number of expected cabinets
        if exchange['properties']['geotype'] == 'inner london': #>500k
            local_cluster_radius = 500
            minimum_samples = 500
        elif exchange['properties']['geotype'] == 'large city': #>500k
            local_cluster_radius = 500
            minimum_samples = 500
        elif exchange['properties']['geotype'] == 'small city': #>200k
            local_cluster_radius = 500
            minimum_samples = 500
        elif exchange['properties']['geotype'] == '>20k lines':
            local_cluster_radius = 600
            minimum_samples = 200
        elif exchange['properties']['geotype'] == '>10k lines':
            local_cluster_radius = 700
            minimum_samples = 100
        elif exchange['properties']['geotype'] == '>3k lines':
            local_cluster_radius = 800
            minimum_samples = 75
        elif exchange['properties']['geotype'] == '>1k lines':
            local_cluster_radius = 900
            minimum_samples = 50
        elif exchange['properties']['geotype'] == '<1k lines' or 'other':
            local_cluster_radius = 1000 # TODO: according to table these premises geotypes have no internet access
            minimum_samples = 1
        else:
            print('Geotype ' + exchange['properties']['geotype'] + ' is unknown')
            raise Exception()

        points = np.vstack([[float(i) for i in premise['geometry']['coordinates']] for premise in premises])

        db = DBSCAN(eps=local_cluster_radius, min_samples=minimum_samples).fit(points)
        core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
        core_samples_mask[db.core_sample_indices_] = True
        labels = db.labels_
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        clusters = [points[labels == i] for i in range(n_clusters_)]

        cabinets = []
        for idx, cluster in enumerate(clusters):
            cabinet_premises_geom = MultiPoint(cluster)
            cabinet_rep_point = cabinet_premises_geom.representative_point()
            cabinets.append({
                    'type': "Feature",
                    'geometry': {
                        "type": "Point",
                        "coordinates": [cabinet_rep_point.x, cabinet_rep_point.y]
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
        cabinet_by_id_lut[premise['properties']['CAB_ID']].append(shape(premise['geometry']))

    cabinets = []
    for cabinet_id in cabinet_by_id_lut:
        if cabinet_id != "":
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
    points = np.vstack([[float(i) for i in premise['geometry']['coordinates']] for premise in premises])
    number_of_clusters = int(points.shape[0] / 8)

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
# PROCESS BOUNDARIES
#####################################

def voronoi_finite_polygons_2d(vor, radius=None):

    """
    Reconstruct infinite voronoi regions in a 2D diagram to finite regions.

    Parameters
    ----------
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
            exchanges_by_group[f['properties']['EX_ID']].extend(polygons)
        except:
            exchanges_by_group[f['properties']['EX_ID']] = []
            exchanges_by_group[f['properties']['EX_ID']].extend(polygons)

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
            # Get length
            geom = LineString([origin_point['geometry']['coordinates'], lut_dest_points[origin_point['properties']['connection']]])

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
            origin_x = origin['geometry']['coordinates'][0]
            origin_y = origin['geometry']['coordinates'][1]
            dest_x = destination['geometry']['coordinates'][0]
            dest_y = destination['geometry']['coordinates'][1]

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
# GENERATE NETWORK LENGTH STATISTICS
######################################

def calc_total_link_length(exchanges, sp_cab_links, sp_dist_point_links, sp_premises_links, sl_cab_links, 
                            sl_dist_point_links, sl_premises_links, prems_over_lut, prems_under_lut):
    
        length_data = []
        
        for exchange in exchanges:
            for cab_link in sp_cab_links:
                if exchange['properties']['id'] == cab_link['properties']['dest']:
                    for dist_point_link in sp_dist_point_links:
                        if cab_link['properties']['origin'] == dist_point_link['properties']['dest']:
                            for premises_link in sp_premises_links:
                                if dist_point_link['properties']['origin'] == premises_link['properties']['dest']:
                                    if premises_link['properties']['origin'] in prems_over_lut:
                                        premises_distance = 'over'
                                    elif premises_link['properties']['origin'] in prems_under_lut:
                                        premises_distance = 'under'
                                    else:
                                        print('premise not in either distance lut')
                                        premises_distance = 'unknown'

                                    cab_link_length = round(cab_link['properties']['length'],2)
                                    dist_point_link_length = round(dist_point_link['properties']['length'],2)          
                                    premises_link_length = round(premises_link['properties']['length'],2)
                                    d_side_length = round(dist_point_link_length + premises_link_length,2)
                                    total_link_length = round(cab_link_length + d_side_length,2)
                                    
                                    length_data.append({
                                        'premises_id': premises_link['properties']['origin'],
                                        'exchange_id': exchange['properties']['id'],
                                        'geotype': exchange['properties']['geotype'],
                                        'cab_link_length': cab_link_length,
                                        'dist_point_link_length': dist_point_link_length,
                                        'premises_link_length': premises_link_length, 
                                        'd_side': d_side_length,
                                        'total_link_length': total_link_length,
                                        'length_type': 'shortest_path',
                                        'premises_distance': premises_distance
                                    })

        for exchange in exchanges:
            for cab_link in sl_cab_links:
                if exchange['properties']['id'] == cab_link['properties']['dest']:
                    for dist_point_link in sl_dist_point_links:
                        if cab_link['properties']['origin'] == dist_point_link['properties']['dest']:
                            for premises_link in sl_premises_links:
                                if dist_point_link['properties']['origin'] == premises_link['properties']['dest']:
                                    if premises_link['properties']['origin'] in prems_over_lut:
                                        premises_distance = 'over'
                                    elif premises_link['properties']['origin'] in prems_under_lut:
                                        premises_distance = 'under'
                                    else:
                                        print('premise not in either distance lut')
                                        premises_distance = 'unknown'

                                    cab_link_length = round(cab_link['properties']['length'],2)
                                    dist_point_link_length = round(dist_point_link['properties']['length'],2)          
                                    premises_link_length = round(premises_link['properties']['length'],2)
                                    d_side_length = round(dist_point_link_length + premises_link_length,2)
                                    total_link_length = round(cab_link_length + d_side_length,2)
                                    
                                    length_data.append({
                                        'premises_id': premises_link['properties']['origin'],
                                        'exchange_id': exchange['properties']['id'],
                                        'geotype': exchange['properties']['geotype'],
                                        'cab_link_length': cab_link_length,
                                        'dist_point_link_length': dist_point_link_length,
                                        'premises_link_length': premises_link_length, 
                                        'd_side': d_side_length,
                                        'total_link_length': total_link_length,
                                        'length_type': 'straight_line',
                                        'premises_distance': premises_distance
                                    })

        return length_data

def calc_geotype_statistics(exchanges, cabinets, dist_points, premises):

    for exchange in exchanges:
        
        cabs_over = 0
        cabs_under = 0

        if exchange['properties']['geotype'] == '>20k lines' or '>10k lines':
            distance = 2000
        elif exchange['properties']['geotype'] == '>3k lines' or '>1k lines' or '<1k lines':
            distance = 1000
        else:
            print('exchange not allocated a clustering distance of 2km or 1km')

        ex_geom = shape(exchange["geometry"])
        for cab in cabinets:
            if exchange['properties']['id'] == cab['properties']['connection']:
                cab_geom = shape(cab["geometry"])
                strt_distance = round(ex_geom.distance(cab_geom), 2)
                if strt_distance >= distance:
                    cabs_over +=1
                if strt_distance < distance:
                    cabs_under +=1

        exchange['properties']['cabs_over'] = cabs_over
        exchange['properties']['cabs_under'] = cabs_under

        dist_points_over = 0
        dist_points_under = 0

        for cab in cabinets:
            if exchange['properties']['id'] == cab['properties']['connection']:
                for dist_point in dist_points:
                    if cab['properties']['id'] == dist_point['properties']['connection']:
                        dist_point_geom = shape(dist_point["geometry"])
                        strt_distance = round(ex_geom.distance(dist_point_geom), 2)
                        if strt_distance >= distance:
                            dist_points_over +=1
                        if strt_distance < distance:
                            dist_points_under +=1

        exchange['properties']['dps_over'] = dist_points_over
        exchange['properties']['dps_under'] = dist_points_under

    return exchanges

def calculate_network_statistics(length_data, exchanges, exchange_name):

    urban_exchange_length_data = []
    under_exchange_length_data = []
    over_exchange_length_data = []

    for length in length_data:
        if (length['geotype'] == 'inner london' or length['geotype'] == 'large city' or length['geotype'] == 'small city'):

            if length['exchange_id'] == exchange_name and length['length_type'] == 'straight_line':
                urban_exchange_length_data.append(float(length['total_link_length']))

            urban_ave_length = (float(sum(urban_exchange_length_data)) / float(len(urban_exchange_length_data)))

        elif (length['geotype'] == '>20k lines' or length['geotype'] == '>10k lines' or length['geotype'] == '>3k lines' or
            length['geotype'] == '>1k lines' or length['geotype'] == '<1k lines'):

            if length['exchange_id'] == exchange_name and length['length_type'] == 'straight_line' and length['premises_distance'] == 'under': 
                under_exchange_length_data.append(float(length['total_link_length']))

            elif length['exchange_id'] == exchange_name and length['length_type'] == 'straight_line' and length['premises_distance'] == 'over': 
                over_exchange_length_data.append(float(length['total_link_length']))
                        
            if len(under_exchange_length_data) > 0:
                under_ave_length = (float(sum(under_exchange_length_data)) / float(len(under_exchange_length_data)))

            if len(over_exchange_length_data) > 0:
                over_ave_length = (float(sum(over_exchange_length_data)) / float(len(over_exchange_length_data)))

        else:
            print('no geotype found for link in length_data')
    
    return_network_stats = []

    for exchange in exchanges:
        """
        - 'am_' stands for Analysys Mason and refers to the network stats quoted
        in the 2008 report ‘The Costs of Deploying Fibre-Based next-Generation 
        Broadband Infrastructure’ produced for the Broadband Stakeholder Group 
        - 'ovr' = over
        - 'udr' = under
        
        """
        if exchange['properties']['geotype'] == 'inner london':
            am_average_lines_per_exchange = 16,812
            am_cabinets = 2,892
            am_average_lines_per_cabinet = 500
            am_distribution_points = 172,118
            am_ave_lines_per_dist_point = 8.4
            am_ave_line_length = 1240

        elif exchange['properties']['geotype'] == 'large city':
            am_average_lines_per_exchange = 15,512
            am_cabinets = 6,329
            am_average_lines_per_cabinet = 500
            am_distribution_points = 376,721
            am_ave_lines_per_dist_point = 8.4
            am_ave_line_length = 1780

        elif exchange['properties']['geotype'] == 'small city':
            am_average_lines_per_exchange = 15,527
            am_cabinets = 5,590
            am_average_lines_per_cabinet = 500
            am_distribution_points = 332,713
            am_ave_lines_per_dist_point = 8.4
            am_ave_line_length = 1800

        elif exchange['properties']['geotype'] == '>20k lines':
            am_udr_average_lines_per_exchange = 17089
            am_udr_cabinets = 6008
            am_udr_average_lines_per_cabinet = 475
            am_udr_distribution_points = 365,886
            am_udr_average_lines_per_dist_point = 7.8
            am_udr_average_line_length = 1500

            am_ovr_average_lines_per_exchange = 10449
            am_ovr_cabinets = 4362
            am_ovr_average_lines_per_cabinet = 400
            am_ovr_distribution_points = 223708
            am_ovr_average_lines_per_dist_point = 7.8
            am_ovr_average_line_length = 4830

        elif geotype == '>10k lines':
            
            am_udr_average_lines_per_exchange = 10728
            am_udr_cabinets = 9679
            am_udr_average_lines_per_cabinet = 450
            am_udr_distribution_points = 604925
            am_udr_average_lines_per_dist_point =7.2
            am_udr_average_line_length = 1400

            am_ovr_average_lines_per_exchange = 3826
            am_ovr_cabinets = 4142
            am_ovr_average_lines_per_cabinet = 375
            am_ovr_distribution_points = 215740
            am_ovr_average_lines_per_dist_point = 7.2
            am_ovr_average_line_length = 4000

        elif geotype == '>3k lines':

            am_udr_average_lines_per_exchange = 2751
            am_udr_cabinets = 13455
            am_udr_average_lines_per_cabinet = 205
            am_udr_distribution_points = 493569
            am_udr_average_lines_per_dist_point = 5.6
            am_udr_average_line_length = 730

            am_ovr_average_lines_per_exchange = 3181
            am_ovr_cabinets = 22227
            am_ovr_average_lines_per_cabinet = 144
            am_ovr_distribution_points = 570745
            am_ovr_average_lines_per_dist_point = 5.6
            am_ovr_average_line_length = 4830

        elif geotype == '>1k lines':

            am_udr_average_lines_per_exchange = 897
            am_udr_cabinets = 5974
            am_udr_average_lines_per_cabinet = 185
            am_udr_distribution_points = 246555
            am_udr_average_lines_per_dist_point = 4.5
            am_udr_average_line_length = 620

            am_ovr_average_lines_per_exchange = 935
            am_ovr_cabinets = 9343
            am_ovr_average_lines_per_cabinet = 123
            am_ovr_distribution_points = 257043
            am_ovr_average_lines_per_dist_point = 4.5
            am_ovr_average_line_length = 4090

        elif geotype == '<1k lines':

            am_udr_average_lines_per_exchange = 190
            am_udr_cabinets = 0
            am_udr_average_lines_per_cabinet = 0
            am_udr_distribution_points = 130706
            am_udr_average_lines_per_dist_point = 3.4
            am_udr_average_line_length = 520
            
            am_ovr_average_lines_per_exchange = 305
            am_ovr_cabinets = 0
            am_ovr_average_lines_per_cabinet = 0
            am_ovr_distribution_points = 209571
            am_ovr_average_lines_per_dist_point = 3.4
            am_ovr_average_line_length = 4260

        else:
            print('no geotype found for AM reference statistics')

        if (exchange['properties']['geotype'] == 'inner london' or 
                exchange['properties']['geotype'] == 'large city' or 
                exchange['properties']['geotype'] == 'small city'):
        
            return_network_stats.append({
                'exchange_id': exchange['properties']['id'],
                'geotype': exchange['properties']['geotype'],
                'distance_type':'urban',
                'am_ave_lines_per_ex': am_average_lines_per_exchange,
                'total_lines': exchange['properties']['prems_under'] + exchange['properties']['prems_over'], 
                'am_cabinets': am_cabinets,
                'total_cabinets': exchange['properties']['cabs_under'] + exchange['properties']['cabs_over'],
                'am_ave_lines_per_cab': am_average_lines_per_cabinet, 
                'ave_lines_per_cab': 'TODO',
                'am_distribution_points': am_distribution_points,
                'total_dps': exchange['properties']['dps_under'] + exchange['properties']['dps_over'],
                'am_ave_lines_per_dist_point': am_ave_lines_per_dist_point,
                'ave_lines_per_dist_point': 'TODO',
                'am_ave_line_length': am_ave_line_length,
                'ave_line_length': round(urban_ave_length, 2),
            })
            
        elif (length['geotype'] == '>20k lines' or length['geotype'] == '>10k lines' or 
                length['geotype'] == '>3k lines' or length['geotype'] == '>1k lines' or 
                length['geotype'] == '<1k lines'):

            return_network_stats.append({
                'exchange_id': exchange['properties']['id'],
                'geotype': exchange['properties']['geotype'],
                'distance_type':'under_threshold',
                'am_ave_lines_per_ex': am_udr_average_lines_per_exchange,
                'total_lines': exchange['properties']['prems_under'] + exchange['properties']['prems_over'], 
                'am_cabinets': am_udr_cabinets,
                'total_cabinets': exchange['properties']['cabs_under'] + exchange['properties']['cabs_over'],
                'am_ave_lines_per_cab': am_udr_average_lines_per_cabinet, 
                'ave_lines_per_cab': 'TODO',
                'am_distribution_points': am_udr_distribution_points,
                'total_dps': exchange['properties']['dps_under'] + exchange['properties']['dps_over'],
                'am_ave_lines_per_dist_point': am_udr_average_lines_per_dist_point,
                'ave_lines_per_dist_point': 'TODO',
                'am_ave_line_length': am_udr_average_line_length,
                'ave_line_length': round(under_ave_length,2),
            })
            
            return_network_stats.append({
                'exchange_id': exchange['properties']['id'],
                'geotype': exchange['properties']['geotype'],
                'distance_type':'over_threshold',
                'am_ave_lines_per_ex': am_ovr_average_lines_per_exchange,
                'total_lines': exchange['properties']['prems_under'] + exchange['properties']['prems_over'], 
                'am_cabinets': am_ovr_cabinets,
                'total_cabinets': exchange['properties']['cabs_under'] + exchange['properties']['cabs_over'],
                'am_ave_lines_per_cab': am_ovr_average_lines_per_cabinet, 
                'ave_lines_per_cab': 'TODO',
                'am_distribution_points': am_ovr_distribution_points,
                'total_dps': exchange['properties']['dps_under'] + exchange['properties']['dps_over'],
                'am_ave_lines_per_dist_point': am_ovr_average_lines_per_dist_point,
                'ave_lines_per_dist_point': 'TODO',
                'am_ave_line_length': am_ovr_average_line_length,
                'ave_line_length': round(over_ave_length,2),
            })

    return return_network_stats

#####################################
# VISUALISE NETWORK STATS
#####################################

def plot_length_data(data, exchange_name):

    e_side_sp_length = []
    d_side_sp_length = []
    dist_point_sp_length = []
    total_link_sp_length = []
    
    e_side_sl_length = []
    d_side_sl_length = []
    dist_point_sl_length = []
    total_link_sl_length = []

    for datum in data:
        if datum['length_type'] == 'shortest_path':
            e_side_sp_length.append(datum['cab_link_length'])
            d_side_sp_length.append(datum['d_side'])
            dist_point_sp_length.append(datum['premises_link_length'])
            total_link_sp_length.append(datum['total_link_length'])
        elif datum['length_type'] == 'straight_line':
            e_side_sl_length.append(datum['cab_link_length'])
            d_side_sl_length.append(datum['d_side'])
            dist_point_sl_length.append(datum['premises_link_length'])
            total_link_sl_length.append(datum['total_link_length'])

    #specify bins
    e_side_bins = np.linspace(0, 4500, 100)
    d_side_bins = np.linspace(0, 3500, 100)
    final_drop_bins = np.linspace(0, 100, 10)
    total_bins = np.linspace(0, 7000, 100)

    #setup and plot
    f, axarr = plt.subplots(2, 2)
    axarr[0, 0].hist(e_side_sp_length, e_side_bins, alpha=0.5, label='Shortest Path')
    axarr[0, 0].hist(e_side_sl_length, e_side_bins, alpha=0.5, label='Straight Line')
    axarr[0, 0].set_title('E-Side Loop Length')
    axarr[0, 1].hist(d_side_sp_length, d_side_bins, alpha=0.5, label='Shortest Path')
    axarr[0, 1].hist(d_side_sl_length, d_side_bins, alpha=0.5, label='Straight Line')
    axarr[0, 1].set_title('D-Side Loop Length')
    axarr[1, 0].hist(dist_point_sp_length, final_drop_bins, alpha=0.5, label='Shortest Path')
    axarr[1, 0].hist(dist_point_sl_length, final_drop_bins, alpha=0.5, label='Straight Line')
    axarr[1, 0].set_title('Final Drop Length')
    axarr[1, 1].hist(total_link_sp_length, total_bins, alpha=0.5, label='Shortest Path')
    axarr[1, 1].hist(total_link_sl_length, total_bins, alpha=0.5, label='Straight Line')
    axarr[1, 1].set_title('Total Loop Length')

    plt.legend(loc='upper right')
    f.subplots_adjust(hspace=0.5)

    directory = os.path.join(DATA_INTERMEDIATE, exchange_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    plt.savefig(os.path.join(DATA_INTERMEDIATE, exchange_name, 'network_stats.png'), bbox_inches='tight')

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

    with open(os.path.join(DATA_INTERMEDIATE, filename),'w') as csv_file:
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

    print('read exchange area')
    exchange_area = read_exchange_area(exchange_name)

    print('read lads')
    geojson_lad_areas = read_lads(exchange_area)

    print('get lad ids')
    lad_ids = get_lad_area_ids(geojson_lad_areas)

    ####
    # Integrate WTP and WTA household data into premises
    print('Loading MSOA data')
    MSOA_data = read_msoa_data(lad_ids)

    print('Loading age data')
    age_data = read_age_data()

    print('Loading gender data')
    gender_data = read_gender_data()

    print('Loading nation data')
    nation_data = read_nation_data()

    print('Loading urban_rural data')
    urban_rural_data = read_urban_rural_data()

    print('Add country indicator')
    MSOA_data = add_country_indicator(MSOA_data)

    print('Adding adoption data to MSOA data')
    MSOA_data = add_data_to_MSOA_data(age_data, MSOA_data, 'age')
    MSOA_data = add_data_to_MSOA_data(gender_data, MSOA_data, 'gender')

    print('Loading OA data')
    oa_data = read_oa_data()

    print('Match and convert social grades from NS-Sec to NRS')
    oa_data = convert_ses_grades(oa_data)

    print('Loading ses data')
    ses_data = read_ses_data()

    print('Adding ses adoption data to OA data')
    oa_data = add_data_to_MSOA_data(ses_data, oa_data, 'ses')

    print('Adding MSOA data to OA data')
    final_data = merge_two_lists_of_dicts(MSOA_data, oa_data, 'HID', 'lad', 'year')

    print('Catching any missing data')
    final_data, missing_data = get_missing_ses_key(final_data)

    print('Calculate product of adoption factors')
    final_data = calculate_adoption_propensity(final_data)

    print('Calculate willingness to pay')
    final_data = calculate_wtp(final_data)

    print('Aggregating WTP by household')
    household_wtp = aggregate_wtp_and_wta_by_household(final_data)

    print('Reading premises data')
    premises = read_premises_data(exchange_area)

    print('Expand premises entries')
    premises = expand_premises(premises)

    print('Adding household data to premises')
    premises = merge_prems_and_housholds(premises, household_wtp)

    print('Write premises_multiple by household to .csv')
    premises_fieldnames = ['uid','oa','gor','residential_address_count','non_residential_address_count','function','postgis_geom','N','E', 'HID','lad','year','wta','wtp']
    csv_writer(premises, '{}_premises_data.csv'.format(exchange_abbr), premises_fieldnames)

    # print('Writing wtp')
    # wta_data_fieldnames = ['HID','lad','year','wta','wtp']
    # csv_writer(household_wtp, '{}_wta_data.csv'.format(exchange_abbr), wta_data_fieldnames)

    # print('Writing any missing data')
    # missing_data_fieldnames = ['PID','MSOA','lad','gender','age','ethnicity','HID','year', 'nation']
    # csv_writer(missing_data, '{}_missing_data.csv'.format(exchange_abbr), missing_data_fieldnames)
    ####

    print('read_pcd_to_exchange_lut')
    lut_pcd_to_exchange = read_pcd_to_exchange_lut()

    print('read pcd_to_cabinet_lut')
    lut_pcd_to_cabinet = read_pcd_to_cabinet_lut()

    print('read postcode_areas')
    geojson_postcode_areas = read_postcode_areas(exchange_area)

    print('read pcd_technology_lut')
    lut_pcd_technology = read_postcode_technology_lut()

    print('read city exchange geotypes lut')
    city_exchange_lad_lut = read_city_exchange_geotype_lut()

    # Read Premises/Assets
    print('read premises')
    geojson_layer5_premises = read_premises(exchange_area, exchange_abbr)

    print('read exchanges')
    geojson_layer2_exchanges = read_exchanges(exchange_area)
    
    # Geotype exchange
    print('geotype exchanges')
    geojson_layer2_exchanges, prems_over_lut, prems_under_lut = geotype_exchange(geojson_layer2_exchanges, geojson_layer5_premises)

    print('get geotype')
    geotype = get_geotype(geojson_layer2_exchanges)

    # Process/Estimate network hierarchy
    print('add exchange id to postcode areas')
    geojson_postcode_areas = add_exchange_id_to_postcode_areas(geojson_layer2_exchanges, geojson_postcode_areas, lut_pcd_to_exchange)

    print('add cabinet id to postcode areas')
    geojson_postcode_areas = add_cabinet_id_to_postcode_areas(geojson_postcode_areas, lut_pcd_to_cabinet)

    print('add postcode to premises')
    geojson_layer5_premises = add_postcode_to_premises(geojson_layer5_premises, geojson_postcode_areas)

    print('add LAD to premises')
    geojson_layer5_premises = add_lad_to_matching_area(geojson_layer5_premises, geojson_lad_areas)

    print('add LAD to exchanges')
    geojson_layer2_exchanges = add_lad_to_exchanges(geojson_layer2_exchanges, geojson_lad_areas)

    print('merge geotype info by LAD to exchanges')
    geojson_layer2_exchanges = add_urban_geotype_to_exchanges(geojson_layer2_exchanges, city_exchange_lad_lut)
    
    # Process/Estimate assets
    print('complement cabinet locations as expected for this geotype')
    geojson_layer3_cabinets = complement_postcode_cabinets(geojson_postcode_areas, geojson_layer5_premises, geojson_layer2_exchanges, exchange_abbr)

    print('allocating cabinet to premises')
    geojson_layer5_premises = allocate_to_cabinet(geojson_layer5_premises, geojson_layer3_cabinets)

    print('allocating cabinet to pcd_areas')
    geojson_postcode_areas = allocate_to_cabinet(geojson_postcode_areas, geojson_layer3_cabinets)

    print('estimate location of distribution points')
    geojson_layer4_distributions = estimate_dist_points(geojson_layer5_premises, exchange_abbr)

    print('estimate cabinet locations')
    geojson_layer3_cabinets = estimate_cabinet_locations(geojson_layer5_premises)

    #Place assets on roads
    print('estimate cabinet locations on road network')
    geojson_layer3_cabinets = estimate_asset_locations_on_road_network(geojson_layer3_cabinets, exchange_area)

    print('estimate dist points on road network')
    geojson_layer4_distributions = estimate_asset_locations_on_road_network(geojson_layer4_distributions, exchange_area)

    # Process/Estimate boundaries
    print('generate cabinet areas')
    geojson_cabinet_areas = generate_voronoi_areas(geojson_layer3_cabinets, geojson_postcode_areas)

    print('generate distribution areas')
    geojson_distribution_areas = generate_voronoi_areas(geojson_layer4_distributions, geojson_postcode_areas)

    print('generate exchange areas')
    geojson_exchange_areas = generate_exchange_area(geojson_postcode_areas)

    # Connect assets
    print('connect premises to distributions')
    geojson_layer5_premises = connect_points_to_area(geojson_layer5_premises, geojson_distribution_areas)

    print('connect distributions to cabinets')
    geojson_layer4_distributions = connect_points_to_area(geojson_layer4_distributions, geojson_cabinet_areas)

    print('connect cabinets to exchanges')
    geojson_layer3_cabinets = connect_points_to_area(geojson_layer3_cabinets, geojson_exchange_areas)

    # Process/Estimate links
    # print('generate shortest path links layer 5')
    # geojson_layer5_premises_sp_links = generate_link_shortest_path(geojson_layer5_premises, geojson_layer4_distributions, exchange_area)

    # print('generate shortest path links layer 4')
    # geojson_layer4_distributions_sp_links = generate_link_shortest_path(geojson_layer4_distributions, geojson_layer3_cabinets, exchange_area)

    # print('generate shortest path links layer 3')
    # geojson_layer3_cabinets_sp_links = generate_link_shortest_path(geojson_layer3_cabinets, geojson_layer2_exchanges, exchange_area)

    print('generate straight line links layer 5')
    geojson_layer5_premises_sl_links = generate_link_straight_line(geojson_layer5_premises, geojson_layer4_distributions)

    print('generate straight line links layer 4')
    geojson_layer4_distributions_sl_links = generate_link_straight_line(geojson_layer4_distributions, geojson_layer3_cabinets)

    print('generate straight line links layer 3')
    geojson_layer3_cabinets_sl_links = generate_link_straight_line(geojson_layer3_cabinets, geojson_layer2_exchanges)

    # Add technology to network and process this into the network hierachy
    print('add technology to postcode areas')
    geojson_postcode_areas = add_technology_to_postcode_areas(geojson_postcode_areas, lut_pcd_technology)

    print('add technology to premises')
    geojson_layer5_premises = add_technology_to_premises(geojson_layer5_premises, geojson_postcode_areas)

    print('add technology to premises links (finaldrop)')
    geojson_layer5_premises_links = add_technology_to_link(geojson_layer5_premises, geojson_layer5_premises_sl_links)

    print('add technology to distributions')
    geojson_layer4_distributions = add_technology_to_assets(geojson_layer4_distributions, geojson_layer5_premises)

    print('add technology to distribution links')
    geojson_layer4_distributions_sp_links = add_technology_to_link(geojson_layer4_distributions, geojson_layer4_distributions_sl_links)

    print('add technology to cabinets')
    geojson_layer3_cabinets = add_technology_to_assets(geojson_layer3_cabinets, geojson_layer4_distributions)

    print('add technology to cabinet links')
    geojson_layer3_cabinets_sp_links = add_technology_to_link(geojson_layer3_cabinets, geojson_layer3_cabinets_sl_links)

    print('add technology to exchanges')
    geojson_layer2_exchanges = add_technology_to_assets(geojson_layer2_exchanges, geojson_layer3_cabinets)

    # Copy id to name (required for smif outputs)
    print('copy id to name (distributions)')
    geojson_layer4_distributions = copy_id_to_name(geojson_layer4_distributions)

    print('copy id to name (cabinets)')
    geojson_layer3_cabinets = copy_id_to_name(geojson_layer3_cabinets)

    # # Generate loop lengths
    # print('calculating loop length stats')
    # length_data = calc_total_link_length(geojson_layer2_exchanges, 
    #                                         geojson_layer3_cabinets_sp_links, geojson_layer4_distributions_sp_links, geojson_layer5_premises_sp_links,
    #                                         geojson_layer3_cabinets_sl_links, geojson_layer4_distributions_sl_links, geojson_layer5_premises_sl_links,
    #                                         prems_over_lut, prems_under_lut)

    # # Calculate geotype statistics
    # print('calculating geotype statistics')
    # exchanges = calc_geotype_statistics(geojson_layer2_exchanges, geojson_layer3_cabinets, geojson_layer4_distributions, geojson_layer5_premises)

    # # Calculate network statistics
    # print('calculating network statistics')
    # network_stats = calculate_network_statistics(length_data, exchanges, exchange_name)

    # # Plot network statistics
    # print('plotting network statistics')
    # plot_length_data(length_data, exchange_name)

    # # Write network statistics
    # print('write link lengths to .csv')
    # loop_length_fieldnames = ['premises_id','exchange_id','geotype','cab_link_length','dist_point_link_length','premises_link_length', 
    #                             'd_side', 'total_link_length', 'length_type', 'premises_distance']
    # csv_writer(length_data, '{}_link_lengths.csv'.format(exchange_abbr), loop_length_fieldnames)

    # print('write link lengths to .csv')
    # network_stats_fieldnames = ['exchange_id','geotype','distance_type','am_ave_lines_per_ex','total_lines','am_cabinets','total_cabinets',
    #                             'am_ave_lines_per_cab', 'ave_lines_per_cab', 'am_distribution_points','total_dps', 
    #                             'am_ave_lines_per_dist_point', 'ave_lines_per_dist_point', 'am_ave_line_length','ave_line_length']
    # csv_writer(network_stats, '{}_network_statistics.csv'.format(exchange_abbr), network_stats_fieldnames)

    # # Write lookups (for debug purposes)
    # print('write postcode_areas')
    # write_shapefile(geojson_postcode_areas,  exchange_name, '_postcode_areas.shp')

    # print('write distribution_areas')
    # write_shapefile(geojson_distribution_areas,  exchange_name, '_distribution_areas.shp')

    # print('write cabinet_areas')
    # write_shapefile(geojson_cabinet_areas,  exchange_name, '_cabinet_areas.shp')

    # print('write exchange_areas')
    # write_shapefile(geojson_exchange_areas,  exchange_name, '_exchange_areas.shp')

    # Write assets
    print('write premises')
    write_shapefile(geojson_layer5_premises,  exchange_name, 'assets_layer5_premises.shp')

    print('write distribution points')
    write_shapefile(geojson_layer4_distributions,  exchange_name, 'assets_layer4_distributions.shp')

    print('write cabinets')
    write_shapefile(geojson_layer3_cabinets,  exchange_name, 'assets_layer3_cabinets.shp')

    print('write exchanges')
    write_shapefile(geojson_layer2_exchanges,  exchange_name, 'assets_layer2_exchanges.shp')

    # Write links
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

    end = time.time()
    print("script finished")
    print("script took {} minutes to complete".format(round((end - start)/60, 2)))
