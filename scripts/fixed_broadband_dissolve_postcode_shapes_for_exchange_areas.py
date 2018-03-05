from collections import OrderedDict

import fiona
from shapely.geometry import MultiPolygon, Polygon
from shapely.geometry import shape, mapping
from shapely.ops import unary_union, cascaded_union

import os
import csv
import time
import configparser
import itertools

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################
# setup file locations
#####################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'processed')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'processed')

# Initialize timer
start = time.time()

#with fiona.open(os.path.join(SYSTEM_INPUT_FIXED, 'exchange_boundary_polygons.shp'), 'r') as source:

#     # Write exchange polygons
#     sink_schema = {}
#     sink_schema['geometry'] = 'MultiPolygon'
#     sink_schema['properties'] = OrderedDict()
#     sink_schema['properties']['EX_ID'] = 'str:8'

#     with fiona.open(
#         os.path.join(SYSTEM_OUTPUT_FILENAME, 'exchange_boundary_polygons_dissolved.shp'),
#         'w',
#         crs=source.crs,
#         driver=source.driver,
#         schema=sink_schema,
#         ) as sink:

#         exchange_areas = {}

#         # Loop through all exchanges
#         for f in source:

#             # Convert Multipolygons to list of polygons
#             if (isinstance(shape(f['geometry']), MultiPolygon)):
#                 polygons = [p.buffer(0) for p in shape(f['geometry'])]
#             else:
#                 polygons = [shape(f['geometry'])]

#             # Extend list of geometries, create key (exchange_id) if non existing
#             try:
#                 exchange_areas[f['properties']['EX_ID']].extend(polygons)
#             except:
#                 exchange_areas[f['properties']['EX_ID']] = []
#                 exchange_areas[f['properties']['EX_ID']].extend(polygons)

#         # Write Multipolygons per exchange
#         for exchange, area in exchange_areas.items():

#             exchange_multipolygon = MultiPolygon(area)

#             s = {}
#             s['geometry'] = mapping(exchange_multipolygon)
#             s['properties'] = OrderedDict()
#             s['properties']['EX_ID'] = exchange

#             sink.write(s)

with fiona.open(os.path.join(SYSTEM_INPUT_FIXED, 'exchange_boundary_polygons.shp'), 'r') as source:
    # preserve the schema of the original shapefile, including the crs
    
    # Write exchange polygons
    sink_schema = {}
    sink_schema['geometry'] = 'Polygon'
    sink_schema['properties'] = OrderedDict()
    sink_schema['properties']['EX_ID'] = 'str:8' 

    with fiona.open(
        os.path.join(SYSTEM_OUTPUT_FILENAME, 'exchange_boundary_polygons_dissolved.shp'),
        'w',
        crs=source.crs,
        driver=source.driver,
        schema=sink_schema,
        ) as sink:

        for f in source:

            # Avoid intersections
            geom = shape(f['geometry']).buffer(0)
            cascaded_geom = unary_union(geom)

            # Remove islands
            if (isinstance(cascaded_geom, MultiPolygon)):
                for idx, p in enumerate(cascaded_geom):
                    if idx == 0:
                        geom = p
                    elif p.area > geom.area:
                        geom = p
            else:
                geom = cascaded_geom

            # Write exterior to file as polygon
            exterior = Polygon(list(geom.exterior.coords))

            # # Generate convey hull
            # exterior = exterior.convex_hull

            # Write to output
            s = {}
            s['geometry'] = mapping(exterior)
            s['properties'] = OrderedDict()
            s['properties']['EX_ID'] = f['properties']['EX_ID']

            sink.write(s)

end = time.time()
print('Script completed in: ' + str(round((end - start), 2)) + ' seconds.')
