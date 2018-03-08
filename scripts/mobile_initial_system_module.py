import os
from pprint import pprint
import configparser
import csv
from math import ceil

WRITE_INTERMEDIATE_FILES = True

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################
# setup file locations
#####################

SYSTEM_INPUT_FILENAME = os.path.join(BASE_PATH, 'Digital Comms - Fixed broadband model', 'Data', 'initial_system')

SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'Digital Comms - Fixed broadband model', 'initial_system')

initial_system = {}

YEARS = ['2016', '2017']

#####################
# read in codepoint
#####################

SYSTEM_CODEPOINT_LOCATION = os.path.join(BASE_PATH, 'Digital Comms - Fixed broadband model', 'Data', 'codepoint')

codepoint = []

directory = os.path.join(SYSTEM_CODEPOINT_LOCATION)
for root, directories, files in os.walk(directory):
    for file in files:
        if file.endswith(".csv") and file.startswith("cb"):
            with open(os.path.join(root, file), 'r') as system_file:
                reader = csv.reader(system_file)
                for line in reader:
                    codepoint.append({
                        'postcode': line[0].replace(" ", ""), #remove whitespace in string
                        'PO_Box': line[2],
                        'total_delivery_points': line[3],
                        'domestic_delivery_points': line[5],
                        'non_domestic_delivery_points': line[6],
                        'PO_Box_delivery_points': line[6],
                        'eastings': line[10],
                        'northings': line[11],
                        'country': line[12],
                        'district': line[16],
                        'ward': line[17],
                        'pcd_type': line[18],
                    })

if WRITE_INTERMEDIATE_FILES:
    with open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'codepoint.csv'), 'w', newline='') as output_file:
        output_writer = csv.writer(output_file)

        # Write header
        output_writer.writerow(("postcode", "PO_Box", "total_delivery_points", "domestic_delivery_points",
                                "non_domestic_delivery_points", "PO_Box_delivery_points", "eastings",
                                "northings", "country", "district", "ward", "pcd_type"))

        # Write data
        for line in codepoint:
            # so by using a for loop, we're accessing each element in the list.
            # each postcode is then a dict, so we need to index into each dict item
            postcode = line['postcode']
            PO_Box = line['PO_Box']
            total_delivery_points = line['total_delivery_points']
            domestic_delivery_points = line['domestic_delivery_points']
            non_domestic_delivery_points = line['non_domestic_delivery_points']
            PO_Box_delivery_points = line['PO_Box_delivery_points']
            eastings = line['eastings']
            northings = line['northings']
            country = line['country']
            district = line['district']
            ward = line['ward']
            pcd_type = line['pcd_type']

            output_writer.writerow(
                (postcode, PO_Box, total_delivery_points, domestic_delivery_points,
                non_domestic_delivery_points, PO_Box_delivery_points, eastings,
                northings, country, district, ward, pcd_type))

    output_file.close()

#####################
# read in files for 2016 and 2017
#####################

initial_system = {}

