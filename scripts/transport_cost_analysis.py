import os
from pprint import pprint
import configparser
import csv
import numpy as np
from math import exp

from itertools import groupby, product
from operator import itemgetter

from digital_comms.mobile_network.model import pairwise, interpolate

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
                'length_km': (int(line[4])/1000)
            })   

    return road_type_data

#####################################
# demand estimation
#####################################

def calculate_potential_demand(data, car_length, car_spacing):

    # for road in data:
    #     road['cars_per_lane'] = int(round(int(road['length_km']) / (car_length + car_spacing), 0))

    for road in data:
        if road['road_function'] == 'Motorway': 

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


def calculate_number_of_RAN_units_and_civil_works_costs(data, deployment_period, year, scenario, strategy, cell_capex, cell_civil_works_capex, cells_per_mounting):

    cell_spacing = _get_scenario_cell_spacing_value(scenario, strategy)

    if BASE_YEAR <= year < (BASE_YEAR + deployment_period):  
        for road in data:
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

def _get_scenario_cell_spacing_value(scenario, strategy):
    
    if strategy == 'cellular_V2X':
        if scenario == 'high':
            spacing = 0.4

        elif scenario == 'baseline':
            spacing = 0.8

        elif scenario == 'low':
            spacing = 1
    
    else:
        if scenario == 'high':
            spacing = 0.2

        elif scenario == 'baseline':
            spacing = 0.4

        elif scenario == 'low':
            spacing = 0.5
    
    return spacing

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
# Cellular V2X 3GPP 
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
                'length_km': round((float(line[4])/1600),0)
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
                    #'cell_density': round((int(line[1])),0),
                    'area': float(line[2]),
                    'site_density': round((int(line[1])/3)/float(line[2]),3)
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
                #'length_km': datum['length_km'],
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
        if 'cells' and 'area' and 'site_density' in datum:
            my_data.append({
                'pcd_sector': datum['pcd_sector'],
                #'road_function': datum['road_function'],
                #'formofway': datum['formofway'],
                #'urban_rural': datum['urban_rural'],
                #'length_km': datum['length_km'],
                #'cars_per_lane': datum['cars_per_lane'],
                'total_cars': datum['total_cars'],
                'annual_CAV_take_up': datum['annual_CAV_take_up'],
                'CAV_revenue': datum['CAV_revenue'],
                'CAV_mbps_demand': datum['CAV_mbps_demand'],
                'population': datum['population'],              
                'base_demand': datum['base_demand'],
                'cells': datum['cells'],
                'area': datum['area'],
                'site_density': datum['site_density'],
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
            density_capacities = [(entry['site_density'], entry['capacity']) for entry in lut]
            density_capacities.sort(key=lambda lut: lut[0])

            lowest_density, lowest_capacity = density_capacities[0]
            if datum['site_density'] < lowest_density:
                # Never fail, return zero capacity if site density is below range
                datum['capacity'] = 0
            else:
                for a, b in pairwise(density_capacities):
                    lower_density, lower_capacity = a
                    upper_density, upper_capacity = b
                    if lower_density <= datum['site_density'] and datum['site_density'] < upper_density:
                        # Interpolate between values
                        datum['capacity'] = round(interpolate(lower_density, lower_capacity, upper_density, upper_capacity, datum['site_density']), 2)

            # If not caught between bounds return highest capacity
            if not 'capacity' in datum:
                highest_density, highest_capacity = density_capacities[-1]
                datum['capacity'] = round(highest_capacity, 2)

        except:
            datum['capacity'] = 0 

    return data

def upgrade_existing_sites(data, year, scenario, cell_tco, cell_civil_works_tco):

    if BASE_YEAR <= year < 2024:  
     
        for road in data:
            
            if road['site_density'] > 0:
            
                road['lte_site_upgrades'] = int(round((road['site_density'] * road['area']), 0)) 

                road['lte_upgrade_costs'] = int(round(road['lte_site_upgrades'] * cell_tco, 0))

            else:

                road['lte_site_upgrades'] = 0

                road['lte_upgrade_costs'] = 0

    else:

        for road in data:

            road['lte_upgrade_costs'] = 0
        
    return data


def build_new_sites(data, year, deployment_period, lut):

    if BASE_YEAR <= year < 2024:  

        for datum in data:            
            try:
                density_capacities = [(entry['site_density'], entry['capacity']) for entry in lut]
                density_capacities.sort(key=lambda lut: lut[0])
               
                lowest_density, lowest_capacity = density_capacities[0]
                if datum['CAV_mbps_demand'] < lowest_capacity:
                    # Never fail, return zero capacity if site density is below range
                    datum['new_density'] = 0
                else:
                    for a, b in pairwise(density_capacities):
                        lower_density, lower_capacity = a
                        upper_density, upper_capacity = b
                        if lower_capacity <= datum['CAV_demand'] and datum['CAV_demand'] < lower_capacity:
                            # Interpolate between values
                            datum['new_density'] = round(interpolate(lower_density, lower_capacity, upper_density, upper_capacity, datum['CAV_mbps_demand']), 2)

                # If not caught between bounds return highest capacity
                if not 'new_density' in datum:
                    highest_density, highest_capacity = density_capacities[-1]
                    datum['new_density'] = round(highest_capacity, 2)

                for datum in data:
                    total_sites = datum['new_density'] * datum['area']
                    datum['new_sites'] = int(round((total_sites - datum['site_density']) / deployment_period, 0))

            except:
                datum['new_density'] = 0 

    else:
        for datum in data:  
            datum['new_density'] = 0
            datum['new_sites'] = 0    

    return data

def calculate_cost_of_new_assets(data, deployment_period, macro_upgrade_tco, macro_civil_works_tco, fibre_cost_per_m):

    if BASE_YEAR <= year < 2024:  
        
        for datum in data:
            
            if datum['new_sites'] > 0:

                datum['new_sites_cost'] = int(round((datum['new_sites'] * macro_upgrade_tco), 0))

                datum['new_sites_civil_works_cost'] = int(round((datum['new_sites'] * macro_civil_works_tco), 0))

                datum['new_sites_backhaul_cost'] = int(round((datum['new_sites'] * fibre_cost_per_m * 1000), 0)) 

                datum['total_tco'] = int(round(datum['lte_upgrade_costs'] *  datum['new_sites_cost'] * datum['new_sites_civil_works_cost'] * datum['new_sites_backhaul_cost'],0))
            
            else:
                
                datum['new_sites_cost'] = 0

                datum['new_sites_civil_works_cost'] = 0

                datum['new_sites_backhaul_cost'] = 0

                datum['total_tco'] = 0
    else:

        for datum in data:

            datum['new_sites_cost'] = 0

            datum['new_sites_civil_works_cost'] = 0

            datum['new_sites_backhaul_cost'] = 0

            datum['total_tco'] = 0

    return data

def transfer_cost_from_pcd_sector_to_road_type(pcd_sector_data, road_data):

    road_cost_data = []
    missing_data =[]

    for road in road_data:
        for datum in pcd_sector_data:
            if road['pcd_sector'] == datum['pcd_sector']:
                try:
                    if datum['CAV_revenue'] > 0:
                        try: 
                            cost_per_car = float(datum['CAV_revenue']) / float(datum['total_cars'])
                            road['CAV_revenue'] = int(round(float(road['total_cars']) * cost_per_car,0))
                        except:
                            pass
                    elif datum['CAV_revenue'] == 0:
                        road['CAV_revenue'] = 0
                    else:
                        road['CAV_revenue'] = 0

                    if datum['lte_upgrade_costs'] > 0:
                        try: 
                            cost_per_car = float(datum['lte_upgrade_costs']) / float(datum['total_cars'])
                            road['lte_upgrade_costs'] = int(round(float(road['total_cars']) * cost_per_car,0))
                        except:
                            pass
                    elif datum['lte_upgrade_costs'] == 0:
                        road['lte_upgrade_costs'] = 0
                    else:
                        road['lte_upgrade_costs'] = 0
                    
                    if datum['new_sites_cost'] > 0:
                        try: 
                            cost_per_car = float(datum['new_sites_cost']) / float(datum['total_cars'])
                            road['new_sites_cost'] = int(round(float(road['total_cars']) * cost_per_car,0))
                        except:
                            pass
                    elif datum['new_sites_cost'] == 0:
                        road['new_sites_cost'] = 0
                    else:
                        road['new_sites_cost'] = 0

                    if datum['new_sites_civil_works_cost'] > 0:
                        try: 
                            cost_per_car = float(datum['new_sites_civil_works_cost']) / float(datum['total_cars'])
                            road['new_sites_civil_works_cost'] = int(round(float(road['total_cars']) * cost_per_car, 0))
                        except:
                            pass
                    elif datum['new_sites_civil_works_cost'] == 0:
                        road['new_sites_civil_works_cost'] = 0
                    else:
                        road['new_sites_civil_works_cost'] = 0
                    
                    if datum['new_sites_backhaul_cost'] > 0:
                        try: 
                            cost_per_car = float(datum['new_sites_backhaul_cost']) / float(datum['total_cars'])
                            road['new_sites_backhaul_cost'] = int(round(float(road['total_cars']) * cost_per_car,0))
                        except:
                            pass
                    elif datum['new_sites_backhaul_cost'] == 0:
                        road['new_sites_backhaul_cost'] = 0
                    else:
                        road['new_sites_backhaul_cost'] = 0

                    if datum['total_tco'] > 0:
                        try: 
                            cost_per_car = float(datum['total_tco']) / float(datum['total_cars'])
                            road['total_tco'] = int(round(float(road['total_cars']) * cost_per_car,0))
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
                        'length_km': road['length_km'],
                        'cars_per_lane': road['cars_per_lane'],
                        'total_cars': road['total_cars'],
                        'CAV_revenue': road['CAV_revenue'],
                        'lte_upgrade_costs': road['lte_upgrade_costs'],
                        'new_sites_cost': road['new_sites_cost'],
                        'new_sites_civil_works_cost': road['new_sites_civil_works_cost'],
                        'total_tco': road['total_tco']
                    })

                except:
                    missing_data.append({
                        'pcd_sector': road['pcd_sector']
                        })
    
    if len(missing_data) > 0: 
        print("THOWING AWAY NON COMPLETE DATA")

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
                'length_km': float(datum['length_km']),
                'cars_per_lane': datum['cars_per_lane'],
                'total_cars': datum['total_cars'],
                'CAV_revenue': datum['CAV_revenue'],
                'lte_upgrade_costs': datum['lte_upgrade_costs'],
                'new_sites_cost': datum['new_sites_cost'],
                'new_sites_civil_works_cost': datum['new_sites_civil_works_cost'],
                'total_tco': datum['total_tco'],
            })

        else:
            missing_data.append({
                'pcd_sector': datum['pcd_sector'],
            })
    
    if len(missing_data) > 0: 
        print("THOWING AWAY NON COMPLETE ROAD COST DATA")

    return my_data


