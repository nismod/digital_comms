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

from collections import OrderedDict

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################
# setup file locations
#####################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'Digital Comms - Fixed broadband model', 'Data')
SYSTEM_INPUT_CAMBRIDGE = os.path.join(BASE_PATH, 'cambridge_shape_file_analysis', 'Data')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'Digital Comms - Fixed broadband model', 'initial_system')

#####################
# Premise to Cabinet links
#####################

with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'cabinets_points_data.shp'), 'r') as source:

    cabinets = np.empty([len(list(source)), 2])
    cabinet_lut = {}

    for idx, cabinet in enumerate(source):
        
        # Prepare voronoi lookup
        cabinets[idx] = cabinet['geometry']['coordinates']
        cabinet_lut[idx] = cabinet

with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'premises_points_data.shp'), 'r') as source:

    idx_premises = index.Index()
    premise_lut = {}
    for idx, premise in enumerate(source):

        # Prepare rtree lookup
        idx_premises.insert(idx, premise['geometry']['coordinates'])  
        premise_lut[idx] = premise

vor = Voronoi(cabinets)

# # Write voronoi polygons
# schema = {
#     'geometry': 'Polygon',
#     'properties': OrderedDict([('Name', 'str:254')])
# }

# sink_driver = 'ESRI Shapefile'
# sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

# with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'cabinets_points_voronoi.shp'), 'w', driver=sink_driver, crs=sink_crs, schema=schema) as sink:
#     for region in vor.regions:

#         polygon = [vor.vertices[i] for i in region]

#         if len(polygon) > 0:
#             polygon.append(polygon[0])

#             geom = Polygon(polygon)

#             sink.write({
#                 'geometry': mapping(geom),
#                 'properties': OrderedDict([('Name', 'cab_1')])
# })

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

                    if cabinet_lut[idx]['properties']['SAU_NODE_I'] == '{EMCHATT}{P3}':
                        print('here je os')

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
                                    ('Origin', cabinet_lut[idx]['properties']['SAU_NODE_I']), 
                                    ('Dest', premise_lut[premise]['properties']['id'])
                                ]
                            )
                        )
                    )

# Write voronoi polygons
schema = {
    'geometry': 'LineString',
    'properties': OrderedDict([('Origin', 'str:254'), ('Dest', 'str:254')])
}

sink_driver = 'ESRI Shapefile'
sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'cabinets_premises_links.shp'), 'w', driver=sink_driver, crs=sink_crs, schema=schema) as sink:
    for link in links:

        sink.write({
            'geometry': mapping(link[0]),
            'properties': link[1]
})



        

        