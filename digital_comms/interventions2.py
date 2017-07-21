import csv
import os
import pprint

################################################################
#### IMPORT ASSET DATA
################################################################

#set path for sitefinder asset data
BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, '..', 'Data')
DATA_FILE = os.path.join(CONFIG_DIR, 'sitefinder_with_geo_IDs.csv')

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

print('The length of assets is {}'.format(len(assets))) 

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

print('The length of rollout_4G is {}'.format(len(rollout_4G))) 

#remove whitespace from 'pcd_sector' values
for d in rollout_4G:
    for pcd_sector in d:
        if isinstance(d[pcd_sector], str):
            d[pcd_sector] = d[pcd_sector].replace(' ', '')


for sub in rollout_4G:
	for key in ['area_coverage_2014',
				'area_coverage_2015',
				'area_coverage_2016']: # list of keys to convert
		try:
			sub[key] = float(sub[key]) if key !='NA' else None
		except ValueError as e:
			pass

#### join two lists of dicts on a single key
#from collections import defaultdict
#from operator import itemgetter

#d = defaultdict(dict)
#for pcd_sector in (assets, rollout_4G):
#    for elem in pcd_sector:
#        d[elem['pcd_sector']].update(elem)
#output =  sorted(d.values(), key=itemgetter("pcd_sector"))

grouped = {}
for d in assets + rollout_4G:
	grouped.setdefault(d['pcd_sector'], {'Operator':0, 'area_coverage_2014':0}).update(d)

output = [d for d in grouped.values()]
pprint.pprint(output)	

#output = {}
#for d in assets + rollout_4G:
#	output.setdefult(d['pcd_sector'], {'Operator': 0, 'Anttype': 0, 'Freqband': 0}).update(d)

print('The length of output is {}'.format(len(output))) 


#def merge_lists(l1, l2, key):
#    merged = {}
#    for item in l1+l2:
#        if item[key] in merged:
#            merged[item[key]].update(item)
#        else:
#            merged[item[key]] = item
#    return merged.values()

#output = merge_lists(assets, rollout_4G, 'pcd_sector')






#for d in output:
#	try:
#		coverage = float(d['area_coverage_2014'])
#		if coverage > 0:
#			d['new_key'] = True
#		else:
#			d['new_key'] = False
#	except ValueError as e:
#		d['new_key'] = False

#pprint.pprint(output)

#keys = set().union(*(d.keys() for d in output))
#print (all_keys)

#keys = output[0].keys()
#keys = ['Transtype']
#with open ('output.csv', 'w') as output_file:
#	dict_writer = csv.DictWriter(output_file, keys, 
#								extrasaction='ignore',
#								lineterminator = '\n')
#	dict_writer.writeheader()
#	dict_writer.writerows(output)

