def aggregate_costs_by_road_type(data):

    my_aggregated_data = []

    road_function = ['Motorway', 'A Road', 'B Road', 'Minor Road', 'Local Road']
    urban_rural=['urban', 'rural']

    combinations = list(product(road_function, urban_rural))

    for combi in combinations:
        data_combi = [entry for entry in data 
                    if entry['road_function'] == combi[0] and 
                        entry['urban_rural'] == combi[1]]
        
        my_aggregated_data.append({
            'road_function': combi[0],
            'urban_rural': combi[1],
            'CAV_revenue': sum(sector['CAV_revenue'] for sector in data_combi),
            'length_km': sum(sector['length_km'] for sector in data_combi),
            'lte_upgrade_costs': sum(sector['lte_upgrade_costs'] for sector in data_combi),
            'new_sites_cost': sum(sector['new_sites_cost'] for sector in data_combi),
            'new_sites_civil_works_cost': sum(sector['new_sites_civil_works_cost'] for sector in data_combi),
            'total_tco': sum(sector['total_tco'] for sector in data_combi)  
        })

    return my_aggregated_data


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
# WRITE OUT CELLULAR SPEND BY PCD SECTOR
#####################################

def write_cellular_spend(data, year, scenario, strategy, car_spacing):
    suffix = _get_suffix(scenario, strategy, car_spacing)
    filename = os.path.join(FILE_LOCATION, 'pcd_sector_spend_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        spend_file = open(filename, 'w', newline='')
        spend_writer = csv.writer(spend_file)
        spend_writer.writerow(
            ('year', 'scenario', 'strategy', 'car_spacing',
             'pcd_sector', 'total_cars', 'annual_CAV_take_up','CAV_revenue', 'CAV_mbps_demand',
             'population','base_demand',
             'cells', 'area', 'site_density',
             'capacity', 'new_density', 'new_sites', 
             'lte_upgrade_costs', 'new_sites_cost', 'new_sites_civil_works_cost', 'total_tco'))

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
            road['cells'], road['area'], road['site_density'], 
            road['capacity'], road['new_density'], road['new_sites'], 
            road['lte_upgrade_costs'], road['new_sites_cost'], road['new_sites_civil_works_cost'], road['total_tco']))

