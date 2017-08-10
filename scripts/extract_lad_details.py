"""Extract lad id, name
"""
import configparser
import csv
import os

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
LAD_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'initial_system', 'lads.csv')
LAD_CODE_FILENAME = os.path.join(BASE_PATH, 'source_data', 'lad_codes.csv')

# Read in LAD details
# header: LAD16CD,LAD16CDO,LAD16NM (i.e. new code, old code, name)
lad_code_lookup = {}
with open(LAD_CODE_FILENAME, 'r', encoding='utf-8-sig') as input_file:
    r = csv.DictReader(input_file)
    with open(LAD_OUTPUT_FILENAME, 'w', newline='') as output_file:
        w = csv.writer(output_file)
        w.writerow(('id', 'name',))
        for line in r:
            w.writerow((line['LAD16CD'], line['LAD16NM']))
