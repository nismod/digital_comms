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
		'geo_code',
		'X',
		'Y'
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
		'area_sq_km']

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
				'area_coverage_2016',
				'area_sq_km']: # list of keys to convert
		try:
			sub[key] = float(sub[key]) if key !='NA' else None
		except ValueError as e:
			pass

#### join two lists of dicts on a single key

d1 = {d['pcd_sector']:d for d in rollout_4G}
output = [dict(d, **d1.get(d['pcd_sector'], {})) for d in assets]

print('The length of output is {}'.format(len(output)))

#for 2014
for item in output:
	try:
		coverage = float(item['area_coverage_2014'])
		if coverage > 0:
			item["tech_2014"] = "4G"
		else:
			item["tech_2014"] = "other"
	except (KeyError, ValueError) as e:
		item["coverage"] = 0
		item["tech_2014"] = "Other"

#for 2015
for item in output:
	try:
		coverage = float(item['area_coverage_2015'])
		if coverage > 0:
			item["tech_2015"] = "4G"
		else:
			item["tech_2015"] = "other"
	except (KeyError, ValueError) as e:
		item["coverage"] = 0
		item["tech_2015"] = "Other"

##for 2016
for item in output:
	try:
		coverage = float(item['area_coverage_2016'])
		if coverage > 0:
			item["tech_2016"] = "4G"
		else:
			item["tech_2016"] = "other"
	except (KeyError, ValueError) as e:
		item["coverage"] = 0
		item["tech_2016"] = "Other"

#get keys for export
keys = set().union(*(d.keys() for d in output))
keys = output[0].keys()

#set path for sitefinder asset data
BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, '..', 'Data')
DATA_FILE = os.path.join(CONFIG_DIR, 'assets_with_4G_rollout.csv')

with open (DATA_FILE, 'w') as output_file:
	dict_writer = csv.DictWriter(output_file, keys,
								extrasaction='ignore',
								lineterminator = '\n')
	dict_writer.writeheader()
	dict_writer.writerows(output)

###get unique site information

output = list({v['Sitengr']:v for v in output}.values())

#get keys for export
keys = set().union(*(d.keys() for d in output))
keys = output[0].keys()

#set path for site data
BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, '..', 'Data')
DATA_FILE = os.path.join(CONFIG_DIR, 'sites_with_4G_rollout.csv')

with open (DATA_FILE, 'w') as output_file:
	dict_writer = csv.DictWriter(output_file, keys,
								extrasaction='ignore',
								lineterminator = '\n')
	dict_writer.writeheader()
	dict_writer.writerows(output)

#pprint.pprint (output)

# merged dictionary
sites_by_postcode_sector = {}
for i in output:
	pcd_sector = i["pcd_sector"]
	if pcd_sector not in sites_by_postcode_sector:
		sites_by_postcode_sector[pcd_sector] = []

	sites_by_postcode_sector[pcd_sector].append(i)

# # counting and printing
list_of_postcode_sector_sites = []
for postcode_sector, sites in sites_by_postcode_sector.items():
	#print("{0}: {1}".format(postcode_sector, len(sites)))
	site_ngrs = [site['Sitengr'] for site in sites]
	list_of_postcode_sector_sites.append({
		"pcd_sector": postcode_sector,
		"site_ngrs": len(set(site_ngrs))
	})

#### join the 'site_ngrs' count back to the output with the 'area_sq_km' key
d1 = {d['pcd_sector']:d for d in output}
site_count = [dict(d, **d1.get(d['pcd_sector'], {})) for d in list_of_postcode_sector_sites]

print('The length of output is {}'.format(len(output)))

#get keys for export
keys = output[0].keys()

#set path for site data
BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, '..', 'Data')
DATA_FILE = os.path.join(CONFIG_DIR, 'sites_count_by_pcd_sector.csv')

with open (DATA_FILE, 'w') as output_file:
	dict_writer = csv.DictWriter(output_file, keys,
								extrasaction='ignore',
								lineterminator = '\n')
	dict_writer.writeheader()
	dict_writer.writerows(output)


