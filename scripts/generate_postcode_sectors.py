import os
import configparser
import csv
import fiona

from rtree import index
from shapely.geometry import shape, Point, LineString, Polygon, MultiPolygon, mapping
from shapely.ops import unary_union

import itertools
from operator import itemgetter
from collections import OrderedDict

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# SETUP FILE LOCATIONS
#####################################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'raw', 'codepoint')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'raw', 'codepoint')

#####################################
# IMPORT CODEPOINT SHAPES
#####################################

def import_postcodes():

    my_postcode_data = []

    POSTCODE_DATA_DIRECTORY = os.path.join(SYSTEM_INPUT_FIXED,'codepoint-poly_2429451')

    # Initialze Rtree
    idx = index.Index()

    for dirpath, subdirs, files in os.walk(POSTCODE_DATA_DIRECTORY):
        for x in files:
            if x.endswith(".shp"):
                with fiona.open(os.path.join(dirpath, x), 'r') as source:

                    # Store shapes in Rtree
                    for src_shape in source:
                        idx.insert(int(src_shape['id']), shape(src_shape['geometry']).bounds, src_shape)

                    # Split list in regular and vertical postcodes
                    postcodes = {}
                    vertical_postcodes = {}

                    for x in source:

                        x['properties']['POSTCODE'] = x['properties']['POSTCODE'].replace(" ", "")
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
                            'id': neighbour['id'].replace(" ", ""),
                            'properties': neighbour['properties'],
                            'geometry': mapping(merged_geom)
                        }

                        try:
                            postcodes[merged_postcode['id']] = merged_postcode
                        except:
                            raise Exception

                    for key, p in postcodes.items():
                        p.pop('id')
                        my_postcode_data.append(p)

    return my_postcode_data

def add_postcode_sector_indicator(data):

    my_postcode_data = []

    for x in data:
        x['properties']['pcd_sector'] = x['properties']['POSTCODE'][:-2]
        my_postcode_data.append(x)

    return my_postcode_data


def write_shapefile(data, path):

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

    # Write all elements to output file
    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, path), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        for feature in data:
            sink.write(feature)


def dissolve(input, output, fields):
    with fiona.open(os.path.join(SYSTEM_INPUT_FIXED, input)) as input:
        with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, output), 'w', **input.meta) as output:
            grouper = itemgetter(*fields)
            key = lambda k: grouper(k['properties'])
            for k, group in itertools.groupby(sorted(input, key=key), key):
                properties, geom = zip(*[(feature['properties'], shape(feature['geometry'])) for feature in group])
                output.write({'geometry': mapping(unary_union(geom)), 'properties': properties[0]})

#####################################
# EXECUTE FUNCTIONS
#####################################

print("importing codepoint postcode data")
postcodes = import_postcodes()

print("adding pcd_sector indicator")
postcodes = add_postcode_sector_indicator(postcodes)

print("writing postcodes")
write_shapefile(postcodes, 'postcodes.shp')

print("dissolving on pcd_sector indicator")
dissolve('postcodes.shp', 'postcode_sectors.shp', ["pcd_sector"])

print("script finished")



