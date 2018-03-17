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

######################################################################
# spatial join of exchange polygon attributes to all premises points
######################################################################

with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, "exchange_boundary_polygons_dissolved.shp"), "r") as n:

    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, "premises_points_data.shp"), "r") as s:

        # create a schema for the attributes
        outSchema =  deepcopy(s.schema)
        outSchema['properties'].update(n.schema['properties'])

        with fiona.open (os.path.join(SYSTEM_OUTPUT_FILENAME, "final_premises_with_all_attribute_data.shp"), "w", s.driver, outSchema, s.crs) as output:

            for premises in s:
                for exchange in n:
                    # check if point is in polygon and set attribute
                    if shape(premises['geometry']).within(shape(exchange['geometry'])):
                        premises['properties']['EX_ID'] = exchange['properties']['EX_ID']
                    # write out
                        output.write({
                            'properties': premises['properties'],
                            'geometry': premises['geometry']
                        })

end = time.time()
print('Script completed in: ' + str(round((end - start), 2)) + ' seconds.')
