import configparser
import os
import glob
import csv
from math import sqrt, pi, sin, cos, tan, atan2 as arctan2
from pyproj import Proj, transform
import fiona
from shapely.geometry import Point, LineString, shape
from osgeo import gdal
from collections import OrderedDict

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), '..',  '..', 'scripts','script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#data locations
DATA_RAW_INPUTS = os.path.join(BASE_PATH, 'raw', 'e_dem_and_buildings')
DATA_RAW_SHAPES = os.path.join(BASE_PATH, 'raw', 'd_shapes')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')

def find_line_of_sight(x1, y1, x2, y2):

    x_coordinates = []
    y_coordinates = []

    x_coordinates.append(x1)
    x_coordinates.append(x2)
    y_coordinates.append(y1)
    y_coordinates.append(y2)

    x_min = min(x_coordinates)
    x_max = max(x_coordinates) 
    y_min = min(y_coordinates)
    y_max = max(y_coordinates)

    projOSGB36 = Proj(init='epsg:27700')
    projWGS84 = Proj(init='epsg:4326')

    x_min, y_min = transform(projWGS84, projOSGB36, x_min, y_min)
    x_max, y_max = transform(projWGS84, projOSGB36, x_max, y_max)
    
    premises_data = read_premises_data(x_min, y_min, x_max, y_max)

    if len(premises_data) < 1:
        line_of_sight = 'los'
    else:
        tile_ids = find_osbg_tile(x_min, y_min, x_max, y_max)
        
        building_heights = []

        for tile_id in tile_ids:
            pathlist = glob.iglob(os.path.join(DATA_RAW_INPUTS,'mastermap_building_heights_2726794',
            tile_id['tile_ref_2_digit'] + '/*.csv'))
            for path in pathlist:
                if path[-10:-6] == tile_id['tile_ref_4_digit'].lower(): 
                    with open(path, 'r') as system_file:
                        reader = csv.reader(system_file)
                        next(reader)
                        for line in reader:
                            building_heights.append({
                                'id': line[0],
                                'max_height': line[6],
                            })
                else:
                    pass
        
        premises_with_heights = []

        for premises in premises_data:
            for building_height in building_heights:
                if premises['properties']['uid'] == building_height['id']:     
                    premises_with_heights.append({
                        'type': "Feature",
                        'geometry': {
                            "type": "Point",
                            "coordinates": [premises['geometry']['coordinates']]
                        },
                        'properties': {
                            'uid': premises['properties']['uid'],
                            'max_height': building_height['max_height']
                        }
                    })

        for tile_id in tile_ids:
            pathlist = glob.iglob(os.path.join(DATA_RAW_INPUTS,'terrain-5-dtm_2736772',
            tile_id['tile_ref_2_digit'] + '/*.asc'))
            for path in pathlist:
                if path[-10:-4] == tile_id['full_tile_ref']:
                    print('i matched')
                    raster = gdal.Open(path)
                    print(type(raster))
                
    return premises_data

def read_premises_data(x_min, y_min, x_max, y_max):
    """
    Reads in premises points from the OS AddressBase data (.csv).

    Data Schema
    ----------
    * id: :obj:`int`
        Unique Premises ID
    * oa: :obj:`str`
        ONS output area code
    * residential address count: obj:'str'
        Number of residential addresses
    * non-res address count: obj:'str'
        Number of non-residential addresses
    * postgis geom: obj:'str'
        Postgis reference
    * E: obj:'float'
        Easting coordinate
    * N: obj:'float'
        Northing coordinate

    """
    premises_data = []
    
    #pathlist = glob.iglob(os.path.join(DATA_RAW_INPUTS, 'layer_5_premises') + '/*.csv', recursive=False)
    pathlist = glob.iglob(os.path.join(DATA_RAW_INPUTS, 'layer_5_premises', 'blds_with_functions_en_E12000006.csv'))
    
    for path in pathlist:
        with open(os.path.join(path), 'r') as system_file:
            reader = csv.reader(system_file)
            next(reader)
            
            for line in reader:
                if (x_min <= float(line[8]) and y_min <= float(line[7]) and 
                    x_max >= float(line[8]) and y_max >= float(line[7])):
                    premises_data.append({
                        'type': "Feature",
                        'geometry': {
                            "type": "Point",
                            "coordinates": [float(line[8]), float(line[7])]
                        },
                        'properties': {
                            'uid': line[0]
                        }
                    })
                
    return premises_data

def find_osbg_tile(x_min, y_min, x_max, y_max):

    with fiona.open(os.path.join(DATA_RAW_SHAPES, 'osgb_grid', 'OSGB_Grid_5km.shp'), 'r') as source:
        line_geom = LineString([Point(x_min, y_min), Point(x_max, y_max)])
        all_tiles = [tile for tile in source if line_geom.intersection(shape(tile['geometry']))]

    tile_ids = []
    non_conforming_id_lengths = []

    for tile in all_tiles:
        tile_id = tile['properties']['TILE_NAME']
        if len(tile_id) == 6:
            tile_ids.append({
                'full_tile_ref': tile_id,
                'tile_ref_4_digit': tile_id[:4],
                'tile_ref_2_digit': tile_id[:2].lower(),
            })
        elif len(tile_id) == 4:
            tile_ids.append({
                'full_tile_ref': 'not available',
                'tile_ref_4_digit': tile_id[:4],
                'tile_ref_2_digit': tile_id[:2].lower(),
            })
        else:
            non_conforming_id_lengths.append(tile_id)

    return tile_ids

def read_building_height_data(x_min, y_min, x_max, y_max):
    """
    Reads in building height date from OS (.csv).

    """
    premises_data = []
    #print(x_min, y_min, x_max, y_max)
    #pathlist = glob.iglob(os.path.join(DATA_RAW_INPUTS, 'layer_5_premises') + '/*.csv', recursive=False)
    pathlist = glob.iglob(os.path.join(DATA_RAW_INPUTS, 'layer_5_premises', 'blds_with_functions_en_E12000006.csv'))
    
    for path in pathlist:
        with open(os.path.join(path), 'r') as system_file:
            reader = csv.reader(system_file)
            next(reader)
            
            for line in reader:
                if (x_min <= float(line[8]) and y_min <= float(line[7]) and 
                    x_max >= float(line[8]) and y_max >= float(line[7])):
                    premises_data.append({
                        'type': "Feature",
                        'geometry': {
                            "type": "Point",
                            "coordinates": [float(line[8]), float(line[7])]
                        },
                        'properties': {
                            'uid': line[0]
                        }
                    })
                
    return premises_data

def write_shapefile(data, filename):

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

    # Create path
    directory = os.path.join(DATA_INTERMEDIATE, 'built_env_test')
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Write all elements to output file
    with fiona.open(os.path.join(directory, filename), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        [sink.write(feature) for feature in data]


premises = find_line_of_sight(0.124896, 52.215965, 0.133939, 52.215263)

write_shapefile(premises, 'built_env_premises.shp')
