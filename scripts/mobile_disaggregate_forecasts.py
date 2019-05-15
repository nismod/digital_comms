"""
Disaggregate population forecasts from Local Authority
District level to postcode sectors.
Written by Edward J. Oughton
12th May 2019

"""
import configparser
import csv
import os

import fiona

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')
SYSTEM_INPUT_PATH  = os.path.join(
    BASE_PATH, 'raw', 'b_mobile_model','mobile_model_1.0'
    )

def lookup_pcd_to_lad():
    """
    Yield lookup table results for postcode sectors to local
    authority districts.
    """
    path = os.path.join(
        INTERMEDIATE, 'pcd_sector_to_lad_lut', 'pcd_sector_to_lad_lut.csv'
        )

    loaded_data = []

    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        for line in reader:
            loaded_data.append({
                'postcode_sector': line['postcode_sector'],
                'lad': line['lad']
            })

    output = []
    data_seen = set()

    for datum in loaded_data:
        if datum['postcode_sector'] in data_seen:
            continue
        data_seen.add(datum['postcode_sector'])
        output.append(datum)

    return output

def load_in_weights():

    path = os.path.join(
        SYSTEM_INPUT_PATH, 'scenario_data', 'population_baseline_pcd.csv'
        )

    population_data = []

    with open(path, 'r') as source:
        reader = csv.reader(source)
        for line in reader:
            if int(line[0]) == 2015:
                population_data.append({
                    'postcode_sector': line[1],
                    'population': int(line[2]),
                })

    return population_data

def merge_weights_and_lut(lut, weights):

    output = []

    for entry in lut:
        entry_id = entry['postcode_sector']
        for weight in weights:
            weight_id = weight['postcode_sector'].replace(' ', '')
            if entry_id == weight_id:
                output.append({
                    'postcode_sector': entry_id,
                    'lad': weight['lad'],
                    'population': entry['population'],
                })

    return output

def calculate_lad_population(lut):

    output = {}

    lad_ids = set()

    for entry in lut:
        lad_ids.add(entry['lad'])

    lad_population = []

    for lad_id in lad_ids:
        population = 0
        for entry in lut:
            if entry['lad'] == lad_id:
                population += entry['population']
        lad_population.append({
            'lad': lad_id,
            'population': population,
        })

    return lad_population

def create_final_lut(lut, lad_population_lut):

    output = []

    for lad_lut in lad_population_lut:
        for entry in lut:
            if entry['lad'] == lad_lut['lad']:
                output.append({
                    'postcode_sector': entry['postcode_sector'],
                    'lad': entry['lad'],
                    'lad_population': lad_lut['population'],
                    'population': entry['population'],
                    'weight': entry['population'] / lad_lut['population']
                })

    return output

def get_forecast(filename):

    path = os.path.join(SYSTEM_INPUT_PATH, 'scenario_data', filename)

    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        for line in reader:
            yield {
                'year': line['timestep'],
                'lad': line['lad_gb_2016'],
                'population': line['population'],
            }

def disaggregate(forecast, lut):

    output = []

    for line in forecast:
        forecast_lad_id = line['lad']
        for postcode_sector in lut:
            pcd_sector_lad_id = postcode_sector['lad']
            if forecast_lad_id == pcd_sector_lad_id:
                output.append({
                    'year': line['year'],
                    'lad': line['lad'],
                    'postcode_sector': postcode_sector['postcode_sector'],
                    'population': int(
                        float(line['population']) *
                        float(postcode_sector['weight'])
                        )
                })

    return output


def csv_writer(data, filename):
    """
    Write data to a CSV file path
    """
    # Create path
    directory = os.path.join(SYSTEM_INPUT_PATH, 'scenario_data', 'results')
    if not os.path.exists(directory):
        os.makedirs(directory)

    fieldnames = []
    for name, value in data[0].items():
        fieldnames.append(name)

    with open(os.path.join(directory, filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":

    lut = lookup_pcd_to_lad()

    weights = load_in_weights()

    lut = merge_weights_and_lut(weights, lut)

    lad_population_lut = calculate_lad_population(lut)

    final_lut = create_final_lut(lut, lad_population_lut)

    files = [
        'arc_population__baseline.csv',
        'arc_population__scenario1.csv',
        'arc_population__scenario2.csv',
    ]

    for scenario_file in files:

        forecast = get_forecast(scenario_file)

        disaggregated_forecast = disaggregate(forecast, final_lut)

        filename = os.path.join('pcd_' + scenario_file)

        csv_writer(disaggregated_forecast, filename)
