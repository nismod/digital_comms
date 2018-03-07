import os
import fiona
import configparser
import time

from shapely.geometry import shape, mapping
from shapely.ops import unary_union
from rtree import index
from pprint import pprint

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

SYSTEM_INPUT = os.path.join(BASE_PATH, 'raw', 'postcode_shapes')
SYSTEM_OUTPUT = os.path.join(BASE_PATH, 'processed')

start = time.time()

# Initialze Rtree
idx = index.Index()

with fiona.open(os.path.join(SYSTEM_INPUT, 'cb.shp'), 'r') as source:

    sink_schema = source.schema.copy()

    # Store shapes in Rtree
    for src_shape in source:
        idx.insert(int(src_shape['id']), shape(src_shape['geometry']).bounds, src_shape)

    # Open output file
    with fiona.open(
            os.path.join(SYSTEM_OUTPUT, 'pcd_shapes_no_verticals.shp'), 'w',
            crs=source.crs,
            driver=source.driver,
            schema=sink_schema,
            ) as sink:

        print(sink_schema)

        # Split list in regular and vertical postcodes
        postcodes = {}
        vertical_postcodes = {}

        for x in source:

            if x['properties']['POSTCODE'].startswith('V'):
                vertical_postcodes[x['id']] = x
            else:
                postcodes[x['id']] = x

        for key, f in vertical_postcodes.items():

            vpost_geom = shape(f['geometry'])
            best_neighbour = {'id': 0, 'intersection': 0}

            # Find best neighbour
            for n in idx.intersection((vpost_geom.bounds), objects=True):
                if shape(n.object['geometry']).intersection(vpost_geom).length > best_neighbour['intersection'] and n.object['id'] != f['id']:
                    best_neighbour['id'] = n.object['id']
                    best_neighbour['intersection'] = shape(n.object['geometry']).intersection(vpost_geom).length

            # Merge with best neighbour
            neighbour = postcodes[best_neighbour['id']]
            merged_geom = unary_union([shape(neighbour['geometry']), vpost_geom])

            merged_postcode = {
                'id': neighbour['id'],
                'properties': neighbour['properties'],
                'geometry': mapping(merged_geom)
            }

            try:
                postcodes[merged_postcode['id']] = merged_postcode
            except:
                print('print(f)')
                print(f)
                print('print(neighbour)')
                print(neighbour)
                print('print(merged_postcode)')
                print(merged_postcode)
                raise Exception

        for key, p in postcodes.items():
            sink.write(p)

end = time.time()
print('Script completed in: ' + str(round((end - start), 2)) + ' seconds.')
