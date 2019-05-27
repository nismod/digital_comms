import os
import configparser
import fiona
import sys
import glob
import csv
import math

from itertools import tee

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# setup file locations and data files
#####################################

DATA_RAW_SHAPES = os.path.join(BASE_PATH, 'raw', 'd_shapes')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')

#####################################
# read files
#####################################

def read_lads():

    with fiona.open(os.path.join(
        DATA_RAW_SHAPES, 'lad_uk_2016-12', 'lad_uk_2016-12.shp'
        ), 'r') as source:
        for lad in source:
            yield lad['properties']['name']

def read_postcode_sectors():
    with fiona.open(os.path.join(
        DATA_INTERMEDIATE,'postcode_sectors', '_processed_postcode_sectors.shp'
        ), 'r') as source:
        return [pcd_sector for pcd_sector in source]

def read_mobile_geotype_lut(lads):

    geotype_lut = []

    ids_seen = set()

    for lad in lads:
        lad_path = os.path.join(DATA_INTERMEDIATE,'mobile_geotype_lut', lad)
        path_list = glob.iglob(lad_path + '/*.csv', recursive=True)
        for path in path_list:
            with open(path, 'r') as source:
                reader = csv.DictReader(source)
                for line in reader:
                    if line['postcode_sector'] not in ids_seen:

                        ids_seen.add(line['postcode_sector'])

                        geotype_lut.append({
                            'postcode_sector': line['postcode_sector'],
                            'indoor_probability': line['indoor_probability'],
                            'outdoor_probability': line['outdoor_probability'],
                            'residential_count': line['residential_count'],
                            'non_residential_count': line['non_residential_count'],
                            'all_buildings':  (
                                float(line['residential_count']) +
                                float(line['non_residential_count'])
                                ),
                            'area': line['area'],
                            'density': (
                                float(line['residential_count']) +
                                float(line['non_residential_count'])
                                ) / float(line['area']),
                        })


    return geotype_lut


def pairwise(iterable):
    """Return iterable of 2-tuples in a sliding window
    Parameters
    ----------
    iterable: list
        Sliding window
    Returns
    -------
    list of tuple
        Iterable of 2-tuples
    Example
    -------
        >>> list(pairwise([1,2,3,4]))
            [(1,2),(2,3),(3,4)]
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def select_postcode_sectors(postcode_sectors, segment_number):

    ranked = sorted(postcode_sectors, key=lambda x: x['density'])

    num_sectors = len(postcode_sectors)

    percentile_allocated = []
    for rank, sector in enumerate(ranked):
        rank_plus = rank + 1
        percentile = math.floor(segment_number * (rank_plus/ num_sectors))
        percentile_allocated.append({
                'postcode_sector': sector['postcode_sector'],
                'density': sector['density'],
                'percentile': percentile
        })

    output = []

    for i in range(1, segment_number+1):
        list_of_dicts = []
        for sector in percentile_allocated:
            if sector['percentile'] == i:
                list_of_dicts.append(sector)

        length = len(list_of_dicts)

        if length > 0:
            middle = int(round(length/2))
            output.append(list_of_dicts[middle])
        else:
            pass

    return output


def get_selection_list(selection_dict):

    output = []

    for selection in selection_dict:
        output.append(selection['postcode_sector'])

    return output

def segments_for_transmitter_module():

    segment_number = 3

    lads = read_lads()

    pcd_sectors = read_mobile_geotype_lut(lads)

    selection_dict = select_postcode_sectors(pcd_sectors, segment_number)

    selection = get_selection_list(selection_dict)

    return selection

####################################
# run script
####################################

if __name__ == "__main__":

    selection = []

    SYSTEM_INPUT = os.path.join('data', 'digital_comms', 'raw')

    if len(sys.argv) < 2 or sys.argv[1] == 'national':

        pcd_sectors = read_postcode_sectors()
        selection = [
            (pcd_sector['properties']['postcode'].replace(' ', ''))
            for pcd_sector in pcd_sectors
            ]

    elif sys.argv[1] == 'testbeds':
        selection = [
            'CB1 1',
            'BS1 5',
        ]

    elif sys.argv[1] == 'segments_for_transmitter_module':

        selection = segments_for_transmitter_module()

    print(*selection, sep='\n')
