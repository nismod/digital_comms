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
from  matplotlib.ticker import FuncFormatter

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..','..','scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA = os.path.join(BASE_PATH, 'intermediate', 'system_simulator')
DATA_OUTPUT = os.path.join(BASE_PATH, '..', 'data_visualisation', 'uk_5g_assessment')


def load_in_all_main_lut():

    filenames = glob.iglob(os.path.join(DATA, '**/*test_lookup_table*'), recursive=True)

    output = pd.concat((pd.read_csv(f) for f in filenames))

    output['capacity_per_Hz_km2'] = (
        output['three_sector_capacity_mbps_km2'] / (output['bandwidth_MHz'] * 1e6)
        )

    output['sites_per_km2'] = output.sites_per_km2.round(1)

    output['inter_site_distance_km'] = output['inter_site_distance'] / 1e3

    return output


def plot_main_lut(data):

    data['environment'] = data['environment'].replace(
        {
            'urban': 'Urban',
            'suburban': 'Suburban',
            'rural': 'Rural'
        }
    )

    area_types = [
        # 'urban',
        # 'suburban',
        # 'rural',
        'all'
    ]

    for area_type in area_types:

        if not area_type == 'all':
            plotting_data = data.loc[data['environment'] == area_type]

        else:
            plotting_data = data

        # plotting_function1(plotting_data, area_type)

        # plotting_function2(plotting_data, area_type)

        plotting_function3(plotting_data, 'path_loss_dB', 'Path Loss (dB)')
        plotting_function3(plotting_data, 'received_power_dBm', 'Received Power (dBm)')
        plotting_function3(plotting_data, 'interference_dBm', 'Interference (dBm)')
        plotting_function3(plotting_data, 'sinr', 'SINR')
        plotting_function3(plotting_data, 'spectral_efficency_bps_hz', 'Spectral Efficiency (Bps/Hz)')
        plotting_function3(plotting_data, 'three_sector_capacity_mbps_km2', 'Average Capacity (Mbps/km^2)')

    return ('complete')


def plotting_function1(data, filename):

    data_subset = data[['sites_per_km2','frequency_GHz','mast_height_m',
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


def plotting_function2(data, filename):

    data_subset = data[['inter_site_distance_km','frequency_GHz','mast_height_m',
    'sinr', 'spectral_efficency_bps_hz', 'capacity_per_Hz_km2']]

    data_subset.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)',
        'SINR', 'SE', 'Capacity']

    data_subset = data_subset[data_subset['Inter-Site Distance (km)'].isin([
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])]

    long_data = pd.melt(data_subset,
        id_vars=['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)'],
        value_vars=['SINR', 'SE', 'Capacity'])

    long_data.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)',
        'Metric', 'Value']

    plot = sns.FacetGrid(long_data, row="Metric", col="Height (m)", hue="Frequency (GHz)",
    sharey='row')

    plot.map(sns.barplot, "Inter-Site Distance (km)", "Value").add_legend()

    plot.axes[0,0].set_ylabel('SINR (dB)')
    plot.axes[1,0].set_ylabel('SE (Bps/Hz)')
    plot.axes[2,0].set_ylabel('Capacity (Bps/Hz/Km^2)')

    plt.gca().xaxis.set_major_formatter(FuncFormatter(lambda x, _: int(x)))

    plt.subplots_adjust(hspace=0.2, wspace=0.3, bottom=0.06)

    plot.savefig(DATA_OUTPUT + '/capacity_barplot_{}.png'.format(filename))

    return 'completed {}'.format(filename)


def plotting_function3(data, metric_lower, metric_higher):

    data_subset = data[['inter_site_distance_km','frequency_GHz','mast_height_m',
    metric_lower, 'spectral_efficency_bps_hz', 'capacity_per_Hz_km2', 'environment']]

    data_subset.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)',
        metric_higher, 'SE', 'Capacity', 'Env']

    data_subset = data_subset[data_subset['Inter-Site Distance (km)'].isin([
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])]

    plot = sns.FacetGrid(data_subset, row="Env", col="Height (m)", hue="Frequency (GHz)")

    plot.map(sns.lineplot, "Inter-Site Distance (km)", metric_higher).add_legend()

    plt.subplots_adjust(hspace=0.2, wspace=0.2, bottom=0.06)

    plot.savefig(DATA_OUTPUT + '/{}_facet.png'.format(metric_lower))

    return 'completed {}'.format(metric_lower)


