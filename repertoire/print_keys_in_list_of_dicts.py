import csv
import os

BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, '..', 'Data')
DATA_FILE = os.path.join(CONFIG_DIR, 'pcd_sectors.csv')

#set DictReader with file name
reader = csv.DictReader(open(DATA_FILE))

#create empty dictionary
result = []

#populate dictionary
for row in reader:
    result.append(row)

all_keys = set().union(*(d.keys() for d in result))

print(all_keys)	
