import fiona
import os
import configparser

from shapely.geometry import Point, LineString, mapping
from collections import OrderedDict

#####################
# generate dummy data
#####################

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

# Config
input_shapefiles_dir = 'processed'

# Helper functions
def write_points_to_shp(filename, data, schema):
    sink_driver = 'ESRI Shapefile'
    sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

    with fiona.open(filename, 'w', driver=sink_driver, crs=sink_crs, schema=schema) as sink:
        for geom in data:
            if schema['geometry'] == 'Point':
                sink.write({
                    'geometry': mapping(geom[0]),
                    'properties': geom[1]
                })
            elif schema['geometry'] == 'LineString':
                sink.write({
                    'geometry': mapping(geom[0]),
                    'properties': geom[1]
                })

def write_links_to_shp(filename, data):
    sink_driver = 'ESRI Shapefile'
    sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

    setup_linestring_schema = {
        'geometry': 'LineString',
        'properties': OrderedDict([('From', 'str:254'), ('To', 'str:254')])
    }

    with fiona.open(filename, 'w', driver=sink_driver, crs=sink_crs, schema=setup_linestring_schema) as sink:
        for link in data:
            sink.write({
                'geometry': mapping(link[0]),
                'properties': link[1]
            })

# Create shapefiles
setup_fixed_model_pcp_schema = {
    'geometry': 'Point',
    'properties': OrderedDict([('Name', 'str:254'), ('Type', 'str:254')])
}

setup_fixed_model_pcp = [
    (Point(-1.944580, 52.792175), OrderedDict([('Name', 'cab_1'), ('Type', 'pcp')])),
    (Point(-0.395508, 52.485498), OrderedDict([('Name', 'cab_2'), ('Type', 'pcp')])),
    (Point(-2.713623, 52.652437), OrderedDict([('Name', 'cab_3'), ('Type', 'pcp')])),
    (Point( 0.417480, 51.147694), OrderedDict([('Name', 'cab_4'), ('Type', 'pcp')])),
    (Point( 1.219482, 52.431944), OrderedDict([('Name', 'cab_5'), ('Type', 'pcp')])),
    (Point(-1.900635, 51.223443), OrderedDict([('Name', 'cab_6'), ('Type', 'pcp')])),
    (Point( 0.802002, 51.154586), OrderedDict([('Name', 'cab_7'), ('Type', 'pcp')]))
]

setup_fixed_model_exchanges_schema = {
    'geometry': 'Point',
    'properties': OrderedDict([('Name', 'str:254'), ('Type', 'str:254')])
}

setup_fixed_model_exchanges = [
    (Point(-0.572275, 51.704581), OrderedDict([('Name', 'EAARR'), ('Type', 'exchange')])),
    (Point( 0.537344, 51.745323), OrderedDict([('Name', 'EABTM'), ('Type', 'exchange')]))
]

setup_fixed_model_corenodes_schema = {
    'geometry': 'Point',
    'properties': OrderedDict([('Name', 'str:254'), ('Type', 'str:254')])
}

setup_fixed_model_corenodes = [
    (Point(0.3, 51.825323), OrderedDict([('Name', 'CoreNode'), ('Type', 'core')]))
]

setup_fixed_model_links_schema = {
    'geometry': 'LineString',
    'properties': OrderedDict([('Origin', 'str:254'), ('Dest', 'str:254'), ('Type', 'str:254'), ('Physical', 'str:254')])
}

setup_fixed_model_links = [
    (LineString([(-0.572275, 51.704581), (0, 52), (-1.944580, 52.792175)]), OrderedDict([('Origin', 'EAARR'),    ('Dest', 'cab_1'), ('Type', 'link'), ('Physical', 'fiberglass')])),
    (LineString([(-0.572275, 51.704581), (0, 52), (-0.395508, 52.485498)]), OrderedDict([('Origin', 'EAARR'),    ('Dest', 'cab_2'), ('Type', 'link'), ('Physical', 'fiberglass')])),
    (LineString([(-0.572275, 51.704581), (0, 52), (-2.713623, 52.652437)]), OrderedDict([('Origin', 'EAARR'),    ('Dest', 'cab_3'), ('Type', 'link'), ('Physical', 'fiberglass')])),
    (LineString([(-0.572275, 51.704581), (0, 52), ( 0.417480, 51.147694)]), OrderedDict([('Origin', 'EAARR'),    ('Dest', 'cab_4'), ('Type', 'link'), ('Physical', 'fiberglass')])),
    (LineString([( 0.537344, 51.745323), (0, 52), ( 1.219482, 52.431944)]), OrderedDict([('Origin', 'EABTM'),    ('Dest', 'cab_5'), ('Type', 'link'), ('Physical', 'copper')    ])),
    (LineString([( 0.537344, 51.745323), (0, 52), (-1.900635, 51.223443)]), OrderedDict([('Origin', 'EABTM'),    ('Dest', 'cab_6'), ('Type', 'link'), ('Physical', 'copper')    ])),
    (LineString([( 0.537344, 51.745323), (0, 52), ( 0.802002, 51.154586)]), OrderedDict([('Origin', 'EABTM'),    ('Dest', 'cab_7'), ('Type', 'link'), ('Physical', 'copper')    ])),
    (LineString([( 0.3,      51.825323), (0, 51), (-0.572275, 51.704581)]), OrderedDict([('Origin', 'CoreNode'), ('Dest', 'EAARR'), ('Type', 'link'), ('Physical', 'copper')    ])),
    (LineString([( 0.3,      51.825323), (0, 51), ( 0.537344, 51.745323)]), OrderedDict([('Origin', 'CoreNode'), ('Dest', 'EABTM'), ('Type', 'link'), ('Physical', 'copper')    ]))
]

write_points_to_shp(os.path.join(BASE_PATH, input_shapefiles_dir, 'fixed_model_pcp.shp'), setup_fixed_model_pcp, setup_fixed_model_pcp_schema)
write_points_to_shp(os.path.join(BASE_PATH, input_shapefiles_dir, 'fixed_model_exchanges.shp'), setup_fixed_model_exchanges, setup_fixed_model_exchanges_schema)
write_points_to_shp(os.path.join(BASE_PATH, input_shapefiles_dir, 'fixed_model_corenodes.shp'), setup_fixed_model_corenodes, setup_fixed_model_corenodes_schema)
write_points_to_shp(os.path.join(BASE_PATH, input_shapefiles_dir, 'fixed_model_links.shp'), setup_fixed_model_links, setup_fixed_model_links_schema)

print('Done... Files are generated')