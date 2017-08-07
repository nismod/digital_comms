"""Extract total resident population for high, baseline and low scenarios
"""
import configparser
import csv
import os

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
INPUT_FILENAME = os.path.join(BASE_PATH, 'scenario_data', 'population_population_regional_breakdown.csv')
LAD_CODE_FILENAME = os.path.join(BASE_PATH, 'source_data', 'lad_codes.csv')
LAD_INTERMEDIATE_CODE_FILENAME = os.path.join(BASE_PATH, 'source_data', 'intermediate_lad_codes.csv')
# LAD_WALES_FILENAME = os.path.join(BASE_PATH, 'source_data', 'wales_lad_2011_clipped.csv')
# LAD_ENGLAND_FILENAME = os.path.join(BASE_PATH, 'source_data', 'england_lad_2011_clipped.csv')
SCENARIOS = ("High", "Baseline", "Low")

# Read in LAD code lookup (old code => new code)
# header: LAD16CD,LAD16CDO,LAD16NM (i.e. new code, old code, name)
lad_code_lookup = {}
with open(LAD_CODE_FILENAME, 'r', encoding='utf-8-sig') as input_file:
    r = csv.DictReader(input_file)
    for line in r:
        old_code = line['LAD16CDO']
        new_code = line['LAD16CD']
        lad_code_lookup[old_code] = new_code

with open(LAD_INTERMEDIATE_CODE_FILENAME, 'r') as input_file:
    r = csv.DictReader(input_file)
    for line in r:
        old_code = line['old_code']
        intermediate_code = line['intermediate_code']
        new_code = lad_code_lookup[intermediate_code]
        lad_code_lookup[old_code] = new_code

missing_codes = []

# Read population scenarios file (from ITRC projections),
# outputting total population (both genders, all ages) for each LAD
output_files = {}
output_writers = {}
with open(INPUT_FILENAME, 'r') as input_file:
    r = csv.DictReader(input_file)
    for scenario in SCENARIOS:
        output_filename = os.path.join(
            BASE_PATH,
            'scenario_data',
            'population_{}_lad.csv'.format(scenario.lower()))
        output_files[scenario] = open(output_filename, 'w', newline='')
        output_writers[scenario] = csv.writer(output_files[scenario])

    for line in r:
        scenario = line['scenario']
        if scenario in SCENARIOS and line['gender'] == '2':
            pop = line['cat_ages_total']
            old_lad_code = line['location']
            if old_lad_code not in lad_code_lookup:
                if old_lad_code not in missing_codes:
                    missing_codes.append(old_lad_code)
                    print(old_lad_code)
                continue
            lad = lad_code_lookup[old_lad_code]
            year = line['year']
            output_writers[scenario].writerow((year,lad,pop))

# Close output files
for output_file in output_files.values():
    output_file.close()