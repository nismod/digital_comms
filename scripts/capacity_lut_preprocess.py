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

def read_capacity_lut():
    """

    """
    capacity_lut_data = []
    with open(os.path.join(LUT_INPUT_FIXED, 'UK-home-broadband-performance-2017-panellist-data.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            capacity_lut_data.append({
                'urban_rural': line[4],
                'distance': line[5],
                'technology': line[6],
                'mean_speed': float(line[8]),
            })     
 
        return capacity_lut_data

def find_mean_capacity():
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
capacity_lut = read_capacity_lut()

#find mean capacity
mean_capacity_lut = find_mean_capacity()

#write to .csv file
csv_writer(mean_capacity_lut, 'fixed_capacity_lut.csv')