def load_in_individual_luts():

    filenames = glob.iglob(os.path.join(DATA, '**/*test_capacity_data*.csv'), recursive=True)

    output = pd.concat((pd.read_csv(f) for f in filenames))

    output['capacity_per_Hz_km2'] = (
        output['estimated_capacity'] / (output['bandwidth'] * 1e6)
        )

    output['sites_per_km2'] = output.sites_per_km2.round(1)

    output['inter_site_distance_km'] = output['inter_site_distance'] / 1e3

    return output


def plot_individual_luts(data):

    data = data[data['inter_site_distance_km'].isin([
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16])]

    # data['environment'] = data['environment'].replace(
    #     {
    #         'urban': 'Urban',
    #         'suburban': 'Suburban',
    #         'rural': 'Rural'
    #     }
    # )

    # data_subset = data[['inter_site_distance_km','frequency_GHz','mast_height_m',
    # metric_lower, 'spectral_efficency_bps_hz', 'capacity_per_Hz_km2', 'environment']]

    # data_subset.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)',
    #     metric_higher, 'SE', 'Capacity', 'Env']

    # plotting_function4(data, 'path_loss', 'Path Loss (dB)')
    # plotting_function4(data, 'received_power', 'Received Power (dBm)')
    # plotting_function4(data, 'interference', 'Interference (dBm)')
    # plotting_function4(data, 'sinr', 'SINR')
    # plotting_function4(data, 'spectral_efficiency', 'Spectral Efficiency (Bps/Hz)')
    # plotting_function4(data, 'estimated_capacity', 'Average Capacity (Mbps/km^2)')

    plotting_function5(data)

    plotting_function6(data)

    plotting_function7(data)

    return ('complete')


def plotting_function4(data, metric_lower, metric_higher):


    #environment	inter_site_distance	sites_per_km2	frequency	bandwidth	generation
    # mast_height	receiver_x	receiver_y	path_loss	received_power	interference
    # noise	sinr	spectral_efficiency	estimated_capacity

    # data_subset = data[['inter_site_distance_km','frequency_GHz','mast_height_m',
    # metric_lower, 'spectral_efficency_bps_hz', 'capacity_per_Hz_km2', 'environment']]

    # data_subset.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)',
    #     metric_higher, 'SE', 'Capacity', 'Env']

    long_data = pd.melt(data_subset,
        id_vars=['Density (Km^2)', 'Frequency (GHz)', 'Height (m)'],
        value_vars=['SINR', 'SE', 'Capacity'])

    long_data.columns = ['Density (Km^2)', 'Frequency (GHz)', 'Height (m)',
        'Metric', 'Value']


    ax = sns.lineplot(x="inter_site_distance", y=metric_lower, hue="environment",
        data=data, palette=sns.set_palette("husl"))

    # plot = sns.FacetGrid(data_subset, row="Env", col="Height (m)", hue="Frequency (GHz)")

    # plot.map(sns.lineplot, "Inter-Site Distance (km)", metric_higher).add_legend()

    # plt.subplots_adjust(hspace=0.2, wspace=0.2, bottom=0.06)

    ax.figure.savefig(DATA_OUTPUT + '/lineplot_{}.png'.format(metric_lower))

    plt.cla()

    return 'completed {}'.format(metric_lower)


