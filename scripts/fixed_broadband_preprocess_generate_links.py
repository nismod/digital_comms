import os
from pprint import pprint
import configparser
import csv
import fiona
from shapely.geometry import Point, mapping, LineString, Polygon
from pyproj import Proj, transform
import numpy as np
from scipy.spatial import Voronoi, voronoi_plot_2d
from rtree import index
import matplotlib.mlab as mlab
import matplotlib.pyplot as plt

from collections import OrderedDict

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################
# setup file locations
#####################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'Digital Comms - Fixed broadband model', 'Data')
SYSTEM_INPUT_CAMBRIDGE = os.path.join(BASE_PATH, 'cambridge_shape_file_analysis', 'Data')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, '../input_shapefiles')

def open_premises_shapefile():
    return fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'premises_points_data.shp'), 'r')

def open_cabinets_shapefile():
    return fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'cabinets_points_data.shp'), 'r')

def open_pcps_shapefile():
    return fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'pcps_points_data.shp'), 'r')

def calculate_links(premise_source, cabinet_source):

    # Prepare premises lookup
    idx_premises = index.Index()
    premise_lut = {}
    for idx, premise in enumerate(premise_source):
        idx_premises.insert(idx, premise['geometry']['coordinates'])  
        premise_lut[idx] = premise

    # Prepare voronoi cabinet lookup 
    cabinets = np.empty([len(list(cabinet_source)), 2])
    cabinet_lut = {}
    for idx, cabinet in enumerate(cabinet_source):
        cabinets[idx] = cabinet['geometry']['coordinates']
        cabinet_lut[idx] = cabinet

    # Generate voronoi
    vor = Voronoi(cabinets)

    # Write voronoi polygons
    schema = {
        'geometry': 'Polygon',
        'properties': OrderedDict([('Name', 'str:254')])
    }

    sink_driver = 'ESRI Shapefile'
    sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'cabinets_points_voronoi.shp'), 'w', driver=sink_driver, crs=sink_crs, schema=schema) as sink:
        for region in vor.regions:

            polygon = [vor.vertices[i] for i in region]

            if len(polygon) > 0:
                polygon.append(polygon[0])

                geom = Polygon(polygon)

                sink.write({
                    'geometry': mapping(geom),
                    'properties': OrderedDict([('Name', 'cab_1')])
    })

    # Find links
    links = []

    for idx, cab in enumerate(vor.point_region):

        polygon = [vor.vertices[i] for i in vor.regions[cab]]
        if len(polygon) > 0:
            geom = Polygon(polygon)
            bounds = geom.bounds
            premises_candidates = list(idx_premises.intersection(bounds))
            
            if len(premises_candidates) < 1000: #Avoid processing weird polygons'
                
                for premise in premises_candidates:
            
                    if Point(premise_lut[premise]['geometry']['coordinates']).within(geom):

                        links.append(
                            (
                                LineString(
                                    [
                                        cabinet_lut[idx]['geometry']['coordinates'], 
                                        premise_lut[premise]['geometry']['coordinates']
                                    ]
                                ), 
                                OrderedDict(
                                    [
                                        ('Origin', cabinet_lut[idx]['properties']['Name']), 
                                        ('Dest', premise_lut[premise]['properties']['Name'])
                                    ]
                                )
                            )
                        )
    return links

def analyse_number_of_links_per_node(links):

    origins = np.array([link[1]['Origin'] for link in links])
    unique, counts = np.unique(origins, return_counts=True)
    nodes = dict(zip(unique, counts))

    plt.hist(counts, bins=list(range(0, 20, 1)))
    plt.axis([0, 20, 0, 100])
    plt.ylabel('Number of links per node')

    # # the histogram of the data
    # plt.hist(origins, bins=20)

    plt.show()


def write_links(links, filename):

    schema = {
        'geometry': 'LineString',
        'properties': OrderedDict([('Origin', 'str:254'), ('Dest', 'str:254')])
    }

    sink_driver = 'ESRI Shapefile'
    sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, filename), 'w', driver=sink_driver, crs=sink_crs, schema=schema) as sink:
        for link in links:

            sink.write({
                'geometry': mapping(link[0]),
                'properties': link[1]
    })


if __name__ == "__main__":
    
    prems = open_premises_shapefile()
    cabs = open_cabinets_shapefile()
    pcps = open_pcps_shapefile()
    
    # prem_to_cab_links = calculate_links(prems, cabs)
    cab_to_pcp_links = calculate_links(cabs, pcps)

    analyse_number_of_links_per_node(cab_to_pcp_links)

    # write_links(prem_to_cab_links, 'premises_cabinets_links.shp')
    write_links(cab_to_pcp_links, 'cabinets_pcps_links.shp')

        