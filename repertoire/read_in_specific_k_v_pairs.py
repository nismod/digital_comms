import csv
import os
import pprint

#set path for 4G rollout data
BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, '..', 'Data')
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
selection = [dict((k, d[k]) for k in keys) for d in rollout_4G]#

pprint.pprint (selection)