def plotting_function5(data):


    #environment	inter_site_distance	sites_per_km2	frequency	bandwidth	generation
    # mast_height	receiver_x	receiver_y	path_loss	received_power	interference
    # noise	sinr	spectral_efficiency	estimated_capacity

    data_subset = data[['inter_site_distance_km','frequency','mast_height',
    'path_loss', 'received_power', 'interference', 'sinr', 'spectral_efficiency',
    'estimated_capacity', 'environment']]

    data_subset.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)',
        'Path Loss (DB)', 'Received Power (dB)', 'Interference (dB)', 'SINR',
        'SE', 'Capacity (Mbps/km^2)', 'Env']

    long_data = pd.melt(data_subset,
        id_vars=['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)', 'Env'],
        value_vars=['Path Loss (DB)', 'Received Power (dB)', 'Interference (dB)', 'SINR',
            'SE', 'Capacity (Mbps/km^2)'])

    long_data.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)',
    'Env', 'Metric', 'Value']

    ax = sns.relplot(x="Inter-Site Distance (km)", y='Value', hue="Env", row="Metric",
        col='Height (m)', kind="line", data=long_data, palette=sns.set_palette("husl"),
        facet_kws=dict(sharex=False, sharey=False),)

    # plot = sns.FacetGrid(data_subset, row="Env", col="Height (m)", hue="Frequency (GHz)")

    # plot.map(sns.lineplot, "Inter-Site Distance (km)", metric_higher).add_legend()

    # plt.subplots_adjust(hspace=0.2, wspace=0.2, bottom=0.06)

    ax.savefig(DATA_OUTPUT + '/facet_lineplot.png')

    plt.cla()

    return print('completed')


def plotting_function6(data):

    data_subset = data[['inter_site_distance_km','frequency','mast_height',
    'path_loss', 'received_power', 'interference', 'environment']]

    data_subset.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)',
        'Path Loss (DB)', 'Received Power (dB)', 'Interference (dB)', 'Env']

    long_data = pd.melt(data_subset,
        id_vars=['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)', 'Env'],
        value_vars=['Path Loss (DB)', 'Received Power (dB)', 'Interference (dB)'])

    long_data.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)',
    'Env', 'Metric', 'Value']

    ax = sns.relplot(x="Inter-Site Distance (km)", y='Value', hue="Env", row="Metric",
        col='Height (m)', kind="line", data=long_data, palette=sns.set_palette("husl"),
        facet_kws=dict(sharex=False, sharey=False),)

    # plot = sns.FacetGrid(data_subset, row="Env", col="Height (m)", hue="Frequency (GHz)")

    # plot.map(sns.lineplot, "Inter-Site Distance (km)", metric_higher).add_legend()

    # plt.subplots_adjust(hspace=0.2, wspace=0.2, bottom=0.06)

    ax.savefig(DATA_OUTPUT + '/facet_lineplot_1.png')

    plt.cla()

    return print('completed')


def plotting_function7(data):

    data_subset = data[['inter_site_distance_km','frequency','mast_height',
    'sinr', 'spectral_efficiency', 'estimated_capacity', 'environment']]

    data_subset.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)',
        'SINR', 'SE', 'Capacity (Mbps/km^2)', 'Env']

    long_data = pd.melt(data_subset,
        id_vars=['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)', 'Env'],
        value_vars=['SINR', 'SE', 'Capacity (Mbps/km^2)'])

    long_data.columns = ['Inter-Site Distance (km)', 'Frequency (GHz)', 'Height (m)',
    'Env', 'Metric', 'Value']

    ax = sns.relplot(x="Inter-Site Distance (km)", y='Value', hue="Env", row="Metric",
        col='Height (m)', kind="line", data=long_data, palette=sns.set_palette("husl"),
        facet_kws=dict(sharex=False, sharey=False),)

    # plot = sns.FacetGrid(data_subset, row="Env", col="Height (m)", hue="Frequency (GHz)")

    # plot.map(sns.lineplot, "Inter-Site Distance (km)", metric_higher).add_legend()

    # plt.subplots_adjust(hspace=0.2, wspace=0.2, bottom=0.06)

    ax.savefig(DATA_OUTPUT + '/facet_lineplot2.png')

    plt.cla()

    return print('completed')

if __name__ == '__main__':

    # data = load_in_all_main_lut()

    # plot_main_lut(data)

    individual_data = load_in_individual_luts()

    plot_individual_luts(individual_data)
