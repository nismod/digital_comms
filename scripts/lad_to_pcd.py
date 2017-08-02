import csv
import math
import os

POPULATION_BY_LAD_FILES = {
    "High": "population_high_cambridge_lad.csv",
    "Baseline": "population_base_cambridge_lad.csv",
    "Low": "population_low_cambridge_lad.csv"
}
POPULATION_BY_POSTCODE_SECTOR_FILES = {
    "High": "population_high_cambridge_pcd.csv",
    "Baseline": "population_base_cambridge_pcd.csv",
    "Low": "population_low_cambridge_pcd.csv"
}
PCD_SECTORS_FILE = 'pcd_sectors.csv'

weights_by_pcd_sector = {}

with open(PCD_SECTORS_FILE, 'r') as in_file:
    r = csv.DictReader(in_file)
    for line in r:
        pcd = line['pcd_sector']
        weight = float(line['population_weight'])
        weights_by_pcd_sector[pcd] = weight

for scenario in ("High", "Baseline", "Low"):
    with open(POPULATION_BY_LAD_FILES[scenario], 'r') as in_file:
        with open(POPULATION_BY_POSTCODE_SECTOR_FILES[scenario], 'w') as out_file:
            r = csv.reader(in_file)
            w = csv.writer(out_file)
            for year, lad, lad_pop in r:
                for pcd_id, pop_weight in weights_by_pcd_sector.items():
                    pcd_pop = math.floor(int(lad_pop) * pop_weight)
                    w.writerow((year, pcd_id, pcd_pop))
