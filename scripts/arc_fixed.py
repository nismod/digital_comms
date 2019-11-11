"""
Arc fixed broadband cost analysis

Written by Edward Oughton and Tom Russell

30th October 2019

"""

import configparser
import csv
import os
from itertools import tee

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA = os.path.join(BASE_PATH,'..','arc_fixed_bb')
RESULTS = os.path.join(BASE_PATH, '..','arc_fixed_bb', 'results')

def read_data(path):

    with open(path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for item in reader:
            yield item


def lad_geotypes(urban_rural_lut):
    #1 = Mainly rural
    #2 = Largely rural
    #3 = Urban with significant rural
    #4 = Urban with city and town
    #5 = Urban with minor conurbation
    #6 = Urban with major conurbation

    lad_geotypes = []

    for item in urban_rural_lut:
        lad_geotypes.append({
            'lad11cd': item['LAD11CD'],
            'geotype': int(item['RUC11CD']),
            'geotype_name': item['RUC11']
        })

    return lad_geotypes


def processing_dwellings(data):

    dwelling_data = []

    for dwelling_item in data:
        dwelling_data.append({
            'scenario': dwelling_item['scenario'],
            'oa11cd': dwelling_item['oa11cd'],
            'lad11cd': dwelling_item['lad11cd'],
            'lad11nm': dwelling_item['lad11nm'],
            'dwellings_oa__final': dwelling_item['dwellings_oa__final'],
        })

    return dwelling_data


def process_geotypes(dwelling_data, urban_rural_lut, lad_areas):

    oa_geotypes = []

    for dwelling_item in dwelling_data:
        if dwelling_item['lad11cd'] in lad_areas: #26 LADs in the Arc
            for geotype_item in urban_rural_lut:
                if dwelling_item['lad11cd'] == geotype_item['lad11cd']:
                    oa_geotypes.append({
                        'scenario': dwelling_item['scenario'],
                        'oa11cd': dwelling_item['oa11cd'],
                        'lad11cd': dwelling_item['lad11cd'],
                        'lad11nm': dwelling_item['lad11nm'],
                        'dwellings_oa__final': dwelling_item['dwellings_oa__final'],
                        'geotype': int(geotype_item['geotype']),
                        'geotype_name': geotype_item['geotype_name']
                    })

    return oa_geotypes


def process_area_data(dwelling_data, area_data):

    final_data = []

    for area in area_data:
        for item in dwelling_data:
            if area['oa11cd'] == item['oa11cd']:
                final_data.append({
                    'scenario': item['scenario'],
                    'oa11cd': item['oa11cd'],
                    'lad11cd': item['lad11cd'],
                    'lad11nm': item['lad11nm'],
                    'dwellings_oa__final': item['dwellings_oa__final'],
                    'geotype': int(item['geotype']),
                    'geotype_name': item['geotype_name'],
                    'dwelling_density': (
                        int(item['dwellings_oa__final']) /
                        (float(area['st_areasha']) / 100)),
                    'area_km2': float(area['st_areasha']) / 100,
                })

    return final_data


def lad_dwelling_density(dwelling_data, urban_rural_lut):

    unique_scenarios = set()

    for item in dwelling_data:
        unique_scenarios.add(item['scenario'])

    interim = []

    unique_lads = set()

    for oa in dwelling_data:
        unique_lads.add(oa['lad11cd'])

    for scenario in list(unique_scenarios):
        for lad in list(unique_lads):
            area_of_lad = 0
            dwellings_in_lad = 0
            for oa in dwelling_data:
                if scenario == oa['scenario']:
                    area_of_lad += float(oa['area_km2'])
                    dwellings_in_lad += float(oa['dwellings_oa__final'])
            interim.append({
                'scenario': scenario,
                'lad11cd': lad,
                'area_of_lad': area_of_lad,
                'dwellings_in_lad': dwellings_in_lad,
            })

    output = []

    for lad in interim:
        for item in urban_rural_lut:
            if lad['lad11cd'] == item['lad11cd']:
                output.append({
                    'scenario': lad['scenario'],
                    'lad11cd': lad['lad11cd'],
                    'area_of_lad': lad['area_of_lad'],
                    'dwellings_in_lad': lad['dwellings_in_lad'],
                    'geotype': item['geotype'],
                    'geotype_name': item['geotype_name'],
                })

    return output


def process_cost_data(cost_data):

    output = []

    for item in cost_data:
        if item['cost_type'] == (
            'Whole Life Cost per Premises (on a 30-year life) excl. Connection costs'
            ):
            output.append({
                'geotype': item['geotype'],
                'scenario': item['scenario'],
                'cost': item['cost'],
            })

    return output


def add_costs_to_lad_lut(lad_dwelling_density_lut, cost_data):

    output = []

    for item in lad_dwelling_density_lut:
        for cost_item in cost_data:
            if int(item['geotype']) == int(cost_item['geotype']):
                output.append({
                    'scenario': item['scenario'],
                    'lad11cd': item['lad11cd'],
                    'area_of_lad': item['area_of_lad'],
                    'dwellings_in_lad': item['dwellings_in_lad'],
                    'dwelling_density': item['dwellings_in_lad'] / item['area_of_lad'],
                    'geotype': item['geotype'],
                    'geotype_name': item['geotype_name'],
                    'strategy': cost_item['scenario'],
                    'cost': cost_item['cost'],
                })

    return output


def add_cost_to_oas(oa_dwelling_data, lad_dwelling_density_lut):

    unique_strategies = set()

    for item in lad_dwelling_density_lut:
        unique_strategies.add(item['strategy'])


    output = []

    for oa in oa_dwelling_data:
        for strategy in unique_strategies:
            dwelling_density = oa['dwelling_density']
            cost = lookup_cost(dwelling_density, strategy, lad_dwelling_density_lut)
            output.append({
                'scenario': oa['scenario'],
                'strategy': strategy,
                'oa11cd': oa['oa11cd'],
                'lad11cd': oa['lad11cd'],
                'lad11nm': oa['lad11nm'],
                'dwellings_oa__final': oa['dwellings_oa__final'],
                'geotype': int(oa['geotype']),
                'geotype_name': oa['geotype_name'],
                'dwelling_density': (
                    int(oa['dwellings_oa__final']) /
                    (float(oa['area_km2']) / 100)),
                'area_km2': float(oa['area_km2']) / 100,
                'cost_per_dwelling': cost,
                'total_cost': cost * int(oa['dwellings_oa__final']),
            })

    return output


def pairwise(iterable):
    """Return iterable of 2-tuples in a sliding window

        >>> list(pairwise([1,2,3,4]))
        [(1,2),(2,3),(3,4)]
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def lookup_cost(dwelling_density, strategy, lad_dwelling_density_lut):
    """

    """
    density_costs = []
    for item in lad_dwelling_density_lut:
        if item['strategy'] == strategy:
            density_costs.append(
                (float(item['dwelling_density']), float(item['cost']))
            )

    lowest_density, lowest_cost = density_costs[0]
    if dwelling_density < lowest_density:
        return interpolate(0, 0, lowest_density, lowest_cost, dwelling_density) #Tom can you check this please?

    for a, b in pairwise(density_costs):
        lower_density, lower_capacity = a
        upper_density, upper_capacity = b
        if lower_density <= dwelling_density and dwelling_density < upper_density:
            return interpolate(lower_density, lower_capacity, upper_density, upper_capacity, dwelling_density)

    highest_density, highest_capacity = density_costs[-1]

    return highest_capacity


def interpolate(x0, y0, x1, y1, x):
    """
    Linear interpolation between two values.

    """
    y = (y0 * (x1 - x) + y1 * (x - x0)) / (x1 - x0)
    return y


def csv_writer(data, directory, filename):
    """
    Write data to a CSV file path
    """
    # Create path
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

    LAD_AREAS = [
        'E06000031',
        'E07000005',
        'E07000006',
        'E07000007',
        'E06000032',
        'E06000042',
        'E06000055',
        'E06000056',
        'E07000004',
        'E07000008',
        'E07000009',
        'E07000010',
        'E07000011',
        'E07000012',
        'E07000150',
        'E07000151',
        'E07000152',
        'E07000153',
        'E07000154',
        'E07000155',
        'E07000156',
        'E07000177',
        'E07000178',
        'E07000179',
        'E07000180',
        'E07000181',
    ]

    print('load geotype lut')
    path = os.path.join(DATA, 'RUC11_LAD11_ENv2.csv')
    urban_rural_lut = read_data(path)

    print('process geotype lut')
    urban_rural_lut = lad_geotypes(urban_rural_lut)

    print('load dwelling data')
    path = os.path.join(DATA, 'processed','oa_dwellings.csv')
    data = read_data(path)

    print('processing dwelling data')
    oa_dwelling_data = processing_dwellings(data)[:200]

    print('process geotypes')
    oa_dwelling_data = process_geotypes(oa_dwelling_data, urban_rural_lut, LAD_AREAS)

    print('load area data')
    path = os.path.join(DATA, 'processed','oas_with_dwellings_initial.csv')
    area_data = read_data(path)

    print('process area data')
    oa_dwelling_data = process_area_data(oa_dwelling_data, area_data)

    print('get lad dwelling density')
    lad_dwelling_density_lut = lad_dwelling_density(oa_dwelling_data, urban_rural_lut)

    print('load nic costs')
    path = os.path.join(DATA, 'nic_costs.csv')
    cost_data = read_data(path)

    print('process cost data')
    cost_data = process_cost_data(cost_data)

    print('add costs to lad lut')
    lad_dwelling_density_lut = add_costs_to_lad_lut(lad_dwelling_density_lut, cost_data)

    print('add costs to oas lut')
    output = add_cost_to_oas(oa_dwelling_data, lad_dwelling_density_lut)

    csv_writer(output, RESULTS, 'results.csv')
