import time
start = time.time()
import os
import configparser
import csv
import fiona
import numpy as np

from itertools import groupby
from operator import itemgetter

from collections import OrderedDict, defaultdict
from rtree import index
from shapely.geometry import shape, Point, LineString, Polygon, mapping, MultiPolygon

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# SETUP SYSTEM FILE LOCATIONS
#####################################

SYSTEM_INPUT_PATH = os.path.join(BASE_PATH, 'raw')
SYSTEM_OUTPUT_PATH = os.path.join(BASE_PATH,'processed')
SYSTEM_RESULTS_PATH = os.path.join(BASE_PATH,'..', '..','results','digital_transport' )

#####################################
# setup yearly increments
#####################################

BASE_YEAR = 2020
END_YEAR = 2029
TIMESTEP_INCREMENT = 1
TIMESTEPS = range(BASE_YEAR, END_YEAR + 1, TIMESTEP_INCREMENT)

#####################################
# IMPORT SHAPES
#####################################

def read_in_os_open_roads(data):

    open_roads_network = []

    for my_file in os.listdir(data):
        if my_file.endswith("RoadLink.shp"):
            with fiona.open(os.path.join(data, my_file), 'r') as source:
                for src_shape in source:   
                    open_roads_network.extend([src_shape for src_shape in source if src_shape['properties']['function'] == 'Motorway' or src_shape['properties']['function'] == 'A Road' or src_shape['properties']['function'] == 'B Road' or src_shape['properties']['function'] == 'Minor Road' or src_shape['properties']['function'] == 'Local Road']) 
                    #open_roads_network.extend([src_shape for src_shape in source]) 
                    for element in open_roads_network:

                        if element['properties']['name1'] in element['properties']:
                            del element['properties']['name1']
                        else:
                            pass 

                        if element['properties']['name1_lang'] in element['properties']:
                            del element['properties']['name1_lang']
                        else:
                            pass 

                        if element['properties']['name2'] in element['properties']:
                            del element['properties']['name2']
                        else:
                            pass 

                        if element['properties']['name2_lang'] in element['properties']:
                            del element['properties']['name2_lang']
                        else:
                            pass 

                        if element['properties']['structure'] in element['properties']:
                            del element['properties']['structure']
                        else:
                            pass 

                        if element['properties']['nameTOID'] in element['properties']:
                            del element['properties']['nameTOID']
                        else:
                            pass 

                        if element['properties']['numberTOID'] in element['properties']:
                            del element['properties']['numberTOID']
                        else:
                            pass 

    return open_roads_network

def add_dense_motorway_geotype(data):

    for road in data:
        if road['properties']['function'] == 'Motorway': 
            if road['properties']['roadNumber'] == 'M25':
                road['properties']['function'] = 'Dense Motorway'
            elif road['properties']['roadNumber'] == 'M42':
                road['properties']['function'] = 'Dense Motorway'
            elif road['properties']['roadNumber'] == 'M5':
                road['properties']['function'] = 'Dense Motorway'
            elif road['properties']['roadNumber'] == 'M6':
                road['properties']['function'] = 'Dense Motorway'
            elif road['properties']['roadNumber'] == 'M20':
                road['properties']['function'] = 'Dense Motorway'
            elif road['properties']['roadNumber'] == 'M23':
                road['properties']['function'] = 'Dense Motorway'
            elif road['properties']['roadNumber'] == 'M3':
                road['properties']['function'] = 'Dense Motorway'
            elif road['properties']['roadNumber'] == 'M4':
                road['properties']['function'] = 'Dense Motorway'
            elif road['properties']['roadNumber'] == 'M1':
                road['properties']['function'] = 'Dense Motorway'
            elif road['properties']['roadNumber'] == 'M60':
                road['properties']['function'] = 'Dense Motorway'
            elif road['properties']['roadNumber'] == 'M62':
                road['properties']['function'] = 'Dense Motorway'
        else:
            pass

    return data

def read_in_built_up_areas():

    built_up_area_polygon_data = []

    # with fiona.open(os.path.join(SYSTEM_INPUT_PATH, 'built_up_areas', 'built_up_areas_cambridgeshire.shp'), 'r') as source:
    #     for src_shape in source:           
    #         built_up_area_polygon_data.extend([src_shape for src_shape in source]) 

    with fiona.open(os.path.join(SYSTEM_INPUT_PATH, 'built_up_areas', 'Builtup_Areas_December_2011_Boundaries_V2_england_and_wales', 'urban_areas_england_and_wales_27700.shp'), 'r') as source:
        for src_shape in source:           
            built_up_area_polygon_data.extend([src_shape for src_shape in source]) 

    with fiona.open(os.path.join(SYSTEM_INPUT_PATH, 'built_up_areas', 'shapefiles-mid-2016-settlements-localities_scotland', 'urban_areas_27700.shp'), 'r') as source:
        for src_shape in source:           
            built_up_area_polygon_data.extend([src_shape for src_shape in source]) 

    return built_up_area_polygon_data


def add_urban_rural_indicator_to_roads(road_data, built_up_polygons): 

    joined_road_data = []

    # Initialze Rtree
    idx = index.Index()

    for rtree_idx, area in enumerate(built_up_polygons):
        idx.insert(rtree_idx, shape(area['geometry']).bounds, area)
    
    # Join the two
    for road in road_data:
        matches = [n for n in idx.intersection((shape(road['geometry']).bounds), objects=True)]
        if len(matches) > 0:
            road['properties']['urban_rural_indicator'] = 'urban'
        else:
            road['properties']['urban_rural_indicator'] = 'rural'

    return road_data


