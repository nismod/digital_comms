import os
from pprint import pprint
import configparser
import csv
import numpy as np
from math import exp

from itertools import groupby
from operator import itemgetter

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# setup yearly increments
#####################################

BASE_YEAR = 2020
END_YEAR = 2021
TIMESTEP_INCREMENT = 1
TIMESTEPS = range(BASE_YEAR, END_YEAR + 1, TIMESTEP_INCREMENT)

#####################################
# setup file locations and data files
#####################################

RAW_DATA = os.path.join(BASE_PATH, 'raw')
FILE_LOCATION = os.path.join(BASE_PATH, 'processed')

#####################################
# setup file locations and data files
#####################################

def read_in_csv_road_geotype_data(data):

    road_type_data = []

    with open(os.path.join(FILE_LOCATION, data), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            road_type_data.append({
                'road': line[0],
                'road_function': line[1],
                'formofway': line[2],
                'urban_rural': line[3],
                'length_meters': line[4]
            })   

    return road_type_data

#####################################
# demand estimation
#####################################

def calculate_potential_demand(data, car_length, car_spacing):

    for road in data:
        road['cars_per_lane'] = int(round(int(road['length_meters']) / (car_length + car_spacing), 0))

    for road in data:
        if road['road_function'] == 'Motorway': 
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


def s_curve_function(year, start, end, inflection, takeover, curviness):
    
    return start + (end - start) / (1 + curviness ** ((inflection + takeover / 2-(year-2019))/takeover))


def calculate_yearly_CAV_take_up(data, year, scenario):

    for road in data:
        road['annual_CAV_take_up'] = round(road['total_cars'] * s_curve_function(year, 0, 0.75, 3, 6, 500), 0)

    wtp_per_user = _get_scenario_wtp_and_data_value(scenario)

    for road in data:
        road['CAV_revenue'] = road['annual_CAV_take_up'] * (wtp_per_user * 12)

    mbps_per_vehicle = _get_scenario_wtp_and_data_value(scenario)

    for road in data:
        road['CAV_mbps_demand'] = road['annual_CAV_take_up'] * (mbps_per_vehicle)

    return data

def _get_scenario_wtp_and_data_value(scenario):

    """treat wtp and data demand as correlated.
       so, 10 Mbps is £10 per month.
    """

    if scenario == 'high':
        spacing_or_mbps = 10

    elif scenario == 'baseline':
        spacing_or_mbps = 4

    elif scenario == 'low':
        spacing_or_mbps = 1
    
    return spacing_or_mbps

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

    #print("capex over {} - {} with an asset lifetime of {} years is £{}".format(year_deployed, end_year, asset_lifetime, total_capex))

    my_opex = []

    for i in range(10):

        total_opex = int(round(opex / (1 + discount_rate) ** ((year_deployed - current_year) + (i+1)), 0)) 

        my_opex.append(total_opex)

    #print("opex over {} - {} is £{}".format(year_deployed, end_year, sum(my_opex)))

    total_cost_of_ownership = total_capex + sum(my_opex)

    #print("tco over {} - {} is £{}".format(year_deployed, end_year, total_cost_of_ownership))

    return total_cost_of_ownership


def calculate_number_of_RAN_units_and_civil_works_costs(data, year, scenario, cell_capex, cell_civil_works_capex):

    cell_spacing = _get_scenario_spacing_value(scenario)

    if BASE_YEAR <= year < 2024:  
        for road in data:
            road['RAN_units'] = int(round(int(road['length_meters']) / int(cell_spacing), 0))
        
        for road in data:
            road['RAN_cost'] = road['RAN_units'] * cell_capex

        for road in data:
            road['small_cell_mounting_points'] = int(road['RAN_units'] / 2)

        for road in data:
            road['small_cell_mounting_cost'] = road['small_cell_mounting_points'] * cell_civil_works_capex
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

def _get_scenario_spacing_value(scenario):
        
    if scenario == 'high':
        spacing = 200

    elif scenario == 'baseline':
        spacing = 800

    elif scenario == 'low':
        spacing = 2000
    
    return spacing

def calculate_backhaul_costs(data, strategy, fibre_tco):
   
    if BASE_YEAR <= year < 2024:  
        for road in data:
            road['fibre_backhaul_meters'] = road['length_meters']  

        if strategy == 'DSRC_full_greenfield':
            for road in data:
                road['fibre_backhaul_cost'] = int(road['fibre_backhaul_meters']) *  fibre_tco

        if strategy == 'DSRC_NRTS_greenfield':
            for road in data:
                road['fibre_backhaul_cost'] = (int(road['fibre_backhaul_meters'])/4) *  fibre_tco

        for road in data:
            road['total_tco'] = int(round(road['RAN_cost'] + road['small_cell_mounting_cost'] + road['fibre_backhaul_cost'], 0))
    
    else:
        for road in data:
            road['fibre_backhaul_meters'] = 0

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
    filename = os.path.join(FILE_LOCATION, 'spend_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        spend_file = open(filename, 'w', newline='')
        spend_writer = csv.writer(spend_file)
        spend_writer.writerow(
            ('year', 'scenario', 'strategy', 'car_spacing',
             'road','road_function','formofway', 'length_meters','urban_rural', 
             'cars_per_lane', 'total_cars', 'annual_CAV_take_up','CAV_revenue', 'CAV_mbps_demand',
             'RAN_units','RAN_cost','small_cell_mounting_points','small_cell_mounting_cost', 
             'fibre_backhaul_meters', 'fibre_backhaul_cost', 'total_tco'))
    else:
        spend_file = open(filename, 'a', newline='')
        spend_writer = csv.writer(spend_file)

    # output and report results for this timestep
    for road in data:
        spend_writer.writerow(
            (year, scenario, strategy, car_spacing, 
            road['road'], road['road_function'], road['formofway'], road['length_meters'], road['urban_rural'], 
            road['cars_per_lane'], road['total_cars'], road['annual_CAV_take_up'], road['CAV_revenue'], road['CAV_mbps_demand'],
            road['RAN_units'], road['RAN_cost'], road['small_cell_mounting_points'],road['small_cell_mounting_cost'], 
            road['fibre_backhaul_meters'], road['fibre_backhaul_cost'], road['total_tco']))

def _get_suffix(scenario, strategy, car_spacing):
    suffix = 'scenario_{}_strategy_{}_car_spacing{}'.format(scenario, strategy, car_spacing)
    return suffix

#####################################
# run functions
#####################################

# print("reading in aggregated road geotype data")
# road_geotype_data = read_in_csv_road_geotype_data('aggregated_road_statistics.csv')

# print("calculating tco costs")
# small_cell_tco = calculate_tco_for_each_asset(2500, 350, 0.035, 2019, 2020, 5, 2029, 'yes') 
# small_cell_civil_works_tco = calculate_tco_for_each_asset(13300, 0, 0.035, 2019, 2020, 0, 2029, 'no')
# fibre_tco_per_meter = calculate_tco_for_each_asset(10, 0.6, 0.035, 2019, 2020, 0, 2029, 'no') 

# print('running scenarios')
# for scenario, strategy, car_spacing in [
#         ('high', 'DSRC_full_greenfield', 15),
#         ('baseline', 'DSRC_full_greenfield', 30),
#         ('low', 'DSRC_full_greenfield', 60),

#         ('high', 'DSRC_NRTS_greenfield', 15),
#         ('baseline', 'DSRC_NRTS_greenfield', 30),
#         ('low', 'DSRC_NRTS_greenfield', 60),
#     ]:

#     print("Running:", scenario, strategy, car_spacing)

#     for year in TIMESTEPS:
        
#         #for DSRC 5.9GHz
#         road_geotype_data = calculate_potential_demand(road_geotype_data, 5, car_spacing)

#         road_geotype_data = calculate_yearly_CAV_take_up(road_geotype_data, year, scenario)

#         road_geotype_data = calculate_number_of_RAN_units_and_civil_works_costs(road_geotype_data, year, scenario, small_cell_tco, small_cell_civil_works_tco)

#         road_geotype_data = calculate_backhaul_costs(road_geotype_data, strategy, fibre_tco_per_meter)

#         write_spend(road_geotype_data, year, scenario, strategy, car_spacing)
        

#Cellular V2X 3GPP 
        
#####################################
# 
#####################################

def read_in_road_geotype_data(data):

    road_type_data = []

    with open(os.path.join(FILE_LOCATION, data), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            road_type_data.append({
                
                'pcd_sector': line[0],
                'road_function': line[1],
                'formofway': line[2],
                'urban_rural': line[3],
                'length_meters': line[4]
            })   

    return road_type_data

def read_in_cell_densities(data):

    cell_data = []

    with open(os.path.join(FILE_LOCATION, data), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            if line[0] != 'not in pcd_sector' and line[2] != 'not available':
                cell_data.append({
                    'pcd_sector': line[0],
                    'cells': int(line[1]),
                    'site_density': round((int(line[1])/3),0),
                    'area': float(line[2]),
                    'density': round((int(line[1])/3)/float(line[2]),3)
                })   

    return cell_data

def aggregator(data, aggregated_metric, group_item1, group_item2):

    my_grouper = itemgetter(group_item1, group_item2)
    result = []
    for key, grp in groupby(sorted(data, key = my_grouper), my_grouper):
        try:
            temp_dict = dict(zip([group_item1, group_item2], key))
            temp_dict[aggregated_metric] = sum(int(item[aggregated_metric]) for item in grp)
            result.append(temp_dict)
        except:
            pass
    
    return result

def read_in_population_estimates(data, year):

    pcd_sector_population_data = []

    with open(os.path.join(RAW_DATA, 'mobile_model_1.0', 'scenario_data', data), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for line in reader:
            if int(line[0]) == year:
                pcd_sector_population_data.append({
                    'pcd_sector': line[1],
                    'population': int(line[2])
                })   

    return pcd_sector_population_data

def get_annual_user_demand(data, year):

    with open(os.path.join(RAW_DATA, 'mobile_model_1.0', 'scenario_data', data), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            if int(line[0]) == year:
                user_demand = float(line[1])

    return user_demand

def calc_pcd_sector_baseline_demand(population_data, monthly_demand):

    #mbps = GB * 1024 * 8 * (1/days) * % busy hour/100 * 1/3600
    hourly_demand = monthly_demand * 1024 * 8 * (1/30) * (15/100) * (1/3600)

    for pcd_sector in population_data:

        pcd_sector['base_demand'] = float(round(pcd_sector['population'] * hourly_demand, 1))

    return population_data

def merge_two_lists_of_dicts(msoa_list_of_dicts, oa_list_of_dicts, parameter1, parameter2):
    """
    Combine the msoa and oa dicts using the household indicator and year keys. 
    """
    d1 = {(d[parameter1], d[parameter2]):d for d in oa_list_of_dicts}

    msoa_list_of_dicts = [dict(d, **d1.get((d[parameter1], d[parameter2]), {})) for d in msoa_list_of_dicts]	

    return msoa_list_of_dicts

def deal_with_missing_population(data):
    
    my_data = []
    missing_data = []

    for datum in data:
        if 'population' and 'base_demand' in datum:
            my_data.append({
                'pcd_sector': datum['pcd_sector'],
                #'road_function': datum['road_function'],
                #'formofway': datum['formofway'],
                #'urban_rural': datum['urban_rural'],
                #'length_meters': datum['length_meters'],
                #'cars_per_lane': datum['cars_per_lane'],
                'total_cars': datum['total_cars'],
                'annual_CAV_take_up': datum['annual_CAV_take_up'],
                'CAV_revenue': datum['CAV_revenue'],
                'CAV_mbps_demand': datum['CAV_mbps_demand'],
                'population': datum['population'],
                'base_demand': datum['base_demand'],
            })
        else:
            missing_data.append({
                'pcd_sector': datum['pcd_sector'],
            })
    
    if len(missing_data) > 0: 
        print("THOWING AWAY NON COMPLETE POPULATION DATA")

    return my_data

def deal_with_missing_cells(data):

    my_data = []
    missing_data = []

    for datum in data:
        if 'cells' and 'area' and 'density' in datum:
            my_data.append({
                'pcd_sector': datum['pcd_sector'],
                #'road_function': datum['road_function'],
                #'formofway': datum['formofway'],
                #'urban_rural': datum['urban_rural'],
                #'length_meters': datum['length_meters'],
                #'cars_per_lane': datum['cars_per_lane'],
                'total_cars': datum['total_cars'],
                'annual_CAV_take_up': datum['annual_CAV_take_up'],
                'CAV_revenue': datum['CAV_revenue'],
                'CAV_mbps_demand': datum['CAV_mbps_demand'],
                'population': datum['population'],              
                'base_demand': datum['base_demand'],
                'cells': datum['cells'],
                'site_density': datum['site_density'],
                'area': datum['area'],
                'density': datum['density'],
            })

        else:
            missing_data.append({
                'pcd_sector': datum['pcd_sector'],
            })
    
    if len(missing_data) > 0: 
        print("THOWING AWAY NON COMPLETE CELLS DATA")

    return my_data

def read_in_capacity_lut(data):

    capacity_lut_data = []

    with open(os.path.join(RAW_DATA, 'mobile_model_1.0', 'lookup_tables', data), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for line in reader:
            if line[1] == '3500 MHz':
                capacity_lut_data.append({
                    'site_density': float(line[3]),   #load in site_density
                    'capacity': float(line[4])
                    })  #load in capacity

    return capacity_lut_data

def get_pcd_sector_capacity(data, lut):

    for datum in data:            
        try:
            closest = {'site_density': float('inf'), 'capacity': None}
            for l in lut:
                if abs(l['site_density'] - datum['site_density']) < abs(closest['site_density'] - datum['site_density']):
                    closest = l
            datum['capacity'] = closest['capacity']

        except:
            datum['capacity'] = 0 

    return data

def build_new_sites(data, lut):

    for datum in data:                 
        try:
            closest = {'site_density': float('inf'), 'demand': None}
            for l in lut:
                if abs(l['site_density'] - datum['CAV_mbps_demand']) < abs(closest['site_density'] - datum['CAV_mbps_demand']):
                    closest = l
            datum['new_density'] = closest['site_density']
        
        except:
            datum['new_density'] = 0        

    for datum in data:
        total_sites = datum['new_density'] * datum['area']
        datum['new_sites'] = total_sites - datum['site_density']

    return data

def calculate_cost_of_new_assets(data, macrocell_asset_tco):

    for datum in data:
        datum['new_macro_cost'] = round(datum['new_sites'] * macrocell_asset_tco, 0)

        datum['total_tco'] = float(round(datum['new_macro_cost'], 0)) 

    return data

def transfer_cost_from_pcd_sector_to_road_type(pcd_sector_data, road_data):

    road_cost_data = []

    for road in road_data:
        for datum in pcd_sector_data:
            if road['pcd_sector'] == datum['pcd_sector']:
                if datum['total_tco'] > 0:
                    try: 
                        cost_per_car = float(datum['total_tco']) / float(datum['total_cars'])
                        road['total_tco'] = float(road['total_cars']) * cost_per_car
                    except:
                        pass
                elif datum['total_tco'] == 0:
                    road['total_tco'] = 0
                else:
                    road['total_tco'] = 0
                
                road_cost_data.append({
                    'pcd_sector': road['pcd_sector'],
                    'road_function': road['road_function'],
                    'formofway': road['formofway'],
                    'urban_rural': road['urban_rural'],
                    'length_meters': road['length_meters'],
                    'cars_per_lane': road['cars_per_lane'],
                    'total_cars': road['total_cars'],
                    'total_tco': road['total_tco']
                })
    
    return road_cost_data

def deal_with_missing_road(data):

    my_data = []
    missing_data = []

    for datum in data:
        if 'total_tco' in datum:
            my_data.append({
                'pcd_sector': datum['pcd_sector'],
                'road_function': datum['road_function'],
                'formofway': datum['formofway'],
                'urban_rural': datum['urban_rural'],
                'length_meters': datum['length_meters'],
                'cars_per_lane': datum['cars_per_lane'],
                'total_cars': datum['total_cars'],
                'total_tco': datum['total_tco'],
            })

        else:
            missing_data.append({
                'pcd_sector': datum['pcd_sector'],
            })
    
    if len(missing_data) > 0: 
        print("THOWING AWAY NON COMPLETE ROAD COST DATA")

    return my_data

#####################################
# WRITE OUT CELLULAR SPEND BY PCD SECTOR
#####################################

def write_cellular_spend(data, year, scenario, strategy, car_spacing):
    suffix = _get_suffix(scenario, strategy, car_spacing)
    filename = os.path.join(FILE_LOCATION, 'spend_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        spend_file = open(filename, 'w', newline='')
        spend_writer = csv.writer(spend_file)
        spend_writer.writerow(
            ('year', 'scenario', 'strategy', 'car_spacing',
             'pcd_sector', 'total_cars', 'annual_CAV_take_up','CAV_revenue', 'CAV_mbps_demand',
             'population','base_demand',
             'cells','site_density', 'area', 'density', 
             'capacity', 'new_density', 'new_sites', 'new_macro_cost', 'total_tco'))

    else:
        spend_file = open(filename, 'a', newline='')
        spend_writer = csv.writer(spend_file)

    # output and report results for this timestep
    for road in data:
        spend_writer.writerow(
            (year, scenario, strategy, car_spacing, 
            road['pcd_sector'], road['total_cars'], road['annual_CAV_take_up'], 
            road['CAV_revenue'], road['CAV_mbps_demand'],
            road['population'], road['base_demand'], 
            road['cells'], road['site_density'], road['area'], road['density'], 
            road['capacity'], road['new_density'], road['new_sites'], road['new_macro_cost'], road['total_tco']))

#####################################
# WRITE OUT CELLULAR SPEND BY ROAD
#####################################

def write_cellular_spend_by_road(data, year, scenario, strategy, car_spacing):
    suffix = _get_suffix(scenario, strategy, car_spacing)
    filename = os.path.join(FILE_LOCATION, 'road_spend_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        spend_file = open(filename, 'w', newline='')
        spend_writer = csv.writer(spend_file)
        spend_writer.writerow(
            ('year', 'scenario', 'strategy', 'car_spacing',
             'road_function', 'urban_rural', 'total_tco'))
    else:
        spend_file = open(filename, 'a', newline='')
        spend_writer = csv.writer(spend_file)

    # output and report results for this timestep
    for road in data:
        spend_writer.writerow(
            (year, scenario, strategy, car_spacing, 
            road['road_function'], road['urban_rural'],  road['total_tco']))

def _get_suffix(scenario, strategy, car_spacing):
    suffix = 'scenario_{}_strategy_{}_car_spacing{}'.format(scenario, strategy, car_spacing)
    return suffix

#####################################
# run functions
#####################################

print("reading in road by pcd_sector data")
road_by_pcd_sectors = read_in_road_geotype_data('pcd_sector_road_length_by_type.csv')

print("reading in cell densities by pcd_sector data")
cell_densities = read_in_cell_densities('pcd_sector_cell_densities.csv')

print("reading in capacity lut")
capacity_lut = read_in_capacity_lut('lookup_table_long.csv')

print("calculating tco costs")
macrocell_tco = calculate_tco_for_each_asset(110000, 1000, 0.035, 2019, 2020, 10, 2029, 'no') 

print('running scenarios')
for scenario, strategy, car_spacing in [
        ('high', 'cellular_V2X', 15),
        ('baseline', 'cellular_V2X', 30),
        ('low', 'cellular_V2X', 60),
    ]:

    print("Running:", scenario, strategy, car_spacing)

    for year in TIMESTEPS:
        
        print("-", year)
        
        all_roads_pcd_demand = calculate_potential_demand(road_by_pcd_sectors, 5, car_spacing)

        pcd_sector_road_demand = aggregator(all_roads_pcd_demand,'total_cars','pcd_sector','pcd_sector')

        pcd_sector_road_demand = calculate_yearly_CAV_take_up(pcd_sector_road_demand, year, scenario)

        pcd_sector_population = read_in_population_estimates('population_baseline_pcd.csv', year)

        user_demand = get_annual_user_demand('monthly_data_growth_scenarios.csv', year)

        baseline_demand = calc_pcd_sector_baseline_demand(pcd_sector_population, user_demand)

        pcd_sector_data = merge_two_lists_of_dicts(pcd_sector_road_demand, baseline_demand, 'pcd_sector', 'pcd_sector')

        pcd_sector_data = deal_with_missing_population(pcd_sector_data)

        pcd_sector_data = merge_two_lists_of_dicts(pcd_sector_data, cell_densities, 'pcd_sector', 'pcd_sector')

        pcd_sector_data = deal_with_missing_cells(pcd_sector_data)

        pcd_sector_data = get_pcd_sector_capacity(pcd_sector_data, capacity_lut)

        pcd_sector_data = build_new_sites(pcd_sector_data, capacity_lut)

        pcd_sector_data = calculate_cost_of_new_assets(pcd_sector_data, macrocell_tco)

        cost_by_road_type = transfer_cost_from_pcd_sector_to_road_type(pcd_sector_data, all_roads_pcd_demand)

        cost_by_road_type = deal_with_missing_road(cost_by_road_type)

        cost_by_road_type = aggregator(cost_by_road_type,'total_tco','road_function','urban_rural')

        write_cellular_spend_by_road(cost_by_road_type, year, scenario, strategy, car_spacing)

        write_cellular_spend(pcd_sector_data, year, scenario, strategy, car_spacing)
        








