import csv
import os
import pprint

################################################################
#### IMPORT ASSET DATA
################################################################

#set path for sitefinder asset data
BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, '..', 'Data')
DATA_FILE = os.path.join(CONFIG_DIR, 'sitefinder_asset_data.csv')

#set DictReader with file name for 4G rollout data
reader = csv.DictReader(open(DATA_FILE))

#create empty dictionary
assets = []

#populate dictionary
for row in reader:
    assets.append(row)

keys = ['Operator', 
		'Sitengr',
		'Transtype',
		'Freqband',
		'Anttype',
		'pcd_sector',
		'geo_code'
		]
assets = [dict((k, d[k]) for k in keys) for d in assets]

#remove whitespace from 'pcd_sector' values
for d in assets:
    for pcd_sector in d:
        if isinstance(d[pcd_sector], str):
            d[pcd_sector] = d[pcd_sector].replace(' ', '')

################################################################
#### IMPORT ROLLOUT DATA
################################################################

#set path for 4G rollout data
DATA_FILE = os.path.join(CONFIG_DIR, 'rollout_4G.csv')

#set DictReader with file name for 4G rollout data
reader = csv.DictReader(open(DATA_FILE))

#create empty dictionary
rollout_4G = []

#populate dictionary
for row in reader:
    rollout_4G.append(row)

keys = ['name', 
		'pcd_sector',
		'area_coverage_2014',
		'area_coverage_2015',
		'area_coverage_2016',
		]
rollout_4G = [dict((k, d[k]) for k in keys) for d in rollout_4G]#

#### join two lists of dicts on a single key
from collections import defaultdict
from operator import itemgetter

d = defaultdict(dict)
for pcd_sector in (assets, rollout_4G):
    for elem in pcd_sector:
        d[elem['pcd_sector']].update(elem)

output =  sorted(d.values(), key=itemgetter("pcd_sector"))

pprint.pprint (output)


