#####################################
# WRITE OUT CELLULAR SPEND BY ROAD
#####################################

def write_cellular_spend_by_road(data, year, scenario, strategy, car_spacing):
    suffix = _get_suffix(scenario, strategy, car_spacing)
    filename = os.path.join(FILE_LOCATION, 'cellular_road_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        spend_file = open(filename, 'w', newline='')
        spend_writer = csv.writer(spend_file)
        spend_writer.writerow(
            ('year', 'scenario', 'strategy', 'car_spacing',
             'road_function', 'urban_rural','length_km', 'CAV_revenue',
             'lte_upgrade_costs', 'new_sites_cost', 'new_sites_civil_works_cost', 'total_tco'))
    else:
        spend_file = open(filename, 'a', newline='')
        spend_writer = csv.writer(spend_file)

    # output and report results for this timestep
    for road in data:
        spend_writer.writerow(
            (year, scenario, strategy, car_spacing, 
            road['road_function'], road['urban_rural'], road['length_km'], road['CAV_revenue'],   
            road['lte_upgrade_costs'], road['new_sites_cost'], road['new_sites_civil_works_cost'], road['total_tco']))

def _get_suffix(scenario, strategy, car_spacing):
    suffix = 'scenario_{}_strategy_{}_car_spacing_{}'.format(scenario, strategy, car_spacing)
    return suffix

#####################################
# run functions
# #####################################

DEPLOYMENT_PERIOD = 4

print("reading in aggregated road geotype data")
road_geotype_data = read_in_csv_road_geotype_data('aggregated_road_statistics.csv')

print("reading in road by pcd_sector data")
road_by_pcd_sectors = read_in_road_geotype_data('pcd_sector_road_length_by_type.csv')

print("reading in cell densities by pcd_sector data")
cell_densities = read_in_cell_densities('pcd_sector_cell_densities.csv')

print("reading in capacity lut")
capacity_lut = read_in_capacity_lut('lookup_table_long.csv')

print("calculating tco costs")
small_cell_tco = calculate_tco_for_each_asset(2500, 350, 0.035, 2019, 2020, 10, 2029, 'no') 
small_cell_civil_works_tco = calculate_tco_for_each_asset(13300, 0, 0.035, 2019, 2020, 0, 2029, 'no')
fibre_tco_per_km = calculate_tco_for_each_asset(20000, 20, 0.035, 2019, 2020, 0, 2029, 'no') 
# upgrade_lte_macro_tco = calculate_tco_for_each_asset(15000, 1800, 0.035, 2019, 2020, 10, 2029, 'no') 
# upgrade_macro_to_lte_tco = calculate_tco_for_each_asset(40900, 8898, 0.035, 2019, 2020, 10, 2029, 'no') 
# upgrade_macro_to_lte_civil_works = calculate_tco_for_each_asset(18000, 0, 0.035, 2019, 2020, 10, 2029, 'no') 

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
        
    # else:
        
    #     for year in TIMESTEPS:

    #         print("-", year)

    #         all_roads_pcd_demand = calculate_potential_demand(road_by_pcd_sectors, 5, car_spacing)

    #         pcd_sector_road_demand = aggregator(all_roads_pcd_demand,'total_cars','pcd_sector','pcd_sector')

    #         pcd_sector_road_demand = calculate_yearly_CAV_take_up(pcd_sector_road_demand, year, scenario)

    #         pcd_sector_population = read_in_population_estimates('population_baseline_pcd.csv', year)

    #         user_demand = get_annual_user_demand('monthly_data_growth_scenarios.csv', year)

    #         baseline_demand = calc_pcd_sector_baseline_demand(pcd_sector_population, user_demand)

    #         pcd_sector_data = merge_two_lists_of_dicts(pcd_sector_road_demand, baseline_demand, 'pcd_sector', 'pcd_sector')

    #         pcd_sector_data = deal_with_missing_population(pcd_sector_data)

    #         pcd_sector_data = merge_two_lists_of_dicts(pcd_sector_data, cell_densities, 'pcd_sector', 'pcd_sector')

    #         pcd_sector_data = deal_with_missing_cells(pcd_sector_data)

    #         pcd_sector_data = get_pcd_sector_capacity(pcd_sector_data, capacity_lut)

    #         pcd_sector_data = upgrade_existing_sites(pcd_sector_data, year, scenario, upgrade_lte_macro_tco, 0)
            
    #         pcd_sector_data = build_new_sites(pcd_sector_data, year, DEPLOYMENT_PERIOD, capacity_lut)

    #         # pcd_sector_data = calculate_cost_of_new_assets(pcd_sector_data, DEPLOYMENT_PERIOD, upgrade_macro_to_lte_tco, upgrade_macro_to_lte_civil_works, fibre_tco_per_km)

    #         # cost_by_road_type = transfer_cost_from_pcd_sector_to_road_type(pcd_sector_data, all_roads_pcd_demand)
            
    #         # cost_by_road_type = deal_with_missing_road(cost_by_road_type)
            
    #         # cost_by_road_type = aggregate_costs_by_road_type(cost_by_road_type)

    #         # write_cellular_spend_by_road(cost_by_road_type, year, scenario, strategy, car_spacing)

    #         # write_cellular_spend(pcd_sector_data, year, scenario, strategy, car_spacing)

       