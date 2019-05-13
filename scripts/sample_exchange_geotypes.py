import os
import csv
import configparser
from random import shuffle

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw', 'a_fixed_model', 'exchange_geotypes')

def import_exchange_data():

    exchanges = []

    with open(os.path.join(DATA_RAW, 'exchange_properties.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader, None)
        # Put the values in the population dict
        for line in reader:
            exchanges.append({
                'id': line[0],
                'Name': line[1],
                'pcd': line[2],
                'Region': line[3],
                'County': line[4],
                'geotype': line[5],
                'prems_over': int(line[6]),
                'prems_under': int(line[7]),
            })

    return exchanges

def count_exchanges(exchange_data):

    inner_london = []
    large_city = []
    small_city = []
    over_20k = []
    over_10k = []
    over_3k = []
    over_1k = []
    under_1k = [] 

    for exchange in exchange_data:
        if exchange['geotype'] == 'inner london':
            inner_london.append(exchange)
        elif exchange['geotype'] == 'large city':
            large_city.append(exchange)
        elif exchange['geotype'] == 'small city':
            small_city.append(exchange)
        elif exchange['geotype'] == '>20k lines':
            over_20k.append(exchange)
        elif exchange['geotype'] == '>10k lines':
            over_10k.append(exchange)
        elif exchange['geotype'] == '>3k lines':
            over_3k.append(exchange)
        elif exchange['geotype'] == '>1k lines':
            over_1k.append(exchange)
        elif exchange['geotype'] == '<1k lines':
            under_1k.append(exchange)

    print('inner_london is {}'.format(len(inner_london)))
    print('large_city is {}'.format(len(large_city)))
    print('small_city is {}'.format(len(small_city)))
    print('over_20k is {}'.format(len(over_20k)))
    print('over_10k is {}'.format(len(over_10k)))
    print('over_3k is {}'.format(len(over_3k)))
    print('over_1k is {}'.format(len(over_1k)))
    print('under_1k is {}'.format(len(under_1k)))

    shuffle(inner_london)
    shuffle(large_city)
    shuffle(small_city)
    shuffle(over_20k)
    shuffle(over_10k)
    shuffle(over_3k)
    shuffle(over_1k)
    shuffle(under_1k)

    output1 = (inner_london[:70] + large_city[:177] + small_city[:169] + over_20k[:130] +
            over_10k[:190] + over_3k[:270] + over_1k[:290] + under_1k[:323])

    output2 = (inner_london[:3] + large_city[:3] + small_city[:3] + over_20k[:3] +
            over_10k[:3] + over_3k[:3] + over_1k[:3] + under_1k[:3])

    return output1, output2

def csv_writer(data, filename, fieldnames):
    """
    Write data to a CSV file path
    """
    
    with open(os.path.join(DATA_RAW, filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)

####################################
# RUN SCRIPT
####################################

exchanges = import_exchange_data()

exchange_sample1, exchange_sample2 = count_exchanges(exchanges)

fieldnames = ['id','Name','pcd','Region','County','geotype','prems_over', 'prems_under']
csv_writer(exchange_sample1, 'exchange_geotype_sample1.csv', fieldnames)
csv_writer(exchange_sample2, 'exchange_geotype_sample2.csv', fieldnames)