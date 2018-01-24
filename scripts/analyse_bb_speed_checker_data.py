"""Extract lad id, name
"""
import configparser
import csv
import os

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['Broadband Speed Checker']
INPUT_FILENAME = os.path.join(BASE_PATH, 'UniversityOfCambrigeFinalReport.csv')

# Read in LAD code lookup (old code => new code)
# header: LAD16CD,LAD16CDO,LAD16NM (i.e. new code, old code, name)
bb_user_data = {}
with open(INPUT_FILENAME, 'r', encoding='utf-8-sig') as input_file:
    r = csv.DictReader(input_file)
    for line in r:
        DateTime = line['DateTime']
        new_code = line['LAD16CD']
        lad_code_lookup[old_code] = new_code

