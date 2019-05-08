import os
import sys
import configparser
import csv
import fiona
# import numpy as np
# import glob
# import random

#import matplotlib.pyplot as plt
from shapely.geometry import shape, Point, LineString, Polygon, MultiPolygon, mapping, MultiPoint
from shapely.ops import unary_union, cascaded_union
from shapely.wkt import loads
from shapely.prepared import prep
# from pyproj import Proj, transform
# from sklearn.cluster import KMeans #DBSCAN,
# from scipy.spatial import Voronoi, voronoi_plot_2d
from rtree import index
import tqdm

# from collections import OrderedDict, defaultdict, Counter
# import osmnx as ox, networkx as nx, geopandas as gpd

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# setup file locations and data files
#####################################

DATA_RAW_INPUTS = os.path.join(BASE_PATH, 'raw', 'b_mobile_model')
DATA_RAW_SHAPES = os.path.join(BASE_PATH, 'raw', 'd_shapes')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')

#####################################
# READ MAIN DATA
#####################################

def read_lads():
    """
    Read in all lad shapes.

    """
    lad_shapes = os.path.join(
        DATA_RAW_SHAPES, 'lad_uk_2016-12', 'lad_uk_2016-12.shp'
        )

    with fiona.open(lad_shapes, 'r') as lad_shape:
        return [lad for lad in lad_shape if lad['properties']['name'].startswith('E07000008')]
    

def lad_lut(lads):
    """
    Yield lad IDs for use as a lookup.

    """
    for lad in lads:
        yield lad['properties']['name']


def load_geotype_lut(lad_id):

    directory = os.path.join(
        DATA_INTERMEDIATE, 'mobile_geotype_lut', lad_id 
    )

    path = os.path.join(directory, lad_id + '.csv')

    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        for line in reader:
            total_premises = (
                int(float(line['residential_count'])) + 
                int(float(line['non_residential_count']))
                )
            yield {
                'postcode_sector': line['postcode_sector'],
                'total_premises': total_premises,
                'area': float(line['area']),
                'premises_density': total_premises / float(line['area']),
            }

def read_postcode_sectors():
    """
    Read all postcode sector shapes. 

    """
    postcode_sector_shapes = os.path.join(
        DATA_RAW_SHAPES, 'postcode_sectors', '_postcode_sectors.shp'
        )
    
    with fiona.open(postcode_sector_shapes, 'r') as pcd_sector_shapes:  
        return [pcd for pcd in pcd_sector_shapes if 
            pcd['properties']['postcode'].startswith('CB1')
            ]


def add_lad_to_postcode_sector(postcode_sectors, lads):
    """
    Add the LAD indicator(s) to the relevant postcode sector.

    """

    final_postcode_sectors = []

    idx = index.Index(
        (i, shape(lad['geometry']).bounds, lad)
        for i, lad in enumerate(lads)
    )
    
    for postcode_sector in postcode_sectors:
        intersecting_lads = []
        for n in idx.intersection(
            (shape(postcode_sector['geometry']).bounds), objects=True):
            postcode_sector_shape = shape(postcode_sector['geometry'])
            lad_shape = shape(n.object['geometry'])
            if postcode_sector_shape.intersects(lad_shape):
                intersecting_lads.append(n.object['properties']['name'])
        postcode_sectors.append({
            'type': postcode_sector['type'],
            'geometry': postcode_sector['geometry'],
            'properties':{
                'postcode': postcode_sector['properties']['postcode'],
                'lad': intersecting_lads,
                'area': postcode_sector_shape.area,
                },
            })

    return final_postcode_sectors


def import_sitefinder_data():
    """
    Import sites dataset.

    """
    path = os.path.join(
        DATA_INTERMEDIATE, 'sitefinder', 'sitefinder_processed.csv'
        )

    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        for line in reader:
            yield {
                'type': 'Feature',
                'geometry':{
                    'type': 'Point',
                    'coordinates': [line['longitude'], line['latitude']]
                },
                'properties':{
                    'Antennaht': line['Antennaht'],
                    'Transtype': line['Transtype'],
                    'Freqband': line['Freqband'],
                    'Anttype': line['Anttype'],
                    'Powerdbw': line['Powerdbw'],
                    'Maxpwrdbw': line['Maxpwrdbw'],
                    'Maxpwrdbm': line['Maxpwrdbm'],
                }
            }


def load_coverage_data(lad_id):
    """
    Import Ofcom Connected Nations coverage data (2018).

    """
    path = os.path.join(
        DATA_RAW_INPUTS, 'ofcom_2018', '201809_mobile_laua_r02.csv'
        )

    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        for line in reader:
            if line['laua'] == lad_id:
                return {
                    'lad_id': line['laua'],
                    'lad_name': line['laua_name'],
                    '4G_geo_out_0': line['4G_geo_out_0'],
                    '4G_geo_out_1': line['4G_geo_out_1'],
                    '4G_geo_out_2': line['4G_geo_out_2'],
                    '4G_geo_out_3': line['4G_geo_out_3'],
                    '4G_geo_out_4': line['4G_geo_out_4'],
                }


