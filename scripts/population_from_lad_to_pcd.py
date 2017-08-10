import configparser
import csv
import math
import os

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']
PCD_SECTORS_FILE = os.path.join(BASE_PATH, 'initial_system', 'pcd_sectors.csv')
SCENARIOS = ("high", "baseline", "low")

# Read postcode sectors with population snapshot, to group by LAD.
pcd_sectors_by_lad = {}
with open(PCD_SECTORS_FILE, 'r') as in_file:
    r = csv.DictReader(in_file)
    for line in r:
        lad = line['oslaua']
        if lad not in pcd_sectors_by_lad:
            pcd_sectors_by_lad[lad] = []
        pcd_sectors_by_lad[lad].append(line)

# Add population_weight to each postcode sector, as the fraction of the
# population of the containing LAD.
for lad, pcd_sectors in pcd_sectors_by_lad.items():
    lad_population = sum([float(pcd['population']) for pcd in pcd_sectors])
    for line in pcd_sectors:
        weight = float(line['population']) / lad_population
        line['pop_weight'] = weight

# Disaggregate LAD population scenarios, allocating population to postcode
# sectors in proportion to the weights calculated above
for scenario in SCENARIOS:
    in_filename = os.path.join(
        BASE_PATH,
        'scenario_data',
        'population_{}_lad.csv'.format(scenario)
    )
    out_filename = os.path.join(
        BASE_PATH,
        'scenario_data',
        'population_{}_pcd.csv'.format(scenario)
    )
    with open(in_filename, 'r') as in_file:
        with open(out_filename, 'w', newline='') as out_file:
            r = csv.reader(in_file)
            next(r)  # skip header
            w = csv.writer(out_file)
            for year, lad, lad_pop in r:
                for pcd in pcd_sectors_by_lad[lad]:
                    pcd_id = pcd['pcd_sector']
                    pop_weight = pcd['pop_weight']
                    pcd_pop = math.floor(float(lad_pop) * pop_weight)
                    w.writerow((year, pcd_id, pcd_pop))
