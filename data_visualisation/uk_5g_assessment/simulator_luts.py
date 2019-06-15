import os
import configparser
import sys
import glob
import csv
import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..','..','scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA = os.path.join(BASE_PATH, 'intermediate', 'system_simulator')
DATA_OUTPUT = os.path.join(BASE_PATH, '..', 'data_visualisation', 'uk_5g_assessment')


def load_in_all_luts():

    filenames = glob.iglob(os.path.join(DATA, '**/*lookup*'), recursive=True)

    output = pd.concat((pd.read_csv(f) for f in filenames))

    output['capacity_per_Hz_km2'] = (
        output['area_capacity_mbps_km2'] / (output['bandwidth_MHz'] * 1e6)
        )

    output['site_density_km2'] = output.site_density_km2.round(1)

    return output


def lut_plot(data):

    area_types = [
        'urban',
        'suburban',
        # 'rural',
        'all'
    ]

    for area_type in area_types:

        if not area_type == 'all':
            plotting_data = data.loc[data['environment'] == area_type]

        else:
            plotting_data = data

        plotting_function(plotting_data, area_type)

    return ('complete')


def plotting_function(data, filename):

    data_subset = data[['site_density_km2','frequency_GHz','mast_height_m',
    'sinr', 'spectral_efficency_bps_hz', 'capacity_per_Hz_km2']]

    data_subset.columns = ['Density (Km^2)', 'Frequency (GHz)', 'Height (m)',
        'SINR', 'SE', 'Capacity']

    long_data = pd.melt(data_subset,
        id_vars=['Density (Km^2)', 'Frequency (GHz)', 'Height (m)'],
        value_vars=['SINR', 'SE', 'Capacity'])

    long_data.columns = ['Density (Km^2)', 'Frequency (GHz)', 'Height (m)',
        'Metric', 'Value']

    sns.set(font_scale=1.1)

    plot = sns.catplot(x='Density (Km^2)', y='Value', hue="Frequency (GHz)",
        kind="bar", col="Height (m)", row="Metric", data=long_data,
        sharey='row')

    plot.axes[0,0].set_ylabel('SINR (dB)')
    plot.axes[1,0].set_ylabel('SE (Bps/Hz)')
    plot.axes[2,0].set_ylabel('Capacity (Bps/Hz/Km^2)')

    plot.savefig(DATA_OUTPUT + '/capacity_plot_{}.png'.format(filename))

    return 'completed {}'.format(filename)


if __name__ == '__main__':

    data = load_in_all_luts()

    lut_plot(data)
