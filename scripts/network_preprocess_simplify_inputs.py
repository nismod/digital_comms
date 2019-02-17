import os
import sys
import configparser
import csv
from collections import defaultdict

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW_INPUTS = os.path.join(BASE_PATH, 'raw', 'a_fixed_model')
DATA_INTERMEDIATE_INPUTS = os.path.join(BASE_PATH, 'intermediate')

def get_unique_postcodes_by_exchanges(lower_units):
    """
    Function to get unique postcodes by exchange. 
    Produce a dict with the key being the grouping variable and the value being a list.  
    """

    all_data = []

    for item in lower_units:
        all_data.append(item[grouping_variable])

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

def write_premises_to_csv(data, folder, file_prefix, fieldnames):
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

# #Run functions
# #simplify all pcd_to_exchange data into one single file
# pcd_to_exchange_data = read_pcd_to_exchange_lut()
# pcd_to_exchange_data = pcd_to_exchange_data
# pcd_to_exchange_data = allocate_lower_units_to_areas(pcd_to_exchange_data, 'exchange_id', 'postcode')
# fieldnames = ['postcode']
# write_premises_to_csv(pcd_to_exchange_data, 'pcd_2_exchange_luts', 'pcd_to_ex_', fieldnames)

#simplify all pcd_to_cabinet data into one single file
pcd_to_cabinet_data = read_pcd_to_cabinet_lut()
pcd_to_cabinet_data = get_unique_postcodes_to_cabs_by_exchange(pcd_to_cabinet_data)
fieldnames = ['postcode','cabinet','exchange_only_flag']
write_premises_to_csv(pcd_to_cabinet_data, 'pcd_to_cabinet_by_exchange', 'pcd_to_cab_', fieldnames)


