import os
import sys
import configparser
import csv
import glob

import fiona
from rtree import index
from shapely.geometry import shape, Point, Polygon, MultiPoint, mapping

CONFIG = configparser.ConfigParser()
CONFIG.read(
    os.path.join(os.path.dirname(__file__), 'script_config.ini')
)
BASE_PATH = CONFIG['file_locations']['base_path']

#data locations
DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_RESULTS = os.path.join(BASE_PATH, 'intermediate')

def get_postcode_sectors():

    all_postcode_sectors = []

    directory = os.path.join(DATA_RAW, 'd_shapes', 'postcode_sectors')
    pathlist = glob.iglob(directory + '/*.shp', recursive=True)
    for path in pathlist:
        with fiona.open(path, 'r') as source:
            for sector in source:
                all_postcode_sectors.append(sector)

    return all_postcode_sectors

def get_local_authority_districts():

    all_lads = []

    with fiona.open(os.path.join(
        DATA_RAW, 'd_shapes','lad_uk_2016-12', 'lad_uk_2016-12.shp'), 'r') as source:
        for lad in source:
            all_lads.append(lad)

    return all_lads

def intersect_boundaries(postcode_sectors, lads):

    pcd_sector_to_lad_lut = []

    # Initialze Rtree
    idx = index.Index()

    for rtree_idx, postcode_sector in enumerate(postcode_sectors):
        idx.insert(rtree_idx, shape(postcode_sector['geometry']).bounds, postcode_sector)

    # Join the two
    for lad in lads:
        lad_name = lad['properties']['name']
        for n in idx.intersection((shape(lad['geometry']).bounds), objects='raw'):
            pcd_sector_name = n['properties']['postcode']
            lad_shape = shape(lad['geometry'])
            pcd_sector_shape = shape(n['geometry'])
            if lad_shape.intersects(pcd_sector_shape):
                pcd_sector_to_lad_lut.append(
                    (pcd_sector_name, lad_name)
                    )

    unique_entries = list(set([tuple(sorted(t)) for t in pcd_sector_to_lad_lut]))

    return unique_entries

def csv_writer(data_for_writing, filename):
    """
    Write data to a CSV file path

    """
    #create path
    directory = os.path.join(BASE_PATH, 'intermediate', 'pcd_sector_to_lad_lut')
    if not os.path.exists(directory):
        os.makedirs(directory)

    path = os.path.join(directory, filename)

    if not os.path.exists(path):
        lut_file = open(path, 'w', newline='')
        lut_writer = csv.writer(lut_file)
        lut_writer.writerow(
            ('postcode_sector', 'lad'))

    else:
        lut_file = open(path, 'a', newline='')
        lut_writer = csv.writer(lut_file)

    # output and report results for this timestep
    for datum in data_for_writing:
        print(datum)
        lut_writer.writerow(
            (datum[0],
            datum[1])
            )

    lut_file.close()

#####################################
# APPLY METHODS
#####################################

if __name__ == "__main__":

    postcode_sectors = get_postcode_sectors()

    postcode_sectors = postcode_sectors

    lads = get_local_authority_districts()

    lut = intersect_boundaries(postcode_sectors, lads)

    csv_writer(lut, 'pcd_sector_to_lad_lut.csv')
