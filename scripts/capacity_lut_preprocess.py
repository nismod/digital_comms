import configparser
import csv
import os
import statistics

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# setup file locations and data files
#####################################

LUT_INPUT_FIXED = os.path.join(BASE_PATH, 'raw', 'capacity_lookup')
LUT_OUTPUT_FIXED = os.path.join(BASE_PATH, 'processed')

#####################################
# READ LOOK UP TABLE (LUT) DATA
#####################################

def read_capacity_lut(data_name, folder_year, column1, column2, column3, column4):
    """

    """
    capacity_lut_data = []
    with open(os.path.join(LUT_INPUT_FIXED, folder_year, data_name), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            capacity_lut_data.append({
                #'urban_rural': line[column1],
                #'distance': float(line[column2]),
                'technology': line[column3],
                'mean_speed': float(line[column4])
            })     
 
        return capacity_lut_data

##################################################################
# FIND MEAN CAPACITY BASED ON URBAN_RURAL, DISTANCE AND TECHNOLOGY
##################################################################

def find_mean_capacity_urban_distance_technology():
    """

    """
    dic = {}
    for d in capacity_lut:
        key = d['urban_rural'], d['distance'], d['technology']
        if key not in dic: dic[key] = []
        dic[key].append(d['mean_speed'])
        
        mean = [{"urban_rural":key[0], "distance":key[1], "technology":key[2], "mean_speed":sum(val)/len(val)}
            for key,val in dic.items()]

    return mean

##################################################################
# FIND MEAN CAPACITY BASED ON URBAN_RURAL AND TECHNOLOGY
##################################################################

def find_mean_capacity_urban_technology(data):
    """

    """
    dic = {}
    for d in data:
        key = d['technology']
        if key not in dic: dic[key] = []
        dic[key].append(d['mean_speed'])
        
        mean = [{"technology":key, "mean_speed":round(sum(val)/len(val), 1)}
            for key,val in dic.items()]

    return mean

#####################################
# WRITE LOOK UP TABLE (LUT) DATA
#####################################

def csv_writer(data, filename):
    """
    Write data to a CSV file path
    """
    fieldnames = data[0].keys()
    with open(os.path.join(LUT_OUTPUT_FIXED, filename),'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)

#####################################
# EXECUTE FUNCTIONS
#####################################

#read LUT
capacity_lut = read_capacity_lut('panellist-data_November_2017.csv', '2017', 11, 5, 6, 14)

#find mean capacity
mean_capacity_lut = find_mean_capacity_urban_technology(capacity_lut)

#write to .csv file
csv_writer(mean_capacity_lut, 'fixed_capacity_lut_nov_2017.csv')
