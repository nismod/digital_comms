import fiona
from shapely.geometry import shape, mapping
from copy import deepcopy

import os
import time
import configparser

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################
# setup file locations
#####################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'raw', 'postcode_shapes')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'processed')

# Initialize timer
start = time.time()

#####################
# find representative points from postcode polygons
#####################

with fiona.open(os.path.join(SYSTEM_INPUT_FIXED, 'cb.shp'), 'r') as source:
    # preserve the schema of the original shapefile, including the crs
    meta = source.meta
    meta['schema']['geometry'] = 'Point'
    # Write exchange polygons
    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'postcode_polygon_centroids.shp'), 'w', **meta) as sink:

        for f in source:

            centroid = shape(f['geometry']).representative_point()

            f['geometry'] = mapping(centroid)

            sink.write(f)

#####################
# spatial join of polygon attributes to all points within that polygon
#####################

with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, "exchange_boundary_polygons_dissolved.shp"), "r") as n:

    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, "postcode_polygon_centroids.shp"), "r") as s:

        # create a schema for the attributes
        outSchema =  deepcopy(s.schema)
        outSchema['properties'].update(n.schema['properties'])

        with fiona.open (os.path.join(SYSTEM_OUTPUT_FILENAME, "postcode_points_with_exchange_area_id.shp"), "w", s.driver, outSchema, s.crs) as output:

            for postcode in s:
                for exchange in n:
                    # check if point is in polygon and set attribute
                    if shape(postcode['geometry']).within(shape(exchange['geometry'])):
                        postcode['properties']['EX_ID'] = exchange['properties']['EX_ID']
                    # write out
                        output.write({
                            'properties': postcode['properties'],
                            'geometry': postcode['geometry']
                        })

end = time.time()
print('Script completed in: ' + str(round((end - start), 2)) + ' seconds.')
