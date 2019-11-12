"""
Arc fixed broadband cost analysis

Written by Edward Oughton and Tom Russell

30th October 2019

"""

import configparser
import csv
import os

from collections import defaultdict
from itertools import tee

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..', 'scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA = os.path.join(BASE_PATH,'..','arc_fixed_bb')
RESULTS = os.path.join(BASE_PATH, '..','arc_fixed_bb', 'results')

COST_LOWER_BOUND = 500


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
            'dwellings_oa__final': int(dwelling_item['dwellings_oa__final']),
            'dwellings_oa__initial': int(dwelling_item['dwellings_oa__initial']),
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
                        'dwellings_oa__initial': dwelling_item['dwellings_oa__initial'],
                        'geotype': int(geotype_item['geotype']),
                        'geotype_name': geotype_item['geotype_name']
                    })

    return oa_geotypes


def process_area_data(dwelling_data, area_data):

    final_data = []

    area_lu = {area['oa11cd']: float(area['st_areasha']) / 1e6 for area in area_data}

    for item in dwelling_data:
        area = area_lu[item['oa11cd']]
        final_data.append({
            'scenario': item['scenario'],
            'oa11cd': item['oa11cd'],
            'lad11cd': item['lad11cd'],
            'lad11nm': item['lad11nm'],
            'dwellings_oa__final': item['dwellings_oa__final'],
            'dwellings_oa__initial': item['dwellings_oa__initial'],
            'geotype': item['geotype'],
            'geotype_name': item['geotype_name'],
            'dwelling_density': item['dwellings_oa__final'] / area,
            'area_km2': area,
        })

    return final_data


def lad_dwelling_density(dwelling_data, urban_rural_lut):
    """Calculate initial/baseline LAD dwelling density
    """
    interim = []

    unique_lads = set()

    for oa in dwelling_data:
        unique_lads.add(oa['lad11cd'])

    for lad in list(unique_lads):
        area_of_lad = 0
        dwellings_in_lad = 0
        for oa in dwelling_data:
            if oa['scenario'] == 'baseline' and lad == oa['lad11cd']:
                area_of_lad += float(oa['area_km2'])
                dwellings_in_lad += float(oa['dwellings_oa__initial'])
        interim.append({
            'lad11cd': lad,
            'area_of_lad': area_of_lad,
            'dwellings_in_lad': dwellings_in_lad,
        })

    output = []

    for lad in interim:
        for item in urban_rural_lut:
            if lad['lad11cd'] == item['lad11cd']:
                output.append({
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

def cost_for_mean_density(lad_density_cost):
    """Calculate mean density of LADs by geotype
    """
    geotype_strategy_densities = defaultdict(list)
    for item in lad_density_cost:
        geotype_strategy_densities[item['geotype'], item['strategy']] \
            .append(item['dwelling_density'])

    density_cost = []
    for (geotype, strategy), densities in geotype_strategy_densities.items():
        for item in lad_density_cost:
            if item['geotype'] == geotype and item['strategy'] == strategy:
                density_cost.append({
                    'geotype': geotype,
                    'geotype_name': item['geotype_name'],
                    'strategy': strategy,
                    'cost': item['cost'],
                    'dwelling_density': sum(densities) / len(densities)
                })
                break
    return density_cost


def add_cost_to_oas(oa_dwelling_data, cost_density_lut):

    unique_strategies = set()

    for item in cost_density_lut:
        unique_strategies.add(item['strategy'])

    output = []

    for oa in oa_dwelling_data:
        for strategy in unique_strategies:
            dwelling_density = oa['dwelling_density']
            cost, debug = lookup_cost(dwelling_density, strategy, cost_density_lut)
            output.append({
                'scenario': oa['scenario'],
                'strategy': strategy,
                'oa11cd': oa['oa11cd'],
                'lad11cd': oa['lad11cd'],
                'lad11nm': oa['lad11nm'],
                'dwellings_oa__final': oa['dwellings_oa__final'],
                'geotype': int(oa['geotype']),
                'geotype_name': oa['geotype_name'],
                'dwelling_density': oa['dwelling_density'],
                'area_km2': float(oa['area_km2']),
                'cost_per_dwelling': cost,
                'total_cost': cost * int(oa['dwellings_oa__final']),
                'debug_cost_density': debug,
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

    density_costs = sorted(density_costs, key=lambda d: d[0])

    lowest_density, lowest_cost = density_costs[0]
    next_density, next_cost = density_costs[1]
    if dwelling_density < lowest_density:
        return interpolate(lowest_density, lowest_cost, next_density, next_cost, dwelling_density), "<{}".format(int(lowest_density))

    for a, b in pairwise(density_costs):
        lower_density, lower_cost = a
        upper_density, upper_cost = b
        if lower_density <= dwelling_density and dwelling_density < upper_density:
            return interpolate(lower_density, lower_cost, upper_density, upper_cost, dwelling_density), \
                "{}-{} ({}-{}) {}".format(int(lower_density), int(upper_density), int(lower_cost), int(upper_cost), int(dwelling_density))

    next_highest_density, next_highest_cost = density_costs[-2]
    highest_density, highest_cost = density_costs[-1]

    cost = interpolate(next_highest_density, next_highest_cost, highest_density, highest_cost, dwelling_density)
    return max(cost, COST_LOWER_BOUND), ">{}".format(highest_density)


def interpolate(x0, y0, x1, y1, x):
    """Linear interpolation between two values.
    """
    try:
        y = (y0 * (x1 - x) + y1 * (x - x0)) / (x1 - x0)
    except ZeroDivisionError as e:
        print(x1,x0)
        raise e
    return y


def csv_writer(data, directory, filename):
    """
    Write data to a CSV file path
    """
    # Create path
    if not os.path.exists(directory):
        os.makedirs(directory)

    fieldnames = list(data[0].keys())

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
    urban_rural_lut = lad_geotypes(read_data(path))
    csv_writer(urban_rural_lut, RESULTS, 'urban_rural_lut.csv')

    print('load dwelling data')
    path = os.path.join(DATA, 'processed','oa_dwellings.csv')
    oa_dwelling_data = processing_dwellings(read_data(path))

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
    cost_data = process_cost_data(read_data(path))

    print('add costs to lad lut')
    lad_dwelling_density_lut = add_costs_to_lad_lut(lad_dwelling_density_lut, cost_data)
    csv_writer(lad_dwelling_density_lut, RESULTS, 'lad_dwelling_density_lut.csv')

    cost_density_lut = cost_for_mean_density(lad_dwelling_density_lut)
    csv_writer(cost_density_lut, RESULTS, 'cost_density_lut.csv')

    print('add costs to oas lut')
    output = add_cost_to_oas(oa_dwelling_data, cost_density_lut)

    csv_writer(output, RESULTS, 'results.csv')
