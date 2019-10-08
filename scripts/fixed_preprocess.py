import os
import sys
import configparser
import csv
import fiona

from collections import defaultdict, OrderedDict

from shapely.geometry import shape, Polygon, MultiPolygon, mapping
from rtree import index

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_OUTPUT = os.path.join(BASE_PATH, 'intermediate')
DATA_INPUT = os.path.join(BASE_PATH, 'raw', 'd_shapes')


def read_exchange_areas(path):

    with fiona.open(path, 'r') as source:
        return [feature for feature in source]


def read_lad_areas(path):
    with fiona.open(path, 'r') as source:
        return [area for area in source]


def intersect_lad_areas_and_exchanges(exchanges, areas):

    exchange_to_lad_area_lut = defaultdict(list)

    idx = index.Index()
    [idx.insert(0, shape(exchange['geometry']).bounds, exchange) for exchange in exchanges]

    for area in areas:
        for n in idx.intersection((shape(area['geometry']).bounds), objects=True):
            area_shape = shape(area['geometry'])
            exchange_shape = shape(n.object['geometry'])
            if area_shape.intersects(exchange_shape):
                exchange_to_lad_area_lut[n.object['properties']['id']].append({
                    'lad': area['properties']['name'],
                    })

    return exchange_to_lad_area_lut


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


if __name__ == '__main__':

    path = os.path.join(DATA_INPUT, 'all_exchange_areas', '_exchange_areas_fixed.shp')
    exchange_areas = read_exchange_areas(path)

    path = os.path.join(DATA_INPUT, 'lad_uk_2016-12', 'lad_uk_2016-12.shp')
    lad_areas = read_lad_areas(path)

    lut = intersect_lad_areas_and_exchanges(exchange_areas, lad_areas)

    path = os.path.join(DATA_OUTPUT)
    csv_writer(lut, path, 'ex_to_lad_lut.csv')
