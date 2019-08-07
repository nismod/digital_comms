"""
Script to generate digital_mobile interventions.

Written by Ed Oughton
August 2019

"""
import csv
import configparser
import os
import glob

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

RAW = os.path.join(BASE_PATH, 'raw', 'b_mobile_model','mobile_model_1.0')
INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')

def load_postcode_sectors():
    """
    Load in postcode sector information.

    """
    pcd_sectors = []
    PCD_SECTOR_FILENAME = os.path.join(
        BASE_PATH, 'processed', '_processed_postcode_sectors.csv'
        )

    with open(PCD_SECTOR_FILENAME, 'r') as source:
        reader = csv.DictReader(source)
        for pcd_sector in reader:
            pcd_sectors.append({
                "id": pcd_sector['postcode'].replace(" ", ""),
                "lad_id": pcd_sector['lad'],
                "area": float(pcd_sector['area']) / 1e6
            })

    return pcd_sectors


def load_capacity_lookup_table():

    PATH_LIST = glob.iglob(os.path.join(INTERMEDIATE,
        'system_simulator', '**/*test_lookup_table*.csv'), recursive=True)

    capacity_lookup_table = {}

    for path in PATH_LIST:
        with open(path, 'r') as capacity_lookup_file:
            reader = csv.DictReader(capacity_lookup_file)
            for row in reader:
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


def generate_assets(postcode_sectors, number_of_assets_per_area):

    all_possible_assets = []

    for pcd_sector in postcode_sectors:
        for asset_id in range(0, number_of_assets_per_area):
            #add 800 to site
            all_possible_assets.append(
                {
                    'id': 'macrocell_add_{}_{}_{}'.format(
                        '800', pcd_sector['id'], asset_id),
                    'frequency': '800',
                    'technology': '4G',
                    'type': 'macrocell_site',
                    'pcd_sector': pcd_sector['id'].replace(' ', ''),
                    'technical_lifetime': '10',
                    'capex': 50917,
                    'opex': 2000,
                }
            )
            #add 1800 to site
            all_possible_assets.append(
                {
                    'id': 'macrocell_add_{}_{}_{}'.format(
                        '1800', pcd_sector['id'], asset_id),
                    'frequency': '1800',
                    'technology': '4G',
                    'type': 'macrocell_site',
                    'pcd_sector': pcd_sector['id'].replace(' ', ''),
                    'technical_lifetime': '10',
                    'capex': 50917,
                    'opex': 2000,
                }
            )
            #add 2600 to site
            all_possible_assets.append(
                {
                    'id': 'macrocell_add_{}_{}_{}'.format(
                        '2600', pcd_sector['id'], asset_id),
                    'frequency': '2600',
                    'technology': '4G',
                    'type': 'macrocell_site',
                    'pcd_sector': pcd_sector['id'].replace(' ', ''),
                    'technical_lifetime': '10',
                    'capex': 50917,
                    'opex': 2000,
                }
            )
            #add 700 to site
            all_possible_assets.append(
                {
                    'id': 'macrocell_add_{}_{}_{}'.format(
                        '700', pcd_sector['id'], asset_id),
                    'frequency': '700',
                    'technology': '5G',
                    'type': 'macrocell_site',
                    'pcd_sector': pcd_sector['id'].replace(' ', ''),
                    'technical_lifetime': '10',
                    'capex': 50917,
                    'opex': 2000,
                }
            )
            #add 3500 to site
            all_possible_assets.append(
                {
                    'id': 'macrocell_add_{}_{}_{}'.format(
                        '3500', pcd_sector['id'], asset_id),
                    'frequency': '3500',
                    'technology': '5G',
                    'type': 'macrocell_site',
                    'pcd_sector': pcd_sector['id'].replace(' ', ''),
                    'technical_lifetime': '10',
                    'capex': 50917,
                    'opex': 2000,
                }
            )
            #build 4G site
            all_possible_assets.append(
                {
                    'id': 'macro_cell_{}_{}'.format(
                        pcd_sector['id'], asset_id),
                    'frequency': ['800', '1800', '2600'],
                    'technology': '4G',
                    'type': 'macrocell_site',
                    'pcd_sector': pcd_sector['id'].replace(' ', ''),
                    'technical_lifetime': '10',
                    'capex': 142446,
                    'opex': 10000,
                }
            )
            #build 5G site
            all_possible_assets.append(
                {
                    'id': 'macro_cell_{}_{}'.format(
                        pcd_sector['id'], asset_id),
                    'frequency': ['700', '800', '1800', '2600', '3500'],
                    'technology': '5G',
                    'type': 'macrocell_site',
                    'pcd_sector': pcd_sector['id'].replace(' ', ''),
                    'technical_lifetime': '10',
                    'capex': 142446,
                    'opex': 10000,
                }
            )
            #build small cell
            all_possible_assets.append(
                {
                    'id': 'small_cell_{}_{}'.format(
                        pcd_sector['id'], asset_id),
                    'frequency': '3700',
                    'technology': '5G',
                    'type': 'small_cell',
                    'pcd_sector': pcd_sector['id'],
                    'capex': 12000,
                    'opex': 1000,
                    'technical_lifetime': 5,
                }
            )

    return all_possible_assets


def csv_writer(data, filename):
    """
    Write data to a CSV file path
    """
    # Create path
    directory = os.path.join(INTERMEDIATE, 'nismod2_interventions')
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

    number_of_assets_per_area = 50

    print('Loading postcode sectors')
    postcode_sectors = load_postcode_sectors()

    # print('Loading capacity lookup table')
    # capacity_lookup = load_capacity_lookup_table()

    print('Generating assets')
    assets = generate_assets(postcode_sectors, number_of_assets_per_area)

    print('Writing assets to .csv')
    csv_writer(assets, 'digital_interventions.csv')
