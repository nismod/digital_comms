
import configparser
import csv
import os
import statistics
import pprint

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

BASE_YEAR = 2017
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
        - WTP
    """
    wtp_data = []

    with open(os.path.join(BASE_PATH, 'raw', 'willingness_to_pay', 'simple_willingness_to_pay_scenarios.csv'), 'r') as wtp_file:
        reader = csv.reader(wtp_file)

        # Put the values in the population dict
        for row in reader:
            wtp_data.append({
                'age': row[0],
                'wtp': row[1]
            })

        return wtp_data

#####################################
# READ MSOA DEMOGRAPHIC DATA
#####################################

msoa_year_files = {
     year: os.path.join(DEMOGRAPHICS_INPUT_FIXED, 'ass_E07000008_MSOA11_{}.csv'.format(year))
     for year in TIMESTEPS
}

def read_msoa_data():
    """
    MSOA data contains individual level demographic characteristics including:
        - PID - Person ID
        - Area ID
        - DC1117EW_C_SEX - Gender
        - DC1117EW_C_AGE - Age
        - DC2101EW_C_ETHPUK11 - Ethnicity
        - HID - Household ID
    """
    MSOA_data = []

    for filename in msoa_year_files.values():
        # Open file
        with open(filename, 'r') as year_file:
            year_reader = csv.reader(year_file)
            # Put the values in the population dict
            for line in year_reader:
                MSOA_data.append({
                    'PID': line[0],
                    'MSOA': line[1],
                    'gender': line[2],
                    'age': line[3],
                    'ethnicity': line[4],
                    'HID': line[5],
                    'year': filename[56:-4],
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

def read_oa_data():
    """
    MSOA data contains individual level demographic characteristics including:
        - HID - Household ID
        - Area ID

        - HID - Household ID
    """
    OA_data = []

    for filename in oa_year_files.values():
        # Open file
        with open(filename, 'r') as year_file:
            year_reader = csv.reader(year_file)
            # Put the values in the population dict
            for line in year_reader:
                OA_data.append({
                    'HID': line[0],
                    'OA': line[1],
                    'SES': line[12],
                    'year': filename[-8:-4],
                })     

            return OA_data


#####################################
# ALLOCATE DEMOGRAPHIC DATA
#####################################

#sum individual WTP to household

#allocate premises IDs

#####################################
# EXECUTE FUNCTIONS
#####################################

print('Loading MSOA data')
MSOA_data = read_msoa_data()

print('Loading Willingness To Pay data')
wtp_data = read_wtp_data()

print('Adding WTP data to MSOA data')
#MSOA_data = add_wtp_to_MSOA_data(wtp_data, MSOA_data)

print('Loading OA data')
oa_data = read_oa_data()


pprint.pprint(oa_data)
