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

DATA = os.path.join(BASE_PATH, '..', 'results', 'mobile_outputs')
DATA_OUTPUT = os.path.join(BASE_PATH, '..', 'data_visualisation', 'uk_5g_assessment')


def load_in_results():

    filenames = glob.iglob(os.path.join(DATA, '*metrics*'))

    data = []
    for filename in filenames:
        df = pd.read_csv(filename)
        base = os.path.basename(filename).split('_')
        df['scenario_pop'] = base[1][4:]
        df['scenario_data'] = base[2][11:]
        df['strategy'] = base[3][9:-4]
        data.append(df)

    output = pd.concat(data)

    return output


def aggregate_data(data):

    # average_demand = data.groupby([
    #     'year','scenario_pop','scenario_data','strategy'
    #     ])['demand'].mean('demand_mean')

    # plotting_function(average_demand, 'average_demand')

    average_capacity = data.groupby([
        'year','scenario_pop','scenario_data','strategy'
        ]).mean('capacity_mean')

    plotting_function(average_capacity, 'average_capacity')
    # print(data.head())
    data.groupby('total', as_index=False).agg({"year": "sum"})

    # aggreagted_costs = data.groupby('year','scenario_pop','scenario_data','strategy', as_index=False).agg({"cost": "sum"})

    # aggreagted_costs.plot(kind='bar')

    # # aggreagted_costs['cost'] = aggreagted_costs.index

    # print(aggreagted_costs)
    # # sns.set(style="ticks")
    # # data.groupby('month')['duration'].sum()
    # # palette = dict(zip(dots.coherence.unique(),
    # #                 sns.color_palette("rocket_r", 6)))

    # # Plot the lines on two facets
    # plot = sns.relplot(x="year", y="cost",
    #             kind="line", legend="full", data=aggreagted_costs)

    # plot.savefig(DATA_OUTPUT + '/cost_{}.png'.format(aggreagted_costs))

    return print('completed')


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

    data = load_in_results()

    aggregated_data = aggregate_data(data)

    # lut_plot(data)
