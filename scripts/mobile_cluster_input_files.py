import os
import configparser
import fiona
import sys

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# setup file locations and data files
#####################################

DATA_RAW_SHAPES = os.path.join(BASE_PATH, 'raw', 'd_shapes')

#####################################
# read files
#####################################

def read_postcode_sectors():
    with fiona.open(os.path.join(
        DATA_RAW_SHAPES,'postcode_sectors', '_postcode_sectors.shp'
        ), 'r') as source:
        return [pcd_sector for pcd_sector in source]

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
            'CB1 1', # Primrose Hill (Inner London)
            'BS1 5', # Chapeltown (Major City)
        ]

    print(*selection, sep='\n')
