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
from pyproj import Proj, transform               
# from sklearn.cluster import KMeans #DBSCAN,
# from scipy.spatial import Voronoi, voronoi_plot_2d
from rtree import index
import tqdm

from collections import OrderedDict
import osmnx as ox 
import networkx as nx

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# setup file locations and data files
#####################################

DATA_RAW_INPUTS = os.path.join(BASE_PATH, 'raw', 'b_mobile_model')
DATA_FIXED_INPUTS = os.path.join(BASE_PATH, 'raw', 'a_fixed_model')
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
        return [lad for lad in lad_shape] #if 
        # lad['properties']['name'].startswith(
        #     ('E07000008', 'E07000012', 'E07000077')
        #     )]
    

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
        return [pcd for pcd in pcd_sector_shapes] #if pcd['properties']['postcode'].startswith('CB1')]


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
        for n in idx.intersection(
            (shape(postcode_sector['geometry']).bounds), objects=True):
            postcode_sector_shape = shape(postcode_sector['geometry'])
            lad_shape = shape(n.object['geometry'])
            if postcode_sector_shape.intersects(lad_shape):
                final_postcode_sectors.append({
                    'type': postcode_sector['type'],
                    'geometry': postcode_sector['geometry'],
                    'properties':{
                        'postcode': postcode_sector['properties']['postcode'],
                        'lad': n.object['properties']['name'],
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

    site_id = 0

    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        for line in reader:
            yield {
                'type': 'Feature',
                'geometry':{
                    'type': 'Point',
                    'coordinates': [float(line['longitude']), float(line['latitude'])]
                },
                'properties':{
                    'id': 'site_' + str(site_id), 
                    'Antennaht': line['Antennaht'],
                    'Transtype': line['Transtype'],
                    'Freqband': line['Freqband'],
                    'Anttype': line['Anttype'],
                    'Powerdbw': line['Powerdbw'],
                    'Maxpwrdbw': line['Maxpwrdbw'],
                    'Maxpwrdbm': line['Maxpwrdbm'],
                }
            }
            site_id += 1


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
                        'id': n.object['properties']['id'],
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


def read_exchanges():
    """
    Reads in exchanges from 'final_exchange_pcds.csv'.

    """
    path = os.path.join(
        DATA_FIXED_INPUTS, 'layer_2_exchanges', 'final_exchange_pcds.csv'
        )

    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        for line in reader:
            # if line['OLO'] == 'CLMON':
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


def read_exchange_areas():
    """
    Read exchange polygons

    """
    path = os.path.join(
        DATA_RAW_SHAPES, 'all_exchange_areas', '_exchange_areas_fixed.shp'
        )

    with fiona.open(path, 'r') as source:
        for area in source:
            #if area['properties']['id'].startswith('exchange_CLMON'):
            yield area


def select_routing_points(origin_points, dest_points, areas):

    idx = index.Index(
        (i, Point(dest_point['geometry']['coordinates']).bounds, dest_point)
        for i, dest_point in enumerate(dest_points)
        )
    
    for site in origin_points:

        nearest_exchange = list(idx.nearest(
                Point(site['geometry']['coordinates']).bounds,
                1, objects='raw'))[0]

        exchange_id = nearest_exchange['properties']['id']
        
        for exchange_area in areas:
            if exchange_area['properties']['id'] == exchange_id:
                yield site, nearest_exchange, exchange_area

def return_object_coordinates(object):

    if object['geometry']['type'] == 'Polygon':
        origin_geom = object['representative_point']
        x = origin_geom.x
        y = origin_geom.y
    elif object['geometry']['type'] == 'Point':
        x = object['geometry']['coordinates'][0]
        y = object['geometry']['coordinates'][1]
    else:
        print('non conforming geometry type {}'.format(object['geometry']['type']))

    return x, y

def generate_shortest_path(origin_points, dest_points, areas):
    """
    Calculate distance between each site (origin_points) and the
    nearest exchange (dest_points).
    
    """
    processed_sites = []
    links = []

    for site, exchange, exchange_area in select_routing_points(
        origin_points, dest_points, areas):

        ox.config(log_file=False, log_console=False, use_cache=True)
        
        projUTM = Proj(init='epsg:27700')
        projWGS84 = Proj(init='epsg:4326')

        east, north = transform(
            projUTM, projWGS84, shape(exchange_area['geometry']).bounds[2], 
            shape(exchange_area['geometry']).bounds[3]
            )
        
        west, south = transform(
            projUTM, projWGS84, shape(exchange_area['geometry']).bounds[0], 
            shape(exchange_area['geometry']).bounds[1]
            )
        
        G = ox.graph_from_bbox(
            north, south, east, west, network_type='all', 
            truncate_by_edge=True
            )
 
        origin_x, origin_y = return_object_coordinates(site)
        dest_x, dest_y = return_object_coordinates(exchange)

        # Find shortest path between the two
        point1_x, point1_y = transform(projUTM, projWGS84, origin_x, origin_y)
        point2_x, point2_y = transform(projUTM, projWGS84, dest_x, dest_y)

        # Find shortest path between the two
        point1 = (point1_y, point1_x)
        point2 = (point2_y, point2_x)

        # TODO improve by finding nearest edge, 
        # routing to/from node at either end
        origin_node = ox.get_nearest_node(G, point1)
        destination_node = ox.get_nearest_node(G, point2)

        try:
            if origin_node != destination_node:
                route = nx.shortest_path(
                    G, origin_node, destination_node, weight='length'
                    )

                # Retrieve route nodes and lookup geographical location
                routeline = []
                routeline.append((origin_x, origin_y))
                for node in route:
                    routeline.append((
                        transform(projWGS84, projUTM, 
                        G.nodes[node]['x'], G.nodes[node]['y'])
                        ))
                routeline.append((dest_x, dest_y))
                line = routeline
            else:
                line = [(origin_x, origin_y), (dest_x, dest_y)]
        except nx.exception.NetworkXNoPath:
            line = [(origin_x, origin_y), (dest_x, dest_y)]

        # Map to line
        processed_sites.append({
            'type': 'Feature',
            'geometry': site['geometry'],
            'properties':{
                'id': site['properties']['id'],
                'Antennaht': site['properties']['Antennaht'],
                'Transtype': site['properties']['Transtype'],
                'Freqband': site['properties']['Freqband'],
                'Anttype': site['properties']['Anttype'],
                'Powerdbw': site['properties']['Powerdbw'],
                'Maxpwrdbw': site['properties']['Maxpwrdbw'],
                'Maxpwrdbm': site['properties']['Maxpwrdbm'],
                '4G': site['properties']['lte'],
                'exchange': exchange['properties']['id'],
                'backhaul_length_m': LineString(line).length
                }
        })

        # Map to line
        links.append({
            'type': "Feature",
            'geometry': {
                "type": "LineString",
                "coordinates": line
            },
            'properties': {
                "site": site['properties']['id'],
                "exchange": exchange['properties']['id'],
                "length": LineString(line).length
            }
        })

    return links, processed_sites


def write_shapefile(data, folder_name, filename):

    # Translate props to Fiona sink schema
    prop_schema = []
    for name, value in data[0]['properties'].items():
        fiona_prop_type = next((fiona_type for fiona_type, python_type in 
        fiona.FIELD_TYPES_MAP.items() if python_type == type(value)), None)
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
    with fiona.open(os.path.join(directory, filename), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
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

    print('Reading exchanges')
    exchanges = read_exchanges()

    print('Reading exchange areas')
    exchange_areas = read_exchange_areas()

    print('Generating shortest path link')
    backhaul_links, processed_sites = generate_shortest_path(
        processed_sites, exchanges, exchange_areas
        )

    ### WRITE ALL OUTPUTS ###

    write_shapefile(
        processed_sites, 'sitefinder', 'final_processed_sites.shp'
        )   

    write_shapefile(
        backhaul_links, 'backhaul_routes', 'backhaul_routes.shp'
        )   

    print('Writing postcode sectors to intermediate shapes')
    write_shapefile(
        postcode_sectors, 'postcode_sectors', '_processed_postcode_sectors.shp'
        )   

