import os
import configparser
import sys
import glob
import pandas as pd
import geopandas
import contextily as ctx

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..','..','scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA = os.path.join(BASE_PATH, 'intermediate', 'system_simulator')
DATA_OUTPUT = os.path.join(BASE_PATH, '..', 'data_visualisation', 'uk_5g_assessment')