def deal_with_none_values(data):

    my_data = []

    for road in data:      
        if road['properties']['roadNumber'] == None:
            my_data.append({
                'type': "Feature",
                'geometry': {
                    "type": "LineString",
                    "coordinates": road['geometry']['coordinates']
                },
                'properties': {
                    'road': road['properties']['function'],
                    'formofway': road['properties']['formOfWay'],    
                    'length': int(road['properties']['length']),
                    'function': road['properties']['function'],   
                    'urban_rural_indicator': road['properties']['urban_rural_indicator']    
                }
            })
        else:
            my_data.append({
                'type': "Feature",
                'geometry': {
                    "type": "LineString",
                    "coordinates": road['geometry']['coordinates']
                },
                'properties': {
                    'road': road['properties']['function'],
                    'formofway': road['properties']['formOfWay'],    
                    'length': int(road['properties']['length']),
                    'function': road['properties']['function'],   
                    'urban_rural_indicator': road['properties']['urban_rural_indicator']    
                }
            })
        
    return my_data

def write_road_network_shapefile(data, path):

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
    with fiona.open(os.path.join(SYSTEM_RESULTS_PATH, path), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        for feature in data:
            #print(feature)
            sink.write(feature)

def add_lad_to_road(road_network, lads):
    
    road_network_data = []

    # Initialze Rtree
    idx = index.Index()

    for rtree_idx, road in enumerate(road_network):
        idx.insert(rtree_idx, shape(road['geometry']).bounds, road)

    # Join the two
    for lad in lads:
        for n in idx.intersection((shape(lad['geometry']).bounds), objects=True):
            lad_shape = shape(lad['geometry'])
            road_shape = shape(n.object['geometry'])
            if lad_shape.contains(road_shape):
                n.object['properties']['lad'] = lad['properties']['name']
                road_network_data.append(n.object)

    return road_network_data


def import_shapes(file_path):
    with fiona.open(file_path, 'r') as source:
        return [shape for shape in source]

def extract_geojson_properties(data):
    
    my_data = []

    for item in data:
        my_data.append({
            'road': item['properties']['road'],
            'formofway': item['properties']['formofway'], 
            'length': item['properties']['length'],
            'function': item['properties']['function'], 
            'urban_rural_indicator': item['properties']['urban_rura'],        
        })

    return my_data

def extract_geojson_properties_with_lad(data):
    
    my_data = []

    for item in data:
        my_data.append({
            'road': item['properties']['road'],
            'formofway': item['properties']['formofway'], 
            'length': item['properties']['length'],
            'function': item['properties']['function'], 
            'urban_rural_indicator': item['properties']['urban_rura'],
            'lad': item['properties']['lad'],         
        })

    return my_data

def grouper(data, aggregated_metric, group_item1, group_item2, group_item3):

    my_grouper = itemgetter(group_item1, group_item2, group_item3)
    result = []
    for key, grp in groupby(sorted(data, key = my_grouper), my_grouper):
        try:
            temp_dict = dict(zip([group_item1, group_item2, group_item3], key))
            temp_dict[aggregated_metric] = sum(int(item[aggregated_metric]) for item in grp)
            result.append(temp_dict)
        except:
            pass
    
    return result

def grouper_with_lad(data, aggregated_metric, group_item1, group_item2, group_item3, group_item4):

    my_grouper = itemgetter(group_item1, group_item2, group_item3, group_item4)
    result = []
    for key, grp in groupby(sorted(data, key = my_grouper), my_grouper):
        try:
            temp_dict = dict(zip([group_item1, group_item2, group_item3, group_item4], key))
            temp_dict[aggregated_metric] = sum(int(item[aggregated_metric]) for item in grp)
            result.append(temp_dict)
        except:
            pass
    
    return result

#####################################
# WRITE CSV DATA
#####################################

def csv_writer(data, output_fieldnames, filename):
    """
    Write data to a CSV file path
    """
    fieldnames = data[0].keys()
    with open(os.path.join(SYSTEM_RESULTS_PATH, filename),'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)


def write_shapefile(data, path, crs):

    # Translate props to Fiona sink schema
    prop_schema = []
    for name, value in data[0]['properties'].items():
        fiona_prop_type = next((fiona_type for fiona_type, python_type in fiona.FIELD_TYPES_MAP.items() if python_type == type(value)), None)
        prop_schema.append((name, fiona_prop_type))

    sink_driver = 'ESRI Shapefile'
    sink_crs = {'init':crs}
    sink_schema = {
        'geometry': data[0]['geometry']['type'],
        'properties': OrderedDict(prop_schema)
    }

    # Write all elements to output file
    with fiona.open(path, 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        for feature in data:
            sink.write(feature)

#####################################
# setup file locations and data files
#####################################

def read_in_csv_road_geotype_data(data, lad_indicator):

    road_type_data = []

    if lad_indicator == 0:
        with open(os.path.join(SYSTEM_RESULTS_PATH, data), 'r',  encoding='utf8', errors='replace') as system_file:
            reader = csv.reader(system_file)
            next(reader)
            for line in reader:
                road_type_data.append({
                    'road_function': line[0],
                    'formofway': line[1],
                    'urban_rural': line[2],
                    'length_m': (int(line[3]))
                })   
    else:
        with open(os.path.join(SYSTEM_RESULTS_PATH, data), 'r',  encoding='utf8', errors='replace') as system_file:
            reader = csv.reader(system_file)
            next(reader)
            for line in reader:
                road_type_data.append({
                    'lad': line[0],
                    'road_function': line[1],
                    'formofway': line[2],
                    'urban_rural': line[3],
                    'length_m': (int(line[4]))
                })   

    return road_type_data

#####################################
# calculate supply side costings
#####################################

def calculate_tco_for_each_asset(capex, opex, discount_rate, current_year, year_deployed, asset_lifetime, end_year, repeating):
    """
    - capex
    - opex
    - discount rate
    - current year
    - year deployed
    - asset lifetime
    - end_year
    - repeating
    """

    repeating_capex_cost_year1 = capex / (1 + discount_rate) ** (year_deployed - current_year)

    if repeating == 'yes':
        repeating_capex_cost_year5 = capex / (1 + discount_rate) ** ((year_deployed - current_year) + asset_lifetime)
    else:
        repeating_capex_cost_year5 = 0
    
    total_capex = int(round(repeating_capex_cost_year1 + repeating_capex_cost_year5, 0))

    my_opex = []

    for i in range(10):
        total_opex = int(round(opex / (1 + discount_rate) ** ((year_deployed - current_year) + (i+1)), 0)) 
        my_opex.append(total_opex)

    total_cost_of_ownership = total_capex + sum(my_opex)

    return total_cost_of_ownership

def calculate_number_of_RAN_units_and_civil_works_costs(data, deployment_period, year, scenario, strategy, cell_capex, cell_civil_works_capex, cells_per_mounting, spacing_factor):

    if BASE_YEAR <= year < (BASE_YEAR + deployment_period):  
        for road in data:
            cell_spacing = _get_scenario_cell_spacing_value(scenario, strategy, road['road_function'], road['urban_rural'])
            #print('1) cell spacing is {}'.format(cell_spacing))
            #print('2) cell spacing factor is {}'.format(spacing_factor))
            modified_cell_spacing = cell_spacing * spacing_factor
            #print('3) modified cell spacing factor is {}'.format(modified_cell_spacing))
            road['RAN_units'] = round((float(road['length_m']) / float(modified_cell_spacing)) / deployment_period, 5)
            #print('4) road length is {}'.format(road['length_m']))
            #print('5) RAN_units per km is {}'.format(road['RAN_units']))
        for road in data:
            road['RAN_cost'] = round((road['RAN_units'] * cell_capex) , 5)
        for road in data:
            road['small_cell_mounting_points'] = round((road['RAN_units'] / cells_per_mounting), 5)
        for road in data:
            road['small_cell_mounting_cost'] = round((road['small_cell_mounting_points'] * cell_civil_works_capex), 5)
    else:
        for road in data:
            road['RAN_units'] = 0
        for road in data:
            road['RAN_cost'] = 0
        for road in data:
            road['small_cell_mounting_points'] = 0
        for road in data:
            road['small_cell_mounting_cost'] = 0

    return data

def _get_scenario_cell_spacing_value(scenario, strategy, road_type, urban_rural):
    
    if strategy == 'cellular_V2X_full_greenfield' or strategy == 'cellular_V2X_NRTS':
        if scenario == 'low':
            if urban_rural == 'urban':
                if road_type == 'Dense Motorway':
                    spacing = 0.5
                elif road_type == 'Motorway':
                    spacing = 0.7
                elif road_type == 'A Road':
                    spacing = 0.9
                else:
                    spacing = 1
            else:
                if road_type == 'Dense Motorway':
                    spacing = 0.5
                elif road_type == 'Motorway':
                    spacing = 0.7
                elif road_type == 'A Road':
                    spacing = 0.9
                else:
                    spacing = 1                
        elif scenario == 'baseline':
            if urban_rural == 'urban':
                if road_type == 'Dense Motorway':
                    spacing = 0.4
                elif road_type == 'Motorway':
                    spacing = 0.56
                elif road_type == 'A Road':
                    spacing = 0.72
                else:
                    spacing = 0.8
            else:
                if road_type == 'Dense Motorway':
                    spacing = 0.4
                elif road_type == 'Motorway':
                    spacing = 0.56
                elif road_type == 'A Road':
                    spacing = 0.72
                else:
                    spacing = 0.8
        elif scenario == 'high':
            if urban_rural == 'urban':
                if road_type == 'Dense Motorway':
                    spacing = 0.3
                elif road_type == 'Motorway':
                    spacing = 0.42
                else:
                    spacing = 0.6
            else:
                if road_type == 'Dense Motorway':
                    spacing = 0.3
                elif road_type == 'Motorway':
                    spacing = 0.42
                elif road_type == 'A Road':
                    spacing = 0.54
                else:
                    spacing = 0.6

    elif strategy == 'DSRC_full_greenfield' or strategy == 'DSRC_NRTS':
        if scenario == 'low':
            if urban_rural == 'urban':
                if road_type == 'Dense Motorway':
                    spacing = 0.25
                elif road_type == 'Motorway':
                    spacing = 0.35
                elif road_type == 'A Road':
                    spacing = 0.45
                else:
                    spacing = 0.5
            else:
                if road_type == 'Dense Motorway':
                    spacing = 0.25
                elif road_type == 'Motorway':
                    spacing = 0.35
                elif road_type == 'A Road':
                    spacing = 0.45
                else:
                    spacing = 0.5              
        elif scenario == 'baseline':
            if urban_rural == 'urban':
                if road_type == 'Dense Motorway':
                    spacing = 0.2
                elif road_type == 'Motorway':
                    spacing = 0.28
                elif road_type == 'A Road':
                    spacing = 0.36
                else:
                    spacing = 0.4
            else:
                if road_type == 'Dense Motorway':
                    spacing = 0.2
                elif road_type == 'Motorway':
                    spacing = 0.28
                elif road_type == 'A Road':
                    spacing = 0.36
                else:
                    spacing = 0.4
        elif scenario == 'high':
            if urban_rural == 'urban':
                if road_type == 'Dense Motorway':
                    spacing = 0.15
                elif road_type == 'Motorway':
                    spacing = 0.21
                elif road_type == 'A Road':
                    spacing = 0.27
                else:
                    spacing = 0.3
            else:
                if road_type == 'Dense Motorway':
                    spacing = 0.15
                elif road_type == 'Motorway':
                    spacing = 0.21
                elif road_type == 'A Road':
                    spacing = 0.27
                else:
                    spacing = 0.3

    return spacing * 1000

#####################################
# demand estimation
#####################################

def calculate_potential_demand(data, car_length, scenario, year, growth_rate):

    for road in data:
        if road['road_function'] == 'Dense Motorway':

            cars_per_lane = _get_cars_per_lane('Dense Motorway', scenario, year, growth_rate)
            road['cars_per_lane'] = (round(int(road['length_m']) * cars_per_lane, 0))

            if road['formofway'] == 'Collapsed Dual Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 6
            elif road['formofway'] == 'Dual Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 6
            elif road['formofway'] == 'Roundabout':
                road['total_cars'] = road['cars_per_lane'] * 3
            elif road['formofway'] == 'Single Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Slip Road':
                road['total_cars'] = road['cars_per_lane'] * 1

        elif road['road_function'] == 'Motorway': 

            cars_per_lane = _get_cars_per_lane('Motorway', scenario, year, growth_rate)
            road['cars_per_lane'] = int(round(int(road['length_m']) * cars_per_lane, 0))

            if road['formofway'] == 'Collapsed Dual Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 6
            elif road['formofway'] == 'Dual Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 6
            elif road['formofway'] == 'Roundabout':
                road['total_cars'] = road['cars_per_lane'] * 3
            elif road['formofway'] == 'Single Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Slip Road':
                road['total_cars'] = road['cars_per_lane'] * 1

        elif road['road_function'] == 'A Road': 

            cars_per_lane = _get_cars_per_lane('A Road', scenario, year, growth_rate)
            road['cars_per_lane'] = int(round(int(road['length_m']) * cars_per_lane, 0))

            if road['formofway'] == 'Collapsed Dual Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 4
            elif road['formofway'] == 'Dual Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 4
            elif road['formofway'] == 'Roundabout':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Single Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Slip Road':
                road['total_cars'] = road['cars_per_lane'] * 1

        elif road['road_function'] == 'B Road': 

            cars_per_lane = _get_cars_per_lane('B Road', scenario, year, growth_rate)
            road['cars_per_lane'] = int(round(int(road['length_m']) * cars_per_lane, 0))

            if road['formofway'] == 'Collapsed Dual Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Dual Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Roundabout':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Single Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 1
            elif road['formofway'] == 'Slip Road':
                road['total_cars'] = road['cars_per_lane'] * 1

        elif road['road_function'] == 'Minor Road': 

            cars_per_lane = _get_cars_per_lane('Minor Road', scenario, year, growth_rate)
            road['cars_per_lane'] = int(round(int(road['length_m']) * cars_per_lane, 0))

            if road['formofway'] == 'Collapsed Dual Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Dual Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Roundabout':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Single Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Slip Road':
                road['total_cars'] = road['cars_per_lane'] * 1

        elif road['road_function'] == 'Local Road': 

            cars_per_lane = _get_cars_per_lane('Local Road', scenario, year, growth_rate)
            road['cars_per_lane'] = int(round(int(road['length_m']) * cars_per_lane, 0))

            if road['formofway'] == 'Collapsed Dual Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Dual Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Roundabout':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Single Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Slip Road':
                road['total_cars'] = road['cars_per_lane'] * 1

        else:

            road['cars_per_lane'] = int(round(int(road['length_m']) * 0.000005, 0))

            if road['formofway'] == 'Collapsed Dual Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Dual Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Roundabout':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Single Carriageway':
                road['total_cars'] = road['cars_per_lane'] * 2
            elif road['formofway'] == 'Slip Road':
                road['total_cars'] = road['cars_per_lane'] * 1

    return data

def _get_cars_per_lane(road_function, scenario, timestep, growth_rate):

    if road_function == 'Dense Motorway' and scenario == 'high':
        cars = 35 
    if road_function == 'Dense Motorway' and scenario == 'baseline':
        cars = 25
    if road_function == 'Dense Motorway' and scenario == 'low':
        cars = 15
    if road_function == 'Motorway' and scenario == 'high':
        cars = 20
    if road_function == 'Motorway' and scenario == 'baseline':
        cars = 15
    if road_function == 'Motorway' and scenario == 'low':
        cars = 10
    if road_function == 'A Road' and scenario == 'high':
        cars = 12
    if road_function == 'A Road' and scenario == 'baseline':
        cars = 8
    if road_function == 'A Road' and scenario == 'low':
        cars = 6
    if road_function == 'B Road' and scenario == 'high':
        cars = 5
    if road_function == 'B Road' and scenario == 'baseline':
        cars = 4
    if road_function == 'B Road' and scenario == 'low':
        cars = 3
    if road_function == 'Minor Road' and scenario == 'high':
        cars = 4
    if road_function == 'Minor Road' and scenario == 'baseline':
        cars = 3
    if road_function == 'Minor Road' and scenario == 'low':
        cars = 2
    if road_function == 'Local Road' and scenario == 'high':
        cars = 3
    if road_function == 'Local Road' and scenario == 'baseline':
        cars = 2
    if road_function == 'Local Road' and scenario == 'low':
        cars = 1

    return _vehicle_registration_increases(cars, timestep, growth_rate)

def _vehicle_registration_increases(vehicles, timestep, registeration_growth_rate):
    
    if timestep == BASE_YEAR:
        total_vehicles = vehicles
    else:
        total_vehicles = vehicles * (1 + (registeration_growth_rate * (timestep-BASE_YEAR))) #** ((year_deployed - current_year) + asset_lifetime)
    
    return total_vehicles/1000

def s_curve_function(year, start, end, _year, takeover, curviness):
    
    return start + (end - start) / (1 + curviness ** ((_year + takeover / 2-(year-2019))/takeover))

def calculate_yearly_CAV_take_up(data, year, scenario, wtp_scenario, discount_rate, PENETRATION_year):

    #estimate capable vehicles
    for road in data:
        if road['total_cars'] > 0:  
            road['annual_CAV_capability'] = round(road['total_cars'] * s_curve_function(year, 0, 0.8, 3, 8, 500), 0)
        else:
            road['annual_CAV_capability'] = 0

    #estimate tabke-up
    for road in data:
        if road['annual_CAV_capability'] > 0:  
            road['annual_CAV_take_up'] = round(road['annual_CAV_capability'] * s_curve_function(year, 0, 0.70, PENETRATION_year, 4, 500), 0)
        else:
            road['annual_CAV_take_up'] = 0

    wtp_per_user = _get_scenario_wtp_value(wtp_scenario)

    for road in data:
        if road['annual_CAV_take_up'] > 0:
            annual_amount = (wtp_per_user * 12)
            discounted_annual_amount = round(discount_revenue(annual_amount, year, discount_rate),3)
            road['CAV_revenue'] = road['annual_CAV_take_up'] * discounted_annual_amount
        else:
            road['CAV_revenue'] = 0

    mbps_per_vehicle = _get_scenario_data_value(scenario)

    for road in data:
        
        if road['annual_CAV_take_up'] > 0:
            road['CAV_mbps_demand'] = road['annual_CAV_take_up'] * (mbps_per_vehicle)
        else:
            road['CAV_mbps_demand'] = 0

    return data

def _get_scenario_wtp_value(wtp_scenario):

    if scenario == 'high':
        wtp = 20
    elif scenario == 'baseline':
        wtp = 4
    elif scenario == 'low':
        wtp = 2
    
    return wtp

def _get_scenario_data_value(scenario):

    if scenario == 'high':
        mbps = 10
    elif scenario == 'baseline':
        mbps = 4
    elif scenario == 'low':
        mbps = 1
    
    return mbps

def discount_revenue(value, year, discount_rate):

    if year == BASE_YEAR:
        discounted_value = value 
    else:
        discounted_value = value / ((1 + discount_rate) ** (year - BASE_YEAR))

    return discounted_value

def calculate_backhaul_costs(data, deployment_period, year, strategy, fibre_tco):
    """
    cost of full deployment split over the length of the deployment_period
    """   
    backhaul_shortening_factor = 0.5

    if BASE_YEAR <= year < (BASE_YEAR + deployment_period):  
        if strategy == 'cellular_V2X_full_greenfield' or strategy =='DSRC_full_greenfield':
            for road in data:
                if road['formofway'] == 'Collapsed Dual Carriageway' or road['formofway'] == 'Dual Carriageway' or road['formofway'] == 'Single Carriageway':          
                    road['fibre_backhaul_m'] = round(road['length_m'] / deployment_period,2)
                else:
                    road['fibre_backhaul_m'] = 0 

        elif strategy == 'cellular_V2X_NRTS' or strategy == 'DSRC_NRTS':
            for road in data:
                if road['formofway'] == 'Collapsed Dual Carriageway' or road['formofway'] == 'Dual Carriageway' or road['formofway'] == 'Single Carriageway':   
                    if road['road_function'] == 'Dense Motorway' or road['road_function'] == 'Motorway' or road['road_function'] == 'A Road':
                        road['fibre_backhaul_m'] = round((road['length_m']* backhaul_shortening_factor) / deployment_period,2)       
                    if road['road_function'] == 'B Road' or road['road_function'] == 'Minor Road' or road['road_function'] == 'Local Road':
                        road['fibre_backhaul_m'] = round((road['length_m']) / deployment_period,2)   
                else:
                    road['fibre_backhaul_m'] = 0            
        else:
            pass
        
    else:
        for road in data:
            road['fibre_backhaul_m'] = 0
        for road in data:
            road['fibre_backhaul_cost'] = 0
        for road in data:
            road['total_tco'] = 0

    for road in data:
        road['fibre_backhaul_cost'] = road['fibre_backhaul_m'] * fibre_tco
    
    for road in data:
        road['total_tco'] = road['RAN_cost'] + road['small_cell_mounting_cost'] + road['fibre_backhaul_cost']

    return data

#####################################
# simulation
#####################################

def simulation(data, scenario, strategy, wtp_scenario, lad_indicator, VEHCILE_REGISTRATION_GROWTH_RATE):
    SPACING_FACTOR = 1
    for year in TIMESTEPS:

        print("-", year)
        
        road_geotype_data = calculate_potential_demand(data, 5, scenario, year, VEHCILE_REGISTRATION_GROWTH_RATE)
        
        road_geotype_data = calculate_yearly_CAV_take_up(road_geotype_data, year, scenario, wtp_scenario, DISCOUNT_RATE, PENETRATION_year)
        
        road_geotype_data = calculate_number_of_RAN_units_and_civil_works_costs(road_geotype_data, DEPLOYMENT_PERIOD, year, scenario, strategy, small_cell_tco, small_cell_civil_works_tco, 2, SPACING_FACTOR)
        
        road_geotype_data = calculate_backhaul_costs(road_geotype_data, DEPLOYMENT_PERIOD, year, strategy, fibre_tco_per_m)
        if lad_indicator == 0:

            write_spend(road_geotype_data, year, scenario, strategy, wtp_scenario)
        
        else:

            write_spend_lad(road_geotype_data, year, scenario, strategy, wtp_scenario)
            
    return print("simulation_complete")

def sensitivity_simulation_isd(data, scenario, strategy, wtp_scenario, lad_indicator, VEHCILE_REGISTRATION_GROWTH_RATE):
    DEPLOYMENT_PERIOD = 1
    SPACING_FACTOR = 1
    #if scenario == 'baseline':#: and strategy =='cellular_V2X_full_greenfield': # or strategy =='DSRC_full_greenfield':   
    for i in range(10,125,5):
        i = i / 10
        for year in TIMESTEPS:
            if year == BASE_YEAR:

                print("-", year)
                
                road_geotype_data = calculate_potential_demand(data, 5, scenario, year, VEHCILE_REGISTRATION_GROWTH_RATE)
                
                road_geotype_data = calculate_yearly_CAV_take_up(road_geotype_data, year, scenario, wtp_scenario, DISCOUNT_RATE, PENETRATION_year)
                
                road_geotype_data = calculate_number_of_RAN_units_and_civil_works_costs(road_geotype_data, DEPLOYMENT_PERIOD, year, scenario, strategy, small_cell_tco, small_cell_civil_works_tco, 2, i)
                
                road_geotype_data = calculate_backhaul_costs(road_geotype_data, DEPLOYMENT_PERIOD, year, strategy, fibre_tco_per_m)

                write_sensitivity_isd_spend(road_geotype_data, year, scenario, strategy, wtp_scenario, i)

    return print("sensitivity_isd_simulation_complete")

def sensitivity_simulation_penetration(data, scenario, strategy, wtp_scenario, lad_indicator, VEHCILE_REGISTRATION_GROWTH_RATE):
    DEPLOYMENT_PERIOD = 1
    SPACING_FACTOR = 1
    for i in range(10,110,10):
        i = i / 10
        for year in TIMESTEPS:
            if year == 2029:

                print("-", year)
                
                road_geotype_data = calculate_potential_demand(data, 5, scenario, year, VEHCILE_REGISTRATION_GROWTH_RATE)
                
                road_geotype_data = calculate_yearly_CAV_take_up(road_geotype_data, year, scenario, wtp_scenario, DISCOUNT_RATE, i)
                
                road_geotype_data = calculate_number_of_RAN_units_and_civil_works_costs(road_geotype_data, DEPLOYMENT_PERIOD, year, scenario, strategy, small_cell_tco, small_cell_civil_works_tco, 2, SPACING_FACTOR)
                
                road_geotype_data = calculate_backhaul_costs(road_geotype_data, DEPLOYMENT_PERIOD, year, strategy, fibre_tco_per_m)

                write_sensitivity_penetration_spend(road_geotype_data, year, scenario, strategy, wtp_scenario, i)
    
    return print("sensitivity_penetration_simulation_complete")

#####################################
# write out 
#####################################

def write_spend(data, year, scenario, strategy, wtp_scenario):
    suffix = _get_suffix(scenario, strategy, wtp_scenario)
    filename = os.path.join(SYSTEM_RESULTS_PATH, 'spend_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        spend_file = open(filename, 'w', newline='')
        spend_writer = csv.writer(spend_file)
        spend_writer.writerow(
            ('year', 'scenario', 'strategy', 'wtp_scenario',
             'road_function','formofway', 'length_m','urban_rural', 
             'cars_per_lane', 'total_cars', 'annual_CAV_capability','annual_CAV_take_up','CAV_revenue', 'CAV_mbps_demand',
             'RAN_units','RAN_cost','small_cell_mounting_points','small_cell_mounting_cost', 
             'fibre_backhaul_m', 'fibre_backhaul_cost', 'total_tco'))
    else:
        spend_file = open(filename, 'a', newline='')
        spend_writer = csv.writer(spend_file)

    # output and report results for this timestep
    for road in data:
        spend_writer.writerow(
            (year, scenario, strategy, wtp_scenario, 
            road['road_function'], road['formofway'], road['length_m'], road['urban_rural'], 
            road['cars_per_lane'], road['total_cars'], road['annual_CAV_capability'], road['annual_CAV_take_up'], 
            road['CAV_revenue'], road['CAV_mbps_demand'],
            road['RAN_units'], road['RAN_cost'], road['small_cell_mounting_points'],road['small_cell_mounting_cost'], 
            road['fibre_backhaul_m'], road['fibre_backhaul_cost'], road['total_tco']))

def write_spend_lad(data, year, scenario, strategy, wtp_scenario):
    suffix = _get_suffix(scenario, strategy, wtp_scenario)
    filename = os.path.join(SYSTEM_RESULTS_PATH, 'lad_spend_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        spend_file = open(filename, 'w', newline='')
        spend_writer = csv.writer(spend_file)
        spend_writer.writerow(
            ('lad','year', 'scenario', 'strategy', 'wtp_scenario',
             'road_function','formofway', 'length_m','urban_rural', 
             'cars_per_lane', 'total_cars', 'annual_CAV_capability','annual_CAV_take_up','CAV_revenue', 'CAV_mbps_demand',
             'RAN_units','RAN_cost','small_cell_mounting_points','small_cell_mounting_cost', 
             'fibre_backhaul_m', 'fibre_backhaul_cost', 'total_tco'))
    else:
        spend_file = open(filename, 'a', newline='')
        spend_writer = csv.writer(spend_file)

    # output and report results for this timestep
    for road in data:
        spend_writer.writerow(
            (road['lad'], year, scenario, strategy, wtp_scenario, 
            road['road_function'], road['formofway'], road['length_m'], road['urban_rural'], 
            road['cars_per_lane'], road['total_cars'], road['annual_CAV_capability'], road['annual_CAV_take_up'], 
            road['CAV_revenue'], road['CAV_mbps_demand'],
            road['RAN_units'], road['RAN_cost'], road['small_cell_mounting_points'],road['small_cell_mounting_cost'], 
            road['fibre_backhaul_m'], road['fibre_backhaul_cost'], road['total_tco']))

def _get_suffix(scenario, strategy, wtp_scenario):
    suffix = 'scenario_{}_strategy_{}_wtp{}'.format(scenario, strategy, wtp_scenario)
    return suffix

def write_sensitivity_isd_spend(data, year, scenario, strategy, wtp_scenario, i):
    filename = os.path.join(SYSTEM_RESULTS_PATH, 'sensitivity_isd_spend_{}_{}_{}_{}.csv'.format(scenario, strategy, wtp_scenario, i))

    if year == BASE_YEAR:
        spend_file = open(filename, 'w', newline='')
        spend_writer = csv.writer(spend_file)
        spend_writer.writerow(
            ('year', 'scenario', 'strategy', 'wtp_scenario', 'isd', 
            'RAN_units','small_cell_mounting_points','fibre_backhaul_m','length_m', 'total_tco'))
    else:
        spend_file = open(filename, 'a', newline='')
        spend_writer = csv.writer(spend_file)

    # output and report results for this timestep
    for road in data:
        spend_writer.writerow(
            (year, scenario, strategy, wtp_scenario, i, 
            road['RAN_units'], road['small_cell_mounting_points'], road['fibre_backhaul_m'], road['length_m'], road['total_tco']))

def write_sensitivity_penetration_spend(data, year, scenario, strategy, wtp_scenario, i):
    filename = os.path.join(SYSTEM_RESULTS_PATH, 'sensitivity_penetration_spend_{}_{}_{}_{}.csv'.format(scenario, strategy, wtp_scenario, i))

    if year == 2029:
        spend_file = open(filename, 'w', newline='')
        spend_writer = csv.writer(spend_file)
        spend_writer.writerow(
            ('year', 'scenario', 'strategy', 'wtp_scenario', 'inflection_year', 
             'total_cars', 'annual_CAV_take_up', 'CAV_revenue')) 
    else:
        spend_file = open(filename, 'a', newline='')
        spend_writer = csv.writer(spend_file)

    # output and report results for this timestep
    for road in data:
        spend_writer.writerow(
            (year, scenario, strategy, wtp_scenario, i, 
            road['total_cars'], road['annual_CAV_take_up'], road['CAV_revenue']))

#####################################
# RUN SCRIPTS
#####################################

# print('read in road network')
# #road_network = read_in_os_open_roads((os.path.join(SYSTEM_INPUT_PATH, 'os_open_roads', 'open-roads_2438901_cambridge')))
# road_network = read_in_os_open_roads(os.path.join(SYSTEM_INPUT_PATH, 'os_open_roads', 'open-roads_2443825'))

# print('adding dense motorway geotype')
# road_network = add_dense_motorway_geotype(road_network)

# print('read in built up area polygons')
# built_up_areas = read_in_built_up_areas()

# print('add built up area indicator to urban roads')
# road_network = add_urban_rural_indicator_to_roads(road_network, built_up_areas)

# print('dealing with missing values')
# road_network = deal_with_none_values(road_network)

# print("writing road network")
# write_road_network_shapefile(road_network, 'road_network.shp')
# write_shapefile(road_network, SYSTEM_RESULTS_PATH, 'road_network.shp')
# # # #####################################

# print('read in road network')
# road_network = import_shapes(os.path.join(SYSTEM_RESULTS_PATH, 'road_network.shp'))

# print("extracting geojson properties")
# aggegated_road_statistics = extract_geojson_properties(road_network)

# print("applying grouped aggregation")
# aggegated_statistics_by_road = grouper(aggegated_road_statistics, 'length', 'function', 'formofway', 'urban_rural_indicator')

# print('write all road statistics')
# road_statistics_fieldnames = ['function', 'formofway', 'length', 'urban_rural_indicator']
# csv_writer(aggegated_statistics_by_road, road_statistics_fieldnames, 'aggregated_road_statistics.csv')

# # # #####################################

# print('read lads')
# geojson_lad_areas = import_shapes(os.path.join(SYSTEM_INPUT_PATH, 'lad_uk_2016-12', 'lad_uk_2016-12.shp'))

# print('intersect roads and lad boundaries')
# road_network = add_lad_to_road(road_network, geojson_lad_areas)

# print("extracting geojson properties")
# aggegated_road_statistics = extract_geojson_properties_with_lad(road_network)

# print("applying grouped aggregation")
# aggegated_road_statistics_by_lad = grouper_with_lad(aggegated_road_statistics, 'length', 'lad', 'function', 'formofway', 'urban_rural_indicator')

# print('write all road statistics')
# lad_road_statistics_fieldnames = ['lad', 'function', 'formofway', 'length', 'urban_rural_indicator']
# csv_writer(aggegated_road_statistics_by_lad, lad_road_statistics_fieldnames, 'aggregated_road_statistics.csv')

#####################################
# run functions
#####################################

DEPLOYMENT_PERIOD = 4
VEHCILE_REGISTRATION_GROWTH_RATE = 0.009 #0.9% growth per annum
DISCOUNT_RATE = 0.035
SENSITIVITY_ANALYSIS = 0
PENETRATION_year = 3

print("reading in aggregated road geotype data")
road_geotype_data = read_in_csv_road_geotype_data('aggregated_road_statistics.csv', 0)

print("reading in aggregated road geotype data")
lad_road_geotype_data = read_in_csv_road_geotype_data('aggregated_road_statistics_by_lad.csv', 1)

#### 5G NORMA COSTS ###
print("calculating tco costs")
# small_cell_tco = calculate_tco_for_each_asset(2500, 350, DISCOUNT_RATE, 2019, 2020, 10, 2029, 'no') 
# small_cell_civil_works_tco = calculate_tco_for_each_asset(10800, 0, DISCOUNT_RATE, 2019, 2020, 0, 2029, 'no')
# fibre_tco_per_km = calculate_tco_for_each_asset(20000, 20, DISCOUNT_RATE, 2019, 2020, 0, 2029, 'no') 
#### Analysys Mason COSTS ###
#euro 3500:£3143 using 1EUR:£0.9, EUR285:256
small_cell_tco = calculate_tco_for_each_asset(3150, 189, DISCOUNT_RATE, 2019, 2020, 10, 2029, 'no') 
small_cell_civil_works_tco = calculate_tco_for_each_asset(10800, 0, DISCOUNT_RATE, 2019, 2020, 0, 2029, 'no')
fibre_tco_per_m = (calculate_tco_for_each_asset(20000, 20, DISCOUNT_RATE, 2019, 2020, 0, 2029, 'no')/1000) 

print('running scenarios')

for scenario, strategy, wtp_scenario in [
        ('high', 'cellular_V2X_full_greenfield', 'high'),
        ('baseline', 'cellular_V2X_full_greenfield', 'baseline'),
        ('low', 'cellular_V2X_full_greenfield', 'low'),

        ('high', 'cellular_V2X_NRTS', 'high'),
        ('baseline', 'cellular_V2X_NRTS', 'baseline'),
        ('low', 'cellular_V2X_NRTS', 'low'),

        ('high', 'DSRC_full_greenfield', 'high'),
        ('baseline', 'DSRC_full_greenfield', 'baseline'),
        ('low', 'DSRC_full_greenfield', 'low'),

        ('high', 'DSRC_NRTS', 'high'),
        ('baseline', 'DSRC_NRTS', 'baseline'),
        ('low', 'DSRC_NRTS', 'low'),
    ]:

    print("Running:", scenario, strategy, wtp_scenario)
    run = simulation(road_geotype_data, scenario, strategy, wtp_scenario, 0, VEHCILE_REGISTRATION_GROWTH_RATE)
    run = simulation(lad_road_geotype_data, scenario, strategy, wtp_scenario, 1, VEHCILE_REGISTRATION_GROWTH_RATE)
    run = sensitivity_simulation_isd(lad_road_geotype_data, scenario, strategy, wtp_scenario, 1, VEHCILE_REGISTRATION_GROWTH_RATE)
    run = sensitivity_simulation_penetration(lad_road_geotype_data, scenario, strategy, wtp_scenario, 1, VEHCILE_REGISTRATION_GROWTH_RATE)


end = time.time()
print("script finished")
print("script took {} minutes to complete".format(round((end - start)/60, 0))) 

