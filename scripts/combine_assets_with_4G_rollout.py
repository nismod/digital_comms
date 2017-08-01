"""Combine Sitefinder assets with 4G rollout

- export sites by postcode sector with possible
"""
# pylint: disable=C0103
import csv
import os

################################################################
# IMPORT ASSET DATA
################################################################

# set path for sitefinder asset data
BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, '..', 'Data')
DATA_FILE = os.path.join(CONFIG_DIR, 'sitefinder_with_geo_IDs.csv')

# set DictReader with file name for 4G rollout data
reader = csv.DictReader(open(DATA_FILE))

# create empty dictionary
assets = []

# populate dictionary
for row in reader:
    assets.append(row)

keys = [
    'Operator',
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

# remove whitespace from 'pcd_sector' values
for d in assets:
    for pcd_sector in d:
        if isinstance(d[pcd_sector], str):
            d[pcd_sector] = d[pcd_sector].replace(' ', '')

################################################################
# IMPORT ROLLOUT DATA
################################################################

# set path for 4G rollout data
DATA_FILE = os.path.join(CONFIG_DIR, 'rollout_4G.csv')

# set DictReader with file name for 4G rollout data
reader = csv.DictReader(open(DATA_FILE))

# create empty dictionary
rollout_4G = []

# populate dictionary
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

# remove whitespace from 'pcd_sector' values
for d in rollout_4G:
    for pcd_sector in d:
        if isinstance(d[pcd_sector], str):
            d[pcd_sector] = d[pcd_sector].replace(' ', '')


for sub in rollout_4G:
    for key in ['area_coverage_2014',
                'area_coverage_2015',
                'area_coverage_2016',
                'area_sq_km']:  # list of keys to convert
        try:
            sub[key] = float(sub[key]) if key != 'NA' else None
        except ValueError as e:
            pass

# join two lists of dicts on a single key

d1 = {d['pcd_sector']:d for d in rollout_4G}
rollout_data = [dict(d, **d1.get(d['pcd_sector'], {})) for d in assets]

print('The length of rollout_data is {}'.format(len(rollout_data)))


################################################################
# ALLOCATE ANNUAL ROLLOUT COVERAGE TO ASSETS IN PCD_SECTORS
################################################################

# for 2014
for item in rollout_data:
    try:
        coverage = float(item['area_coverage_2014'])
        if coverage > 0:
            item["tech_2014"] = "4G"
        else:
            item["tech_2014"] = "other"
    except (KeyError, ValueError) as e:
        item["coverage"] = 0
        item["tech_2014"] = "Other"

# for 2015
for item in rollout_data:
    try:
        coverage = float(item['area_coverage_2015'])
        if coverage > 0:
            item["tech_2015"] = "4G"
        else:
            item["tech_2015"] = "other"
    except (KeyError, ValueError) as e:
        item["coverage"] = 0
        item["tech_2015"] = "Other"

# for 2016
for item in rollout_data:
    try:
        coverage = float(item['area_coverage_2016'])
        if coverage > 0:
            item["tech_2016"] = "4G"
        else:
            item["tech_2016"] = "other"
    except (KeyError, ValueError) as e:
        item["coverage"] = 0
        item["tech_2016"] = "Other"


################################################################
# EXPORT ASSET-LEVEL ROLLOUT DATA
################################################################

# get keys for export
keys = set().union(*(d.keys() for d in rollout_data))
keys = rollout_data[0].keys()

# set path for sitefinder asset data
BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, '..', 'Data')
DATA_FILE = os.path.join(CONFIG_DIR, 'assets_with_4G_rollout.csv')

with open(DATA_FILE, 'w') as output_file:
    dict_writer = csv.DictWriter(output_file, keys,
                                 extrasaction='ignore',
                                 lineterminator='\n')
    dict_writer.writeheader()
    dict_writer.writerows(rollout_data)

################################################################
# DETERMINE UNIQUE SITES, COUNT AND ADD DENSITY
################################################################

# get unique site information
site_info = list({v['Sitengr']:v for v in rollout_data}.values())

# get keys for export
keys = set().union(*(d.keys() for d in site_info))
keys = site_info[0].keys()

# set path for site data
BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, '..', 'Data')
DATA_FILE = os.path.join(CONFIG_DIR, 'sites_with_4G_rollout.csv')

with open(DATA_FILE, 'w') as output_file:
    dict_writer = csv.DictWriter(output_file, keys,
                                 extrasaction='ignore',
                                 lineterminator='\n')
    dict_writer.writeheader()
    dict_writer.writerows(site_info)


# merged dictionary
"""
{
    "CB11": [
        {"sitengr": 123, "tech": "Other" ... },
        {"sitengr": 123, "tech": "Other" ... },
        {"sitengr": 123, "tech": "Other" ... },
        {"sitengr": 123, "tech": "Other" ... },
    ]
    "CB12": [
        {"sitengr": 123, "tech": "Other" ... },
        {"sitengr": 123, "tech": "Other" ... },
    ]
}
"""
sites_by_postcode_sector = {}
for i in site_info:
    pcd_sector = i["pcd_sector"]
    if pcd_sector not in sites_by_postcode_sector:
        sites_by_postcode_sector[pcd_sector] = []

    sites_by_postcode_sector[pcd_sector].append(i)

# counting and printing
"""
{
    "CB11": 4
    "CB12": 2
}
"""
site_counts_by_postcode_sector = {}
for postcode_sector, sites in sites_by_postcode_sector.items():
    # print("{0}: {1}".format(postcode_sector, len(sites)))
    site_ngrs = [site['Sitengr'] for site in sites]
    site_counts_by_postcode_sector[postcode_sector] = len(set(site_ngrs))

print (rollout_4G[0])

# join the 'site_ngrs' count back to the output with the 'area_sq_km' key
for postcode_sector_data in rollout_4G:
    postcode_sector = postcode_sector_data["pcd_sector"]
    if postcode_sector in site_counts_by_postcode_sector:
        site_count = site_counts_by_postcode_sector[postcode_sector]
        postcode_sector_data["site_count"] = site_count

        area_sq_km = postcode_sector_data["area_sq_km"]
        site_density = site_count / area_sq_km
        postcode_sector_data["site_density"] = site_density
    else:
        # assume zero for missing data
        postcode_sector_data["site_count"] = 0
        postcode_sector_data["site_density"] = 0

print('The length of site_count is {}'.format(len(rollout_4G)))

################################################################
# EXPORT SITES COUNT BY PCD_SECTOR
################################################################

#get keys for export
keys =  rollout_4G[0].keys()

#set path for site data
BASE_DIR = os.path.dirname(__file__)
CONFIG_DIR = os.path.join(BASE_DIR, '..', 'Data')
DATA_FILE = os.path.join(CONFIG_DIR, 'sites_count_by_pcd_sector.csv')

with open (DATA_FILE, 'w') as output_file:
    dict_writer = csv.DictWriter(output_file, keys,
                                 extrasaction='ignore',
                                 lineterminator='\n')
    dict_writer.writeheader()
    dict_writer.writerows(rollout_4G)