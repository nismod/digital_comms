"""
Script to generate digital_mobile interventions.

Written by Ed Oughton
August 2019

"""
import csv
import configparser
import os
import glob
from itertools import tee
import time

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

RAW = os.path.join(BASE_PATH, 'raw', 'b_mobile_model','mobile_model_1.0')
INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')


def load_initial_conditions():

    path = os.path.join(INTERMEDIATE, 'nismod2_inputs', 'digital_initial_conditions.csv')

    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        return [asset for asset in reader]


def load_postcode_sectors(geotype_lookup):
    """
    Load in postcode sector information.

    """
    pcd_sectors = []
    PCD_SECTOR_FILENAME = os.path.join(INTERMEDIATE, 'mobile_model_inputs',
        '_processed_postcode_sectors.csv')

    with open(PCD_SECTOR_FILENAME, 'r') as source:
        reader = csv.DictReader(source)
        for pcd_sector in reader:
            pcd_sectors.append({
                "id": pcd_sector['id'].replace(" ", ""),
                "lad_id": pcd_sector['lad'],
                "pop_density_km2": float(pcd_sector['pop_density_km2']),
                'lte_4G': pcd_sector['lte_4G'],
                "area_km2": float(pcd_sector['area_km2']),
                "geotype": (
                    lookup_clutter_geotype(geotype_lookup,
                    float(pcd_sector['pop_density_km2']))
                )
            })

    return pcd_sectors


def lookup_clutter_geotype(geotype_lookup, population_density):
    """Return geotype based on population density

    Params:
    ======
    geotype_lookup : list of (population_density_upper_bound, geotype) tuples
        sorted by population_density_upper_bound ascending
    """

    highest_popd, highest_geotype = geotype_lookup[0]
    middle_popd, middle_geotype = geotype_lookup[1]
    lowest_popd, lowest_geotype = geotype_lookup[2]

    if population_density < middle_popd:
        return lowest_geotype

    elif population_density > highest_popd:
        return highest_geotype

    else:
        return middle_geotype


def pairwise(iterable):
    """Return iterable of 2-tuples in a sliding window

        >>> list(pairwise([1,2,3,4]))
        [(1,2),(2,3),(3,4)]
    """
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def load_capacity_lookup_table(geotypes):

    PATH_LIST = glob.iglob(os.path.join(INTERMEDIATE, 'system_simulator',
    '*capacity_lookup_table*.csv'))

    capacity_lookup_table = {}

    for path in PATH_LIST:
        with open(path, 'r') as capacity_lookup_file:
            reader = csv.DictReader(capacity_lookup_file)
            for row in reader:
                if row["environment"].lower() == 'urban' and 0.01 > float(row["sites_per_km2"]):
                    continue
                if row["environment"].lower() == 'suburban' and (
                   float(row["sites_per_km2"]) < 0.001 or float(row["sites_per_km2"]) > 1):
                    continue
                if row["environment"].lower() == 'rural' and float(row["sites_per_km2"]) > 0.5:
                    continue
                environment = row["environment"].lower()
                frequency = str(int(float(row["frequency_GHz"]) * 1e3))
                bandwidth = row["bandwidth_MHz"]
                # mast_height = str(row['mast_height_m'])
                density = float(row["sites_per_km2"])
                capacity = float(row["capacity_mbps_km2"])
                cell_edge_spectral_efficency = float(
                    row['spectral_efficiency_bps_hz']
                )

                if (environment, frequency, bandwidth) \
                    not in capacity_lookup_table:
                    capacity_lookup_table[(
                        environment, frequency, bandwidth)
                        ] = []

                capacity_lookup_table[(
                    environment, frequency, bandwidth
                    )].append((
                        density, capacity
                    ))

            for key, value_list in capacity_lookup_table.items():
                value_list.sort(key=lambda tup: tup[0])

    return capacity_lookup_table


def find_maximum_required_assets(geotype, area_km2, capacity_lookup):
    """
    To reduce the number of assets needing to be generated, this function
    uses maximum asset density (per km^2) by geotype, to calculate the
    maximum required assets for a postcode_sector

    """
    capacity_values = []
    for key, values in capacity_lookup.items():
        if key[0] == geotype:
            for value in values:
                capacity_values.append(value[0])

    max_assets_km2 = max(capacity_values)

    max_assets = max_assets_km2 * area_km2

    return roundup(max_assets)


def roundup(number):
    return round(number + 0.5)


