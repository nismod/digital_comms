import csv
import os
from collections import defaultdict

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

#don't know how to do this for multiple keys, but this works	
for sub in result:
    for key in sub:
        sub['sitefinder.count'] = int(sub['sitefinder.count'])

#print(result)	
	
c = defaultdict(int)

for d in result:
    c[d['oslaua']] += d['sitefinder.count']

print (c)