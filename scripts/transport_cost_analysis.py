import os
from pprint import pprint
import configparser
import csv
import numpy as np

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# setup yearly increments
#####################################

BASE_YEAR = 2020
END_YEAR = 2029
TIMESTEP_INCREMENT = 1
TIMESTEPS = range(BASE_YEAR, END_YEAR + 1, TIMESTEP_INCREMENT)

#####################################
# setup scenarios
#####################################

# SCENARIOS = [
#     "DSRC_full_greenfield",
#     "DSRC_NRTS_greenfield",
# ]

# CELL_SPACING = [
#     200,
#     800,
#     2000
# ]

#####################################
# setup file locations and data files
#####################################

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
                'function': line[1],
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
        if road['function'] == 'Motorway': 
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

        elif road['function'] == 'A Road': 
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

        elif road['function'] == 'B Road': 
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

        elif road['function'] == 'Minor Road': 
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

        elif road['function'] == 'Local Road': 
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


def calculate_number_of_RAN_units_and_civil_works_costs(data, year, cell_spacing, cell_capex, cell_civil_works_capex):

    if BASE_YEAR <= year < 2024:  
        for road in data:
            road['RAN_units'] = int(round(int(road['length_meters']) / cell_spacing, 0))
        
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

def calculate_backhaul_costs(data, scenario, fibre_tco):
   
    if BASE_YEAR <= year < 2024:  
        for road in data:
            road['fibre_backhaul_meters'] = road['length_meters']  

        if scenario == 'DSRC_full_greenfield':
            for road in data:
                road['fibre_backhaul_cost'] = int(road['fibre_backhaul_meters']) *  fibre_tco

        if scenario == 'DSRC_NRTS_greenfield':
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

def write_spend(data, year, scenario, cell_spacing, car_spacing):
    suffix = _get_suffix(scenario, cell_spacing, car_spacing)
    filename = os.path.join(FILE_LOCATION, 'spend_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        spend_file = open(filename, 'w', newline='')
        spend_writer = csv.writer(spend_file)
        spend_writer.writerow(
            ('year', 'scenario', 'cell_spacing', 'car_spacing',
             'road','road_function','formofway', 'length_meters',
             'urban_rural', 'cars_per_lane', 'total_cars',
             'RAN_units','RAN_cost','small_cell_mounting_points','small_cell_mounting_cost', 
             'fibre_backhaul_meters', 'fibre_backhaul_cost', 'total_tco'))
    else:
        spend_file = open(filename, 'a', newline='')
        spend_writer = csv.writer(spend_file)

    # output and report results for this timestep
    for road in data:
        spend_writer.writerow(
            (year, scenario, cell_spacing, car_spacing, 
            road['road'], road['function'], road['formofway'], road['length_meters'], 
            road['urban_rural'], road['cars_per_lane'], road['total_cars'],
            road['RAN_units'], road['RAN_cost'], road['small_cell_mounting_points'],road['small_cell_mounting_cost'], 
            road['fibre_backhaul_meters'], road['fibre_backhaul_cost'], road['total_tco']))

def _get_suffix(scenario, cell_spacing, car_spacing):
    suffix = 'scenario_{}_cell_spacing_{}_car_spacing{}'.format(scenario, cell_spacing, car_spacing)
    return suffix

#####################################
# run functions
#####################################

print("reading in aggregated road geotype data")
road_geotype_data = read_in_csv_road_geotype_data('aggregated_road_statistics.csv')

print("calculating tco costs")
small_cell_tco = calculate_tco_for_each_asset(2500, 350, 0.035, 2019, 2020, 5, 2029, 'yes') 
small_cell_civil_works_tco = calculate_tco_for_each_asset(13300, 0, 0.035, 2019, 2020, 0, 2029, 'no')
fibre_tco_per_meter = calculate_tco_for_each_asset(10, 0.6, 0.035, 2019, 2020, 0, 2029, 'no') 

print('running scenarios')
for scenario, cell_spacing, car_spacing in [
        ('DSRC_full_greenfield', 200, 15),
        ('DSRC_full_greenfield', 800, 30),
        ('DSRC_full_greenfield', 2000, 60),

        ('DSRC_NRTS_greenfield', 200, 15),
        ('DSRC_NRTS_greenfield', 800, 30),
        ('DSRC_NRTS_greenfield', 2000, 60),

    ]:
    print("Running:", scenario, cell_spacing, car_spacing)

    for year in TIMESTEPS:
        
        road_geotype_data = calculate_potential_demand(road_geotype_data, 5, car_spacing)

        road_geotype_data = calculate_number_of_RAN_units_and_civil_works_costs(road_geotype_data, year, cell_spacing, small_cell_tco, small_cell_civil_works_tco)

        road_geotype_data = calculate_backhaul_costs(road_geotype_data, scenario, fibre_tco_per_meter)

        write_spend(road_geotype_data, year, scenario, cell_spacing, car_spacing)






