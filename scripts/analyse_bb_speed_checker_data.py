"""Extract lad id, name
"""
import configparser
import csv
import os

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['Broadband Speed Checker']
INPUT_FILENAME = os.path.join(BASE_PATH, 'UniversityOfCambrigeFinalReport.csv')


