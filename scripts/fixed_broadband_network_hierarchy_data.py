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

def read_data_from_tomasso_valletti():
    data_from_tomasso_valletti = []

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'from_tomasso_valletti.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            data_from_tomasso_valletti.append({
                'exchange_id': line[0],
                'postcode': line[1]
            })

def read_pcp_data_2013():
    pcp_data_2013 = []

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'January 2013 PCP to Postcode File Part One.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcp_data_2013.append({
                'exchange_id': line[0],
                'name': line[1],
                'postcode': line[2],
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
                ###skip other unwanted variables
            })

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'January 2013 PCP to Postcode File Part Two.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcp_data_2013.append({
                'exchange_id': line[0],
                'name': line[1],
                'postcode': line[2],
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
                ###skip other unwanted variables
            })

    with open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'pcp_data_2013.csv'), 'w', newline='') as output_file:
        output_writer = csv.writer(output_file)

        # Write header
        output_writer.writerow(("exchange_id", "name", "postcode", "cabinet_id", "exchange_only_flag"))

        # Write data
        for line in pcp_data_2013:
            exchange_id = line['exchange_id']
            name = line['name']
            postcode = line['postcode']
            cabinet_id = line['cabinet_id']
            exchange_only_flag = line['exchange_only_flag']

            output_writer.writerow(
                (exchange_id, name, postcode, cabinet_id, exchange_only_flag))

    output_file.close()


def read_pcp_data_2011():
    pcp_data_2011 = []

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'pcp.to.pcd.dec.11.one.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcp_data_2011.append({
                'exchange_id': line[0],
                'name': line[1],
                'postcode': line[2],
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
                ###skip other unwanted variables
            })

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'pcp.to.pcd.dec.11.two.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcp_data_2011.append({
                'exchange_id': line[0],
                'name': line[1],
                'postcode': line[2],
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
                ###skip other unwanted variables
            })

    with open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'pcp_data_2011.csv'), 'w', newline='') as output_file:
        output_writer = csv.writer(output_file)

        # Write header
        output_writer.writerow(("exchange_id", "name", "postcode", "cabinet_id", "exchange_only_flag"))

        # Write data
        for line in pcp_data_2011:
            exchange_id = line['exchange_id']
            name = line['name']
            postcode = line['postcode']
            cabinet_id = line['cabinet_id']
            exchange_only_flag = line['exchange_only_flag']

            output_writer.writerow(
                (exchange_id, name, postcode, cabinet_id, exchange_only_flag))

    output_file.close()


if __name__ == "__main__":

    print('read pcp_data_2013')
    pcp_data_2013 = read_pcp_data_2013()

    print('read pcp_data_2011')
    pcp_data_2011 = read_pcp_data_2011()
