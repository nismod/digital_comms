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

def read_lads():
    with fiona.open(
        os.path.join(DATA_RAW_SHAPES,'lad_uk_2016-12', 'lad_uk_2016-12.shp'), 'r') as source:
        return [lad for lad in source]

####################################
# run script
####################################

if __name__ == "__main__":

    selection = []

    SYSTEM_INPUT = os.path.join('data', 'digital_comms', 'raw')

    lads = read_lads()
    selection = [(lad['properties']['name']) for lad in lads]

    print(*selection, sep='\n')