for year in YEARS:
    for fixed_pcd_file in os.listdir(SYSTEM_INPUT_FILENAME):
        if fixed_pcd_file.startswith(year):
            with open(os.path.join(SYSTEM_INPUT_FILENAME, fixed_pcd_file), 'r') as system_file:
                reader = csv.reader(system_file)
                next(reader)  # skip header
                for line in reader:
                    initial_system[line[0]] = {
                        'postcode': line[0],
                        'SFBB': (int(line[3])/100),
                        'UFBB': (int(line[4])/100)
                    }

            merged_codepoint = []
            non_matching_codepoint = []

            #print("Start merge 1")
            for point in codepoint:
                #specifically target the small delivery points, following Ofcom's methodology
                if point['pcd_type'] == "S":
                    try:
                        merged_codepoint.append({
                            'postcode': point['postcode'],
                            'PO_Box': point['PO_Box'],
                            'total_delivery_points': point['total_delivery_points'],
                            'domestic_and_SME_delivery_points': 0,
                            'domestic_delivery_points': point['domestic_delivery_points'],
                            'non_domestic_delivery_points': point['non_domestic_delivery_points'],
                            'PO_Box_delivery_points': point['PO_Box_delivery_points'],
                            'eastings': point['eastings'],
                            'northings': point['northings'],
                            'country': point['country'],
                            'district': point['district'],
                            'ward': point['ward'],
                            'pcd_type': point['pcd_type'],
                            'SFBB': initial_system[point['postcode']]['SFBB'],
                            'UFBB': initial_system[point['postcode']]['UFBB'],
                        })
                    except KeyError as e:
                        pass

            for item in merged_codepoint:
                item['SFBB'] = ceil(int(item['total_delivery_points']) * float(item['SFBB']))
                item['UFBB'] = ceil(int(item['total_delivery_points']) * float(item['UFBB']))

            if WRITE_INTERMEDIATE_FILES:
            # write files for 2016 and 2017
                with open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'fixed_postcode_' + str(year) + '.csv'), 'w', newline='') as output_file:
                    output_writer = csv.writer(output_file)

                    # Write header
                    output_writer.writerow(("postcode", "PO_Box", "total_delivery_points", "domestic_delivery_points",
                                            "non_domestic_delivery_points", "PO_Box_delivery_points", "eastings",
                                            "northings", "country", "district", "ward", "pcd_type", "SFBB", "UFBB"))
                    # Write data
                    for merged_cp in merged_codepoint:
                        # so by using a for loop, we're accessing each element in the list.
                        # each postcode is then a dict, so we need to index into each dict item
                        postcode = merged_cp['postcode']
                        PO_Box = merged_cp['PO_Box']
                        total_delivery_points = merged_cp['total_delivery_points']
                        domestic_delivery_points = merged_cp['domestic_delivery_points']
                        non_domestic_delivery_points = merged_cp['non_domestic_delivery_points']
                        PO_Box_delivery_points = merged_cp['PO_Box_delivery_points']
                        eastings = merged_cp['eastings']
                        northings = merged_cp['northings']
                        country = merged_cp['country']
                        district = merged_cp['district']
                        ward = merged_cp['ward']
                        pcd_type = merged_cp['pcd_type']
                        SFBB = merged_cp['SFBB']
                        UFBB = merged_cp['UFBB']

                        output_writer.writerow(
                            (postcode, PO_Box, total_delivery_points, domestic_delivery_points,
                            non_domestic_delivery_points, PO_Box_delivery_points, eastings,
                            northings, country, district, ward, pcd_type, SFBB, UFBB))

                output_file.close()

#####################
# read files for 2015
#####################

initial_system = {}

with open(os.path.join(SYSTEM_INPUT_FILENAME, 'Fixed_Postcode_2015_updated_01022016.csv'), 'r') as system_file:
    reader = csv.reader(system_file)
    next(reader)  # skip header
    for line in reader:
        initial_system[line[0]] = {
            'postcode': line[0],
            'SFBB': (int(line[2])/100),
            'UFBB': (int(line[3])/100),
        }

merged_codepoint = []
non_matching_codepoint = []

for point in codepoint:
    #specifically target the small delivery points, following Ofcom's methodology
    if point['pcd_type'] == "S":
        try:
            merged_codepoint.append({
                'postcode': point['postcode'],
                'PO_Box': point['PO_Box'],
                'total_delivery_points': point['total_delivery_points'],
                'domestic_delivery_points': point['domestic_delivery_points'],
                'non_domestic_delivery_points': point['non_domestic_delivery_points'],
                'PO_Box_delivery_points': point['PO_Box_delivery_points'],
                'eastings': point['eastings'],
                'northings': point['northings'],
                'country': point['country'],
                'district': point['district'],
                'ward': point['ward'],
                'pcd_type': point['pcd_type'],
                'SFBB': initial_system[point['postcode']]['SFBB'],
                'UFBB': initial_system[point['postcode']]['UFBB']
            })
        except KeyError as e:
            pass

for item in merged_codepoint:
    item['SFBB'] = ceil(int(item['total_delivery_points']) * float(item['SFBB']))
    item['UFBB'] = ceil(int(item['total_delivery_points']) * float(item['UFBB']))