def allocate_4G_coverage(postcode_sectors, lad_lut, geotype_lut):

    output = []

    for lad_id in lad_lut:
    
        sector_data = [s for s in load_geotype_lut(lad_id)] 

        total_area = sum([s['area'] for s in sector_data])
        
        coverage_data = load_coverage_data(lad_id)
        
        coverage_amount = float(coverage_data['4G_geo_out_4'])
        
        covered_area = total_area * (coverage_amount/100)
        
        ranked_postcode_sectors = sorted(sector_data, key=lambda x: x['area'])

        area_allocated = 0

        for postcode_sector in postcode_sectors:
            area = postcode_sector['properties']['area'] / 10e6
            total = area + area_allocated
            if total < covered_area:
                postcode_sector['properties']['lte'] = True
                area_allocated += area
            else:
                postcode_sector['properties']['lte'] = False
                break 
            output.append(postcode_sector)
            
    return output 


def add_coverage_to_sites(sitefinder_data, postcode_sectors):

    final_sites = []

    idx = index.Index(
        (i, shape(site['geometry']).bounds, site)
        for i, site in enumerate(sitefinder_data)
    )
    
    for postcode_sector in postcode_sectors:
        for n in idx.intersection(
            (shape(postcode_sector['geometry']).bounds), objects=True):
            postcode_sector_shape = shape(postcode_sector['geometry'])
            site_shape = shape(n.object['geometry'])
            if postcode_sector_shape.intersects(site_shape):
                final_sites.append({
                    'type': 'Feature',
                    'geometry': n.object['geometry'],
                    'properties':{
                        'Antennaht': n.object['properties']['Antennaht'],
                        'Transtype': n.object['properties']['Transtype'],
                        'Freqband': n.object['properties']['Freqband'],
                        'Anttype': n.object['properties']['Anttype'],
                        'Powerdbw': n.object['properties']['Powerdbw'],
                        'Maxpwrdbw': n.object['properties']['Maxpwrdbw'],
                        'Maxpwrdbm': n.object['properties']['Maxpwrdbm'],
                        '4G': n.object['properties']['lte']
                        }
                    })
    
    return final_sites


def read_exchanges(exchange_area):
    """
    Reads in exchanges from 'final_exchange_pcds.csv'.

    """
    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        for line in reader:
            yield {
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [float(line['E']), float(line['N'])]
                },
                'properties': {
                    'id': 'exchange_' + line['OLO'],
                    'Name': line['Name'],
                    'pcd': line['exchange_pcd'],
                }
            }


def write_shapefile(data, folder_name, filename):

    # Translate props to Fiona sink schema
    prop_schema = []
    for name, value in data[0]['properties'].items():
        fiona_prop_type = next((fiona_type for fiona_type, python_type in fiona.FIELD_TYPES_MAP.items() if python_type == type(value)), None)
        prop_schema.append((name, fiona_prop_type))

    sink_driver = 'ESRI Shapefile'
    sink_crs = {'init': 'epsg:27700'}
    sink_schema = {
        'geometry': data[0]['geometry']['type'],
        'properties': OrderedDict(prop_schema)
    }

    # Create path
    directory = os.path.join(DATA_INTERMEDIATE, folder_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    print(os.path.join(directory, filename))
    # Write all elements to output file
    with fiona.open(os.path.join(directory, filename), 'w', 
        driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        [sink.write(feature) for feature in data]


if __name__ == "__main__":

    print('Loading local authority district shapes')
    lads = read_lads()
    
    print('Loading lad lookup')
    lad_lut = lad_lut(lads)

    print('Loading postcode sector shapes')
    postcode_sectors = read_postcode_sectors()

    print('Adding lad IDs to postcode sectors')
    postcode_sectors = add_lad_to_postcode_sector(postcode_sectors, lads)

    print('Importing sitefinder data')
    sitefinder_data = import_sitefinder_data()

    print('Disaggregate 4G coverage to postcode sectors')
    postcode_sectors = allocate_4G_coverage(
        postcode_sectors, lad_lut, load_geotype_lut
        )
    
    print('Allocate 4G coverage to sites from postcode sectors')
    processed_sites = add_coverage_to_sites(sitefinder_data, postcode_sectors)

    print('Writing processed sites')
    write_shapefile(
        processed_sites, 'sitefinder', 'processed_sites.shp'
        )   

    #process sites to have C-RAN indicator

    #give 4g coverage id to sites

    #process sites to have C-RAN indicator

    # print('Writing postcode sectors to intermediate shapes')
    # write_shapefile(
    #     postcode_sectors, 'postcode_sectors', '_postcode_sectors.shp'
    #     )   