def generate_assets(postcode_sectors, capacity_lookup, initial_conditions):

    all_possible_assets = initial_conditions

    for pcd_sector in postcode_sectors:

        max_macro_assets = find_maximum_required_assets(pcd_sector['geotype'],
            pcd_sector['area_km2'], capacity_lookup)

        for asset_id in range(0, (max_macro_assets)):

            #add 800 to site
            all_possible_assets.append(
                {
                    'name': 'macro_cell_{}_{}_{}_{}_{}'.format(
                        '800', '4G', pcd_sector['id'], asset_id, pcd_sector['geotype']),
                    'build_year': None,
                    'frequency': '800',
                    'technology': '4G',
                    'type': 'macrocell_site',
                    'id': pcd_sector['id'].replace(' ', ''),
                    'technical_lifetime_value': 10,
                    'technical_lifetime_units': 'years',
                    'capex': 50917,
                    'opex': 2000,
                }
            )

            #add 1800 to site
            all_possible_assets.append(
                {
                    'name': 'macro_cell_{}_{}_{}_{}_{}'.format(
                        '1800', '4G', pcd_sector['id'], asset_id, pcd_sector['geotype']),
                    'build_year': None,
                    'frequency': '1800',
                    'technology': '4G',
                    'type': 'macrocell_site',
                    'id': pcd_sector['id'].replace(' ', ''),
                    'technical_lifetime_value': 10,
                    'technical_lifetime_units': 'years',
                    'capex': 50917,
                    'opex': 2000,
                }
            )

            #add 2600 to site
            all_possible_assets.append(
                {
                    'name': 'macro_cell_{}_{}_{}_{}_{}'.format(
                        '2600', '4G', pcd_sector['id'], asset_id, pcd_sector['geotype']),
                    'build_year': None,
                    'frequency': '2600',
                    'technology': '4G',
                    'type': 'macrocell_site',
                    'id': pcd_sector['id'].replace(' ', ''),
                    'technical_lifetime_value': 10,
                    'technical_lifetime_units': 'years',
                    'capex': 50917,
                    'opex': 2000,
                }
            )

            #add 700 to site
            all_possible_assets.append(
                {
                    'name': 'macro_cell_{}_{}_{}_{}_{}'.format(
                        '700', '5G', pcd_sector['id'], asset_id, pcd_sector['geotype']),
                    'build_year': None,
                    'frequency': '700',
                    'technology': '5G',
                    'type': 'macrocell_site',
                    'id': pcd_sector['id'].replace(' ', ''),
                    'technical_lifetime_value': 10,
                    'technical_lifetime_units': 'years',
                    'capex': 50917,
                    'opex': 2000,
                }
            )

            #add 3500 to site
            all_possible_assets.append(
                {
                    'name': 'macro_cell_{}_{}_{}_{}_{}'.format(
                        '3500', '5G', pcd_sector['id'], asset_id, pcd_sector['geotype']),
                    'build_year': None,
                    'frequency': '3500',
                    'technology': '5G',
                    'type': 'macrocell_site',
                    'id': pcd_sector['id'].replace(' ', ''),
                    'technical_lifetime_value': 10,
                    'technical_lifetime_units': 'years',
                    'capex': 50917,
                    'opex': 2000,
                }
            )

            #build 4G site
            all_possible_assets.append(
                {
                    'name': 'macro_cell_{}_{}_{}_{}_{}'.format(
                        'new', '4G', pcd_sector['id'], asset_id, pcd_sector['geotype']),
                    'build_year': None,
                    'frequency': ['800', '1800', '2600'],
                    'technology': '4G',
                    'type': 'macrocell_site',
                    'id': pcd_sector['id'].replace(' ', ''),
                    'technical_lifetime_value': 10,
                    'technical_lifetime_units': 'years',
                    'capex': 142446,
                    'opex': 10000,
                }
            )

            #build 5G site
            all_possible_assets.append(
                {
                    'name': 'macro_cell_{}_{}_{}_{}_{}'.format(
                        'new', '5G', pcd_sector['id'], asset_id, pcd_sector['geotype']),
                    'build_year': None,
                    'frequency': ['700', '800', '1800', '2600', '3500'],
                    'technology': '5G',
                    'type': 'macrocell_site',
                    'id': pcd_sector['id'].replace(' ', ''),
                    'technical_lifetime_value': 10,
                    'technical_lifetime_units': 'years',
                    'capex': 142446,
                    'opex': 10000,
                }
            )

        if pcd_sector['geotype'] == 'rural':

            pass

        else:

            max_small_cell_assets = find_maximum_required_assets('small_cells',
                pcd_sector['area_km2'], capacity_lookup)

            for asset_id in range(0, (max_small_cell_assets + 1)):

                #build small cell
                all_possible_assets.append(
                    {
                        'name': 'small_cell_{}_{}_{}_{}_{}'.format(
                            '3700', '5G', pcd_sector['id'], asset_id, pcd_sector['geotype']),
                        'build_year': None,
                        'frequency': '3700',
                        'technology': '5G',
                        'type': 'small_cell',
                        'id': pcd_sector['id'],
                        'capex': 12000,
                        'opex': 1000,
                        'technical_lifetime_value': 5,
                        'technical_lifetime_units': 'years',
                    }
                )

    return all_possible_assets


def csv_writer(data, directory, filename):
    """
    Write data to a CSV file path
    """
    # Create path
    if not os.path.exists(directory):
        os.makedirs(directory)

    fieldnames = []
    for name, value in data[0].items():
        fieldnames.append(name)

    with open(os.path.join(directory, filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)


if __name__ == '__main__':

    start = time.time()

    geotypes = [
        (7959, 'urban'),
        (782, 'suburban'),
        (0, 'rural'),
    ]

    print('Loading assets from digital_initial_conditions.csv')
    initial_conditions = load_initial_conditions()

    print('Loading postcode sectors')
    postcode_sectors = load_postcode_sectors(geotypes)

    print('Loading capacity lookup table')
    capacity_lookup = load_capacity_lookup_table(geotypes)

    print('Generating assets')
    assets = generate_assets(postcode_sectors, capacity_lookup, initial_conditions)

    print('Writing assets to .csv')
    directory = os.path.join(INTERMEDIATE, 'nismod2_inputs')
    csv_writer(assets, directory, 'digital_interventions.csv')

    end = time.time()
    print('time taken: {} minutes'.format(round((end - start) / 60,2)))
