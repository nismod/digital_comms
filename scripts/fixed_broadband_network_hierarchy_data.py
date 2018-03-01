import os
from pprint import pprint
import configparser
import csv

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################
# setup file locations
#####################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'raw', 'network_hierarchy_data')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'processed')

def read_all_data():
    """
    This function reads in various different sources of data.

    pcp_data contains any postcode-to-cabinet-to-exchange information.

    pcd_to_exchange_data contains any postcode-to-exchange information.

    pcd_to_exchange_data_unique contains unique postcode-to-cabinet-to-exchange combinations

    pcp_data and pcd_to_exchange_data_unique are then written out to .csv

    """

    pcp_data = []
    pcd_to_exchange_data = []

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'January 2013 PCP to Postcode File Part One.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcp_data.append({
                'exchange_id': line[0],
                'name': line[1],
                'postcode': line[2].replace(" ", ""),
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
            })

        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'January 2013 PCP to Postcode File Part Two.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcp_data.append({
                'exchange_id': line[0],
                'name': line[1],
                'postcode': line[2].replace(" ", ""),
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
                ###skip other unwanted variables
            })

        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'pcp.to.pcd.dec.11.one.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcp_data.append({
                'exchange_id': line[0],
                'name': line[1],
                'postcode': line[2].replace(" ", ""),
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
                ###skip other unwanted variables
            })

        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'pcp.to.pcd.dec.11.two.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcp_data.append({
                'exchange_id': line[0],
                'name': line[1],
                'postcode': line[2].replace(" ", ""),
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
                ###skip other unwanted variables
            })

        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'from_tomasso_valletti.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })


    ### find unique values in list of dicts
    pcd_to_exchange_data_unique = list({pcd['postcode']:pcd for pcd in pcd_to_exchange_data}.values())

    print('the total number of unique postcodes is: {}'.format(len(pcd_to_exchange_data_unique)))

    with open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'pcp_data.csv'), 'w', newline='') as output_file:
        output_writer = csv.writer(output_file)

        # Write header
        output_writer.writerow(("exchange_id", "name", "postcode", "cabinet_id", "exchange_only_flag"))

        # Write data
        for line in pcp_data:
            exchange_id = line['exchange_id']
            name = line['name']
            postcode = line['postcode']
            cabinet_id = line['cabinet_id']
            exchange_only_flag = line['exchange_only_flag']

            output_writer.writerow(
                (exchange_id, name, postcode, cabinet_id, exchange_only_flag))

    output_file.close()

    with open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'pcd_to_exchange_data.csv'), 'w', newline='') as output_file:
        output_writer = csv.writer(output_file)

        # Write header
        output_writer.writerow(("exchange_id", "postcode"))

        # Write data
        for line in pcd_to_exchange_data_unique:
            exchange_id = line['exchange_id']
            postcode = line['postcode']

            output_writer.writerow(
                (exchange_id, postcode))

    output_file.close()

if __name__ == "__main__":

    print('read all_data')

    all_data = read_all_data()



