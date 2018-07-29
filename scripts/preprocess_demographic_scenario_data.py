import configparser
import csv
import os
import statistics
from itertools import groupby
from operator import itemgetter
from copy import deepcopy
import pprint

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

BASE_YEAR = 2018
END_YEAR = 2018
TIMESTEP_INCREMENT = 1
TIMESTEPS = range(BASE_YEAR, END_YEAR + 1, TIMESTEP_INCREMENT)

#####################################
# SETUP FILE LOCATIONS 
#####################################

DEMOGRAPHICS_INPUT_FIXED = os.path.join(BASE_PATH, 'raw', 'demographic_scenario_data')
DEMOGRAPHICS_OUTPUT_FIXED = os.path.join(BASE_PATH, 'processed')

#####################################
# READ WTP LOOKUP TABLE
#####################################

def read_wtp_data():
    """
    Contains data on wtp by age :
        - Age 
        - Willingness to Pay
        - Willingness to Adopt
    """
    wtp_data = []

    with open(os.path.join(BASE_PATH, 'raw', 'willingness_to_pay', 'simple_willingness_to_pay_scenarios.csv'), 'r') as wtp_file:
        reader = csv.reader(wtp_file)
        next(reader, None)
        # Put the values in the population dict
        for row in reader:
            wtp_data.append({
                'age': row[0],
                'wtp': int(row[1]),
                'wta': float(row[2])
            })

        return wtp_data

#####################################
# READ MSOA DEMOGRAPHIC DATA
#####################################

msoa_year_files = {
     year: os.path.join(DEMOGRAPHICS_INPUT_FIXED, 'ass_E07000008_MSOA11_{}.csv'.format(year))
     for year in TIMESTEPS
}

MSOA_data = []

def read_msoa_data():
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

    for filename in msoa_year_files.values():
        # Open file
        with open(filename, 'r') as year_file:
            year_reader = csv.reader(year_file)
            next(year_reader, None)
            # Put the values in the population dict
            for line in year_reader:
                MSOA_data.append({
                    'PID': line[0],
                    'MSOA': line[1],
                    'gender': line[2],
                    'age': line[3],
                    'ethnicity': line[4],
                    'HID': line[5],
                    'year': int(filename[-8:-4]),
                })     

    return MSOA_data

#####################################
# ADD WTP TO MSOA DATA
#####################################

def add_wtp_to_MSOA_data(consumer_data, population_data):
    """
    Take the WTP lookup table for all ages. Add to the population data based on age.
    """
    d1 = {d['age']:d for d in consumer_data}

    population_data = [dict(d, **d1.get(d['age'], {})) for d in population_data]	

    return population_data

#####################################
# READ OA DATA
#####################################

oa_year_files = {
     year: os.path.join(DEMOGRAPHICS_INPUT_FIXED, 'ass_hh_E07000008_OA11_{}.csv'.format(year))
     for year in TIMESTEPS
}

OA_data = []

def read_oa_data():
    """
    MSOA data contains individual level demographic characteristics including:
        - HID - Household ID
        - OA - Output Area ID
        - SES - Household Socio-Economic Status
        - year - year
    """
    
    for filename in oa_year_files.values():
        # Open file
        with open(filename, 'r') as year_file:
            year_reader = csv.reader(year_file)
            next(year_reader, None)
            # Put the values in the population dict
            for line in year_reader:
                OA_data.append({
                    'HID': line[0],
                    'OA': line[1],
                    'SES': line[12],
                    'year': int(filename[-8:-4]),
                })     

    return OA_data

#####################################
# COMBINE MSOA AND OA DATA
#####################################

def merge_two_lists_of_dicts(msoa_list_of_dicts, oa_list_of_dicts, parameter1, parameter2):
    """
    Combine the msoa and oa dicts using the household indicator and year keys. 
    """
    d1 = {(d[parameter1], d[parameter2]):d for d in oa_list_of_dicts}

    msoa_list_of_dicts = [dict(d, **d1.get((d[parameter1], d[parameter2]), {})) for d in msoa_list_of_dicts]	

    return msoa_list_of_dicts

#####################################
# AGGREGATE WTP DATA
#####################################


from collections import defaultdict
from operator import itemgetter

def aggregate_wtp_and_wta_by_household(data):
    """
    Aggregate wtp by household by Household ID (HID), Socio Economic Status (SES) and year.
    """
    d = defaultdict(lambda: defaultdict(int))

    group_keys = ['HID', 'SES', 'year']
    sum_keys = ['wtp', 'wta']

    for item in data:
        for key in sum_keys:
            d[itemgetter(*group_keys)(item)][key] += item[key]

    results = [{**dict(zip(group_keys, k)), **v} for k, v in d.items()]

    return results

#####################################
# IMPORT PREMISES DATA
#####################################

def read_premises_data():
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

    with open(os.path.join(BASE_PATH,'raw','layer_5_premises','cambridge_points.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            premises_data.append({
                'id': line[0],
                'oa': line[1],
                'residential_address_count': line[2],
                'non_residential_address_count': line[3],
                'postgis_geom': line[4],
                'E': line[5],
                'N':line[6],
            })
    
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

#####################################
# MERGE PREMISES AND HOUSEHOLD WTP
#####################################

def merge_prems_and_housholds(premises_data, household_data):
    """
    Merges two aligned datasets, zipping row to row. 
    Deals with premises_data having multiple repeated dict references due to expand function.
    """
    result = [a.copy() for a in premises_data]

    [a.update(b) for a, b in zip(result, household_data)]

    return result

#####################################
# WRITE DATA
#####################################

def csv_writer(data, filename, fieldnames):
    """
    Write data to a CSV file path
    """
    with open(os.path.join(DEMOGRAPHICS_OUTPUT_FIXED, filename),'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)

#####################################
# EXECUTE FUNCTIONS
#####################################

print('Loading Willingness To Pay data')
wtp_data = read_wtp_data()

print('Loading MSOA data')
MSOA_data = read_msoa_data()

print('Adding WTP data to MSOA data')
MSOA_data = add_wtp_to_MSOA_data(wtp_data, MSOA_data)

print('Loading OA data')
oa_data = read_oa_data()

print('Adding MSOA data to OA data')
final_data = merge_two_lists_of_dicts(MSOA_data, oa_data, 'HID', 'year')

print('Aggregating WTP by household')
household_wtp = aggregate_wtp_and_wta_by_household(final_data)

print('Write WTP by household to .csv')
wtp_fieldnames = ['HID','SES','wtp','wta','year','my_residential_id']
csv_writer(household_wtp, 'household_wtp.csv', wtp_fieldnames)

print('Reading premises data')
premises = read_premises_data()

print('Expand premises entries')
premises = expand_premises(premises)

print('Adding household data to premises')
premises = merge_prems_and_housholds(premises, household_wtp)

print('Write premises_multiple by household to .csv')
premises_fieldnames = ['id','oa','residential_address_count','non_residential_address_count','postgis_geom','E','N','my_residential_id', 'HID','SES','year','wtp','wta']
csv_writer(premises, 'dummy_premises_data.csv', premises_fieldnames)

print('Script complete')
