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
    with fiona.open(os.path.join(SYSTEM_OUTPUT_PATH, path), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        for feature in data:
            #print(feature)
            sink.write(feature)

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

def grouper(data, aggregated_metric, group_item1, group_item2, group_item3, group_item4):

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
    with open(os.path.join(SYSTEM_OUTPUT_PATH, filename),'w') as csv_file:
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

def read_in_csv_road_geotype_data(data):

    road_type_data = []

    with open(os.path.join(SYSTEM_OUTPUT_PATH, data), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            road_type_data.append({
                'road': line[0],
                'road_function': line[1],
                'formofway': line[2],
                'urban_rural': line[3],
                'length_km': (int(line[4])/1000)
            })   

    return road_type_data

#####################################
# calculate supply side costings
#####################################

def calculate_tco_for_each_asset(capex, opex, discount_rate, current_year, year_deployed, asset_lifetime, end_year, repeating):
    
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

def calculate_number_of_RAN_units_and_civil_works_costs(data, deployment_period, year, scenario, strategy, cell_capex, cell_civil_works_capex, cells_per_mounting):

    if BASE_YEAR <= year < (BASE_YEAR + deployment_period):  
        for road in data:
            cell_spacing = _get_scenario_cell_spacing_value(scenario, strategy, road['formofway'], road['urban_rural'])
            road['RAN_units'] = int(round((int(road['length_km']) / cell_spacing) / deployment_period, 0))
        for road in data:
            road['RAN_cost'] = int(round((road['RAN_units'] * cell_capex) / deployment_period, 0))
        for road in data:
            road['small_cell_mounting_points'] = int(round((road['RAN_units'] / cells_per_mounting) / deployment_period, 0))
        for road in data:
            road['small_cell_mounting_cost'] = int(round((road['small_cell_mounting_points'] * cell_civil_works_capex) / deployment_period, 0))
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
    
    if strategy == 'cellular_V2X':
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
    
    elif strategy == 'DSRC_full_greenfield' or strategy == 'DSRC_NRTS_greenfield':
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

    return spacing

#####################################
# demand estimation
#####################################

def calculate_potential_demand(data, car_length, car_spacing):

    for road in data:
        if road['road_function'] == 'Dense Motorway': 

            cars_per_lane = _get_cars_per_lane('Dense Motorway', car_spacing)
            road['cars_per_lane'] = int(round(int(road['length_km']) * cars_per_lane, 0))

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

            cars_per_lane = _get_cars_per_lane('Motorway', car_spacing)
            road['cars_per_lane'] = int(round(int(road['length_km']) * cars_per_lane, 0))

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

            cars_per_lane = _get_cars_per_lane('A Road', car_spacing)
            road['cars_per_lane'] = int(round(int(road['length_km']) * cars_per_lane, 0))

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

            cars_per_lane = _get_cars_per_lane('B Road', car_spacing)
            road['cars_per_lane'] = int(round(int(road['length_km']) * cars_per_lane, 0))

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

            cars_per_lane = _get_cars_per_lane('Minor Road', car_spacing)
            road['cars_per_lane'] = int(round(int(road['length_km']) * cars_per_lane, 0))

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

            cars_per_lane = _get_cars_per_lane('Local Road', car_spacing)
            road['cars_per_lane'] = int(round(int(road['length_km']) * cars_per_lane, 0))

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

            road['cars_per_lane'] = int(round(int(road['length_km']) * 0.005, 0))

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

def _get_cars_per_lane(road_function, car_spacing):

    if road_function == 'Dense Motorway' and car_spacing == 'high':
        cars = 20
    if road_function == 'Dense Motorway' and car_spacing == 'baseline':
        cars = 15
    if road_function == 'Dense Motorway' and car_spacing == 'low':
        cars = 10
    if road_function == 'Motorway' and car_spacing == 'high':
        cars = 10
    if road_function == 'Motorway' and car_spacing == 'baseline':
        cars = 8
    if road_function == 'Motorway' and car_spacing == 'low':
        cars = 5
    if road_function == 'A Road' and car_spacing == 'high':
        cars = 8
    if road_function == 'A Road' and car_spacing == 'baseline':
        cars = 5
    if road_function == 'A Road' and car_spacing == 'low':
        cars = 3
    if road_function == 'B Road' and car_spacing == 'high':
        cars = 4
    if road_function == 'B Road' and car_spacing == 'baseline':
        cars = 3
    if road_function == 'B Road' and car_spacing == 'low':
        cars = 2
    if road_function == 'Minor Road' and car_spacing == 'high':
        cars = 4
    if road_function == 'Minor Road' and car_spacing == 'baseline':
        cars = 3
    if road_function == 'Minor Road' and car_spacing == 'low':
        cars = 2
    if road_function == 'Local Road' and car_spacing == 'high':
        cars = 3
    if road_function == 'Local Road' and car_spacing == 'baseline':
        cars = 2
    if road_function == 'Local Road' and car_spacing == 'low':
        cars = 1

    return cars

def road_spacing_value(car_spacing):

    if car_spacing == 'high':
        wtp_or_mbps = 10
    elif car_spacing == 'baseline':
        wtp_or_mbps = 4
    elif car_spacing == 'low':
        wtp_or_mbps = 1
    
    return wtp_or_mbps

def s_curve_function(year, start, end, inflection, takeover, curviness):
    
    return start + (end - start) / (1 + curviness ** ((inflection + takeover / 2-(year-2019))/takeover))


def calculate_yearly_CAV_take_up(data, year, scenario):

    for road in data:
        if road['total_cars'] > 0:  
            road['annual_CAV_take_up'] = round(road['total_cars'] * s_curve_function(year, 0, 0.75, 3, 6, 500), 0)
        else:
            road['annual_CAV_take_up'] = 0

    wtp_per_user = _get_scenario_wtp_and_data_value(scenario)

    for road in data:
        if road['annual_CAV_take_up'] > 0:
            road['CAV_revenue'] = road['annual_CAV_take_up'] * (wtp_per_user * 12)
        else:
            road['CAV_revenue'] = 0

    mbps_per_vehicle = _get_scenario_wtp_and_data_value(scenario)

    for road in data:
        
        if road['annual_CAV_take_up'] > 0:
            road['CAV_mbps_demand'] = road['annual_CAV_take_up'] * (mbps_per_vehicle)
        else:
            road['CAV_mbps_demand'] = 0

    return data

def _get_scenario_wtp_and_data_value(scenario):

    """treat wtp and data demand as correlated.
       so, 10 Mbps is £10 per month.
    """

    if scenario == 'high':
        wtp_or_mbps = 10
    elif scenario == 'baseline':
        wtp_or_mbps = 4
    elif scenario == 'low':
        wtp_or_mbps = 1
    
    return wtp_or_mbps

def calculate_backhaul_costs(data, deployment_period, year, strategy, fibre_tco):
    """
    cost of full deployment split over the length of the deployment_period
    """   
    if BASE_YEAR <= year < (BASE_YEAR + deployment_period):  
        for road in data:
            road['fibre_backhaul_km'] = road['length_km']  
        if strategy == 'DSRC_NRTS_greenfield':
            backhaul_shortening_factor = 0.5
            for road in data:
                road['fibre_backhaul_cost'] = int(round((int(road['fibre_backhaul_km']) * backhaul_shortening_factor) *  int(fibre_tco) / deployment_period, 0))
        else:
            for road in data:
                road['fibre_backhaul_cost'] = int(round(int(road['fibre_backhaul_km']) * int(fibre_tco) / deployment_period, 0))
        for road in data:
            road['total_tco'] = int(round(road['RAN_cost'] + road['small_cell_mounting_cost'] + int(road['fibre_backhaul_cost']), 0)) 
    else:
        for road in data:
            road['fibre_backhaul_km'] = 0
        for road in data:
            road['fibre_backhaul_cost'] = 0
        for road in data:
            road['total_tco'] = 0

    return data

#####################################
# write out 
#####################################

def write_spend(data, year, scenario, strategy, car_spacing):
    suffix = _get_suffix(scenario, strategy, car_spacing)
    filename = os.path.join(SYSTEM_RESULTS_PATH, 'spend_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        spend_file = open(filename, 'w', newline='')
        spend_writer = csv.writer(spend_file)
        spend_writer.writerow(
            ('year', 'scenario', 'strategy', 'car_spacing',
             'road','road_function','formofway', 'length_km','urban_rural', 
             'cars_per_lane', 'total_cars', 'annual_CAV_take_up','CAV_revenue', 'CAV_mbps_demand',
             'RAN_units','RAN_cost','small_cell_mounting_points','small_cell_mounting_cost', 
             'fibre_backhaul_km', 'fibre_backhaul_cost', 'total_tco'))
    else:
        spend_file = open(filename, 'a', newline='')
        spend_writer = csv.writer(spend_file)

    # output and report results for this timestep
    for road in data:
        spend_writer.writerow(
            (year, scenario, strategy, car_spacing, 
            road['road'], road['road_function'], road['formofway'], road['length_km'], road['urban_rural'], 
            road['cars_per_lane'], road['total_cars'], road['annual_CAV_take_up'], road['CAV_revenue'], road['CAV_mbps_demand'],
            road['RAN_units'], road['RAN_cost'], road['small_cell_mounting_points'],road['small_cell_mounting_cost'], 
            road['fibre_backhaul_km'], road['fibre_backhaul_cost'], road['total_tco']))

def _get_suffix(scenario, strategy, car_spacing):
    suffix = 'scenario_{}_strategy_{}_car_spacing_{}'.format(scenario, strategy, car_spacing)
    return suffix

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
# write_shapefile(road_network, SYSTEM_OUTPUT_PATH, 'road_network.shp')
# # # #####################################

# print('read in road network')
# road_network = import_shapes(os.path.join(SYSTEM_OUTPUT_PATH, 'road_network.shp'))

# print("extracting geojson properties")
# aggegated_road_statistics = extract_geojson_properties(road_network)

# print("applying grouped aggregation")
# aggegated_road_statistics = grouper(aggegated_road_statistics, 'length', 'road', 'function', 'formofway', 'urban_rural_indicator')

# print('write all road statistics')
# road_statistics_fieldnames = ['road', 'function', 'formofway', 'length', 'urban_rural_indicator']
# csv_writer(aggegated_road_statistics, road_statistics_fieldnames, 'aggregated_road_statistics.csv')

#####################################
# run functions
#####################################

DEPLOYMENT_PERIOD = 4

print("reading in aggregated road geotype data")
road_geotype_data = read_in_csv_road_geotype_data('aggregated_road_statistics.csv')

print("calculating tco costs")
small_cell_tco = calculate_tco_for_each_asset(2500, 350, 0.035, 2019, 2020, 10, 2029, 'no') 
small_cell_civil_works_tco = calculate_tco_for_each_asset(13300, 0, 0.035, 2019, 2020, 0, 2029, 'no')
fibre_tco_per_km = calculate_tco_for_each_asset(20000, 20, 0.035, 2019, 2020, 0, 2029, 'no') 

print('running scenarios')
for scenario, strategy, car_spacing in [
        ('high', 'DSRC_full_greenfield', 'high'),
        ('baseline', 'DSRC_full_greenfield', 'baseline'),
        ('low', 'DSRC_full_greenfield', 'low'),

        ('high', 'DSRC_NRTS_greenfield', 'high'),
        ('baseline', 'DSRC_NRTS_greenfield', 'baseline'),
        ('low', 'DSRC_NRTS_greenfield', 'low'),

        ('high', 'cellular_V2X', 'high'),
        ('baseline', 'cellular_V2X', 'baseline'),
        ('low', 'cellular_V2X', 'low'),
    ]:

    print("Running:", scenario, strategy, car_spacing)

    #if strategy == 'DSRC_full_greenfield' or strategy == 'DSRC_NRTS_greenfield':
        
    for year in TIMESTEPS:

        print("-", year)
        
        road_geotype_data = calculate_potential_demand(road_geotype_data, 5, car_spacing)
        
        road_geotype_data = calculate_yearly_CAV_take_up(road_geotype_data, year, scenario)
        
        road_geotype_data = calculate_number_of_RAN_units_and_civil_works_costs(road_geotype_data, DEPLOYMENT_PERIOD, year, scenario, strategy, small_cell_tco, small_cell_civil_works_tco, 2)
        
        road_geotype_data = calculate_backhaul_costs(road_geotype_data, DEPLOYMENT_PERIOD, year, strategy, fibre_tco_per_km)

        write_spend(road_geotype_data, year, scenario, strategy, car_spacing)


end = time.time()
print("script finished")
print("script took {} minutes to complete".format(round((end - start)/60, 0))) 