if WRITE_INTERMEDIATE_FILES:
    with open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'fixed_postcode_2015.csv'), 'w', newline='') as output_file:
        output_writer = csv.writer(output_file)

        # Write header
        output_writer.writerow(("postcode", "PO_Box", "total_delivery_points", "domestic_delivery_points",
                    "non_domestic_delivery_points", "PO_Box_delivery_points", "eastings",
                    "northings", "country", "district", "ward", "pcd_type", "SFBB", "UFBB"))

        # Write data
        for merged_cp in merged_codepoint:
            # so by using a for loop, we're accessing each element in the list.
            # each postcode is then a dict, so we need to index into each dict item
            postcode = merged_cp['postcode']
            PO_Box = merged_cp['PO_Box']
            total_delivery_points = merged_cp['total_delivery_points']
            domestic_delivery_points = merged_cp['domestic_delivery_points']
            non_domestic_delivery_points = merged_cp['non_domestic_delivery_points']
            PO_Box_delivery_points = merged_cp['PO_Box_delivery_points']
            eastings = merged_cp['eastings']
            northings = merged_cp['northings']
            country = merged_cp['country']
            district = merged_cp['district']
            ward = merged_cp['ward']
            pcd_type = merged_cp['pcd_type']
            SFBB = merged_cp['SFBB']
            UFBB = merged_cp['UFBB']

            output_writer.writerow(
                (postcode, PO_Box, total_delivery_points, domestic_delivery_points,
                non_domestic_delivery_points, PO_Box_delivery_points, eastings,
                northings, country, district, ward, pcd_type, SFBB, UFBB))

    output_file.close()

#####################
# read files for 2014
#####################

if WRITE_INTERMEDIATE_FILES:
    with open(os.path.join(SYSTEM_INPUT_FILENAME, 'fixed_postcode_2014_CB.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader)  # skip header
        for line in reader:
            initial_system[line[0]] = {
                'postcode': line[0],
                'SFBB': (int(line[2])/100),
            }

        merged_codepoint = []
        non_matching_codepoint = []

        for point in codepoint:
            #specifically target the small delivery points, following Ofcom's methodology
            if point['pcd_type'] == "S":
                try:
                    merged_codepoint.append({
                        'postcode': point['postcode'],
                        'PO_Box': point['PO_Box'],
                        'total_delivery_points': point['total_delivery_points'],
                        'domestic_delivery_points': point['domestic_delivery_points'],
                        'non_domestic_delivery_points': point['non_domestic_delivery_points'],
                        'PO_Box_delivery_points': point['PO_Box_delivery_points'],
                        'eastings': point['eastings'],
                        'northings': point['northings'],
                        'country': point['country'],
                        'district': point['district'],
                        'ward': point['ward'],
                        'pcd_type': point['pcd_type'],
                        'SFBB': initial_system[point['postcode']]['SFBB'],
                        'UFBB': 0
                    })
                except KeyError as e:
                    pass

        for item in merged_codepoint:
            item['SFBB'] = ceil(int(item['total_delivery_points']) * float(item['SFBB']))
            item['UFBB'] = ceil(int(item['total_delivery_points']) * float(item['UFBB']))

if WRITE_INTERMEDIATE_FILES:
    with open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'fixed_postcode_2014.csv'), 'w', newline='') as output_file:
        output_writer = csv.writer(output_file)

        # Write header
        output_writer.writerow(("postcode", "PO_Box", "total_delivery_points", "domestic_delivery_points",
                    "non_domestic_delivery_points", "PO_Box_delivery_points", "eastings",
                    "northings", "country", "district", "ward", "pcd_type", "SFBB", "UFBB"))

        # Write data
        for merged_cp in merged_codepoint:
            # so by using a for loop, we're accessing each element in the list.
            # each postcode is then a dict, so we need to index into each dict item
            postcode = merged_cp['postcode']
            PO_Box = merged_cp['PO_Box']
            total_delivery_points = merged_cp['total_delivery_points']
            domestic_delivery_points = merged_cp['domestic_delivery_points']
            non_domestic_delivery_points = merged_cp['non_domestic_delivery_points']
            PO_Box_delivery_points = merged_cp['PO_Box_delivery_points']
            eastings = merged_cp['eastings']
            northings = merged_cp['northings']
            country = merged_cp['country']
            district = merged_cp['district']
            ward = merged_cp['ward']
            pcd_type = merged_cp['pcd_type']
            SFBB = merged_cp['SFBB']
            UFBB = merged_cp['UFBB']

            output_writer.writerow(
                (postcode, PO_Box, total_delivery_points, domestic_delivery_points,
                non_domestic_delivery_points, PO_Box_delivery_points, eastings,
                northings, country, district, ward, pcd_type, SFBB, UFBB))

    output_file.close()

