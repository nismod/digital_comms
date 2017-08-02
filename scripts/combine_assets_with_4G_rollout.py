"""Combine Sitefinder assets with 4G rollout

- export sites by postcode sector with possible
"""
# pylint: disable=C0103
import csv
import os
import random

################################################################
# IMPORT ASSET DATA
################################################################

# BASE_PATH = r"C:\Users\EJO31\Dropbox\Digital Comms - Cambridge data"
# BASE_PATH = r"C:\Users\mert2014\Dropbox\Digital Comms - Cambridge data"
BASE_PATH = "/home/tom/Dropbox/Digital Comms - Cambridge data"

SITEFINDER_FILENAME = os.path.join(BASE_PATH, 'sitefinder_with_geo_IDs.csv')

# set path for sitefinder asset data
with open(SITEFINDER_FILENAME, 'r') as sitefinder_file:
    # set DictReader with file name for 4G rollout data
    reader = csv.DictReader(sitefinder_file)

    # create empty dictionary
    assets_by_postcode_sector = {}

    # populate dictionary
    for row in reader:
        # remove whitespace from postcode sector
        pcd_sector = row['pcd_sector'].replace(' ','')

        # check postcode sector is in dictionary
        if pcd_sector not in assets_by_postcode_sector:
            assets_by_postcode_sector[pcd_sector] = []

        # Uniform random assignment of build date over ten-year period
        # to match assumption of ~10% decommissioning rate
        build_date = random.randint(2006, 2016)

        # add asset data to list
        assets_by_postcode_sector[pcd_sector].append({
            'site_ngr': row['Sitengr'],
            'frequency': row['Freqband'],
            'technology': row['Transtype'],
            # assume any macrocell has 2x10MHz bandwidth
            'bandwidth': '2x10MHz',
            'build_date': build_date,
        })

num_pcd_sectors = len(assets_by_postcode_sector.keys())
num_assets = sum([len(assets) for assets in assets_by_postcode_sector.values()])
print('Read {} assets across {} postcode sectors'.format(num_assets, num_pcd_sectors))


################################################################
# IMPORT ROLLOUT DATA
################################################################

# set path for 4G rollout data
ROLLOUT_FILENAME = os.path.join(BASE_PATH, 'rollout_4G.csv')

with open(ROLLOUT_FILENAME, 'r') as rollout_file:
    # set DictReader with file name for 4G rollout data
    reader = csv.DictReader(rollout_file)

    # create empty dictionary
    rollout_4G_by_postcode_sector = {}

    # populate dictionary
    for row in reader:
        # remove whitespace from postcode sector
        pcd_sector = row['pcd_sector'].replace(' ','')

        rollout_datum = {}

        for key in ['area_coverage_2014',
                    'area_coverage_2015',
                    'area_coverage_2016',
                    'area_sq_km']:  # list of keys to convert
            if row[key] != 'NA':
                rollout_datum[key] = float(row[key])
            else:
                rollout_datum[key] = 0

        rollout_4G_by_postcode_sector[pcd_sector] = rollout_datum

print('Read 4G rollout data across {} postcode sectors'.format(len(rollout_4G_by_postcode_sector.keys())))


################################################################
# ALLOCATE ANNUAL ROLLOUT COVERAGE TO ASSETS IN PCD_SECTORS
################################################################

def generate_4g_build_year(year):
    """For rollout up to and including 2014, assume a build date at random
    between 2012 (when UK 4G rollout started) and 2014
    """
    if year > 2014:
        return year
    else:
        return random.randint(2012, 2014)

for pcd_sector, rollout_datum in rollout_4G_by_postcode_sector.items():
    if pcd_sector not in assets_by_postcode_sector:
        # warn if rollout data has a postcode sector absent from sitefinder
        print("{} not found in sitefinder assets, assuming no sites in this postcode sector.".format(pcd_sector))
        assets_by_postcode_sector[pcd_sector] = []

    existing_assets = assets_by_postcode_sector[pcd_sector]
    site_ngrs = list(set([asset['site_ngr'] for asset in existing_assets]))

    for year in [2014, 2015, 2016]:
        coverage = float(rollout_datum['area_coverage_{}'.format(year)])
        # If the postcode got 4G coverage
        if coverage > 0:
            if len(site_ngrs) == 0:
                build_year = generate_4g_build_year(year)
                # If there are no sites from sitefinder, but we got coverage,
                # introduce a site with 4G carriers
                existing_assets.append({
                    'site_ngr': 'unknown',
                    'frequency': '800',
                    'technology': 'LTE',
                    # assume any macrocell has 2x10MHz bandwidth
                    'type': 'macrocell_site',
                    'bandwidth': '2x10MHz',
                    'build_date': build_year,
                })
                existing_assets.append({
                    'site_ngr': 'unknown',
                    'frequency': '2600',
                    'technology': 'LTE',
                    # assume any macrocell has 2x10MHz bandwidth
                    'type': 'macrocell_site',
                    'bandwidth': '2x10MHz',
                    'build_date': build_year,
                })
            else:
                # "Build" a new carrier for each site in the postcode (800MHz and 2.6GHz)
                for site_ngr in site_ngrs:
                    build_year = generate_4g_build_year(year)

                    existing_assets.append({
                        'site_ngr': site_ngr,
                        'frequency': '800',
                        'technology': 'LTE',
                        # assume any macrocell has 2x10MHz bandwidth
                        'type': 'macrocell_site',
                        'bandwidth': '2x10MHz',
                        'build_date': build_year,
                    })
                    existing_assets.append({
                        'site_ngr': site_ngr,
                        'frequency': '2600',
                        'technology': 'LTE',
                        # assume any macrocell has 2x10MHz bandwidth
                        'type': 'macrocell_site',
                        'bandwidth': '2x10MHz',
                        'build_date': build_year,
                    })
            # Stop looping through coverage years
            break


################################################################
# OUTPUT INITIAL SYSTEM
################################################################

keys = (
    'pcd_sector',
    'site_ngr',
    'build_date',
    'type',
    'technology',
    'frequency',
    'bandwidth',
)

SYSTEM_FILENAME =  os.path.join(BASE_PATH, 'initial_system_with_4G.csv')
with open(SYSTEM_FILENAME, 'w', newline='') as system_file:
    writer = csv.DictWriter(system_file, fieldnames=keys)
    writer.writeheader()
    for pcd_sector, assets in assets_by_postcode_sector.items():
        for asset in assets:
            asset['pcd_sector'] = pcd_sector
            writer.writerow(asset)
