import fiona
import csv
import os
import time
import configparser

from rtree import index
from shapely.geometry import Point, shape

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################
# setup file locations
#####################

#SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'processed')
#SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'processed')

#####################
#
#####################

start = time.time()

idx_pcb2cab = index.Index()
lut_pcb2cab = {}
idx_cb = index.Index()
lut_exchanges = {}
idx_exchanges = index.Index()

with fiona.open(os.path.join(BASE_PATH, 'processed', 'pcd_shapes_no_verticals.shp'), 'r') as source:

    # Read the exchange points
    with open(os.path.join(BASE_PATH, 'raw', 'layer_2_exchanges', 'final_exchange_pcds.csv'), 'r') as f:
        reader = csv.reader(f)
        next(reader) # Header['exchange', 'OLO', 'Name', 'Region', 'County', 'E', 'N']

        i = 0
        exchange = {}

        for row in reader:

            # Map and pre-process Csv data
            exchange['id'] = i
            exchange['pcd'] = row[0]
            exchange['OLO'] = row[1]
            exchange['Name'] = row[2]
            exchange['Region'] = row[3]
            exchange['County'] = row[4]
            exchange['E'] = float(row[5])
            exchange['N'] = float(row[6])

            # Add to Rtree and lookup table
            idx_exchanges.insert(i, (exchange['E'],exchange['N'], exchange['E'], exchange['N']), exchange['OLO'])
            lut_exchanges[exchange['OLO']] = {
                'Name': exchange['Name'],
                'pcd': exchange['pcd'],
                'Region': exchange['Region'],
                'County': exchange['County'],
                'E': exchange['E'],
                'N': exchange['N']
            }

            i+=1

    # Read the postcode-to-cabinet-to-exchange lookup file into Rtree
    with open(os.path.join(BASE_PATH, 'processed', 'pcd_to_exchange_data.csv'), 'r') as f:
        reader = csv.reader(f)
        next(reader) # Header['OLO', 'pcd', 'SAU_NODE_ID', 'easting', 'northing']

        i = 0
        pcd = {}

        for row in reader:

            # Map and pre-process Csv data
            pcd['id'] = i
            pcd['OLO'] = row[0]
            pcd['postcode'] = row[1]

            # Add to Rtree and lookup table
            lut_pcb2cab[pcd['postcode']] = pcd['OLO']

            i+=1

    # Copy the source schema and add property that holds the exchange OLO_ID
    sink_schema = source.schema.copy()
    sink_schema['properties']['EX_ID'] = 'str:8'
    sink_schema['properties']['EX_NAME'] = 'str:8'
    sink_schema['properties']['EX_PCD'] = 'str:8'
    sink_schema['properties']['EX_REGION'] = 'str:8'
    sink_schema['properties']['EX_COUNTY'] = 'str:8'
    sink_schema['properties']['EX_EASTING'] = 'float'
    sink_schema['properties']['EX_NORTHING'] = 'float'
    sink_schema['properties']['EX_SRC'] = 'str:8'

    # Open output file
    sink = fiona.open(os.path.join(BASE_PATH, 'processed', 'exchange_areas.shp'), 'w', crs=source.crs, driver=source.driver, schema=sink_schema)

    # Connect each postcode area to an exchange
    for postcode_area in source:

        f = postcode_area
        postcode = postcode_area['properties']['POSTCODE'].replace(" ", "")

        if postcode in lut_pcb2cab:

            # Postcode-to-cabinet-to-exchange association
            f['properties']['EX_ID'] = lut_pcb2cab[postcode]
            f['properties']['EX_SRC'] = 'EXISTING POSTCODE DATA'

        else:

            # Find nearest exchange
            nearest = [n.object for n in idx_exchanges.nearest((shape(f['geometry']).bounds), 1, objects=True)]
            f['properties']['EX_ID'] = nearest[0]
            f['properties']['EX_SRC'] = 'ESTIMATED NEAREST'

        # Match the exchange ID with remaining exchange info
        if f['properties']['EX_ID'] in lut_exchanges:
            f['properties']['EX_NAME'] = lut_exchanges[f['properties']['EX_ID']]['Name']
            f['properties']['EX_PCD'] = lut_exchanges[f['properties']['EX_ID']]['pcd']
            f['properties']['EX_REGION'] = lut_exchanges[f['properties']['EX_ID']]['Region']
            f['properties']['EX_COUNTY'] = lut_exchanges[f['properties']['EX_ID']]['County']
            f['properties']['EX_EASTING'] = lut_exchanges[f['properties']['EX_ID']]['E']
            f['properties']['EX_NORTHING'] = lut_exchanges[f['properties']['EX_ID']]['N']
        else:
            f['properties']['EX_NAME'] = ""
            f['properties']['EX_PCD'] = ""
            f['properties']['EX_REGION'] = ""
            f['properties']['EX_COUNTY'] = ""
            f['properties']['EX_EASTING'] = ""
            f['properties']['EX_NORTHING'] = ""
        # Write to file
        sink.write(f)



end = time.time()
print('Script completed in: ' + str(round((end - start), 2)) + ' seconds.')
