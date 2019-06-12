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

    filenames = glob.iglob(os.path.join(DATA, '**/*.csv'), recursive=True)

    output = pd.concat((pd.read_csv(f) for f in filenames))

    # for name in filenames:
    #     with open(name, 'r') as source:
    #         reader = csv.DictReader(source)
    #         for row in reader:
    #             output.append({
    #                 'environment': row['environment'],
    #                 'technology': row['technology'],
    #                 'frequency_GHz': row['frequency_GHz'],
    #                 'bandwidth_MHz': row['bandwidth_MHz'],
    #                 'mast_height_m': row['mast_height_m'],
    #                 'num_sites': int(row['num_sites']),
    #                 'site_density_km2': float(row['site_density_km2']),
    #                 'generation': row['generation'],
    #                 'received_power_dBm': float(row['received_power_dBm']),
    #                 'interference_dBm': float(row['interference_dBm']),
    #                 'noise_dBm': float(row['noise_dBm']),
    #                 'i_plus_n_dBm': float(row['i_plus_n_dBm']),
    #                 'sinr': float(row['sinr']),
    #                 'spectral_efficency_bps_hz': float(row['spectral_efficency_bps_hz']),
    #                 'single_sector_capacity_mbps_km2': float(row['single_sector_capacity_mbps_km2']),
    #                 'area_capacity_mbps_km2': float(row['area_capacity_mbps_km2']),
    #             })

    output['capacity_per_Hz_km2'] = (
        output['area_capacity_mbps_km2'] / (output['bandwidth_MHz'] * 1e6)
        )

    output['site_density_km2'] = output.site_density_km2.round(1)

    return output


def lut_plot(data):

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

    plot.savefig(DATA_OUTPUT + '/capacity_plot.png')

    return ('complete')


if __name__ == '__main__':

    data = load_in_all_luts()

    lut_plot(data)



# # # import matplotlib.pyplot as plt
# # # from matplotlib.dates import date2num
# # # import datetime
# # # import numpy as np
# # # data = [[5., 25., 50., 20.],
# # #   [4., 23., 51., 17.],
# # #   [6., 22., 52., 19.]]

# # # X = np.arange(4)
# # # plt.bar(X + 0.00, data[0], color = 'b', width = 0.25)
# # # plt.bar(X + 0.25, data[1], color = 'g', width = 0.25)
# # # plt.bar(X + 0.50, data[2], color = 'r', width = 0.25)

# # # plt.show()





# # tips = sns.load_dataset("tips")
# # f, axes = plt.subplots(1, 2, sharey=True, figsize=(6, 4))
# # sns.boxplot(x="day", y="tip", data=tips, ax=axes[0])
# # sns.scatterplot(x="total_bill", y="tip", hue="day", data=tips, ax=axes[1])
# # plt.show()


# First create some toy data:
# x = np.linspace(0, 2*np.pi, 400)
# y = np.sin(x**2)

# # Creates just a figure and only one subplot
# fig, ax = plt.subplots()
# ax.plot(x, y)
# ax.set_title('Simple plot')

# # Creates two subplots and unpacks the output array immediately
# f, (ax1, ax2) = plt.subplots(1, 2, sharey=True)
# ax1.plot(x, y)
# ax1.set_title('Sharing Y axis')
# ax2.scatter(x, y)

# Creates four polar axes, and accesses them through the returned array
# fig, axes = plt.subplots(2, 2, subplot_kw=dict(polar=True))
# axes[0, 0].plot(x, y)
# axes[1, 1].scatter(x, y)

# Share a X axis with each column of subplots
# plt.subplots(2, 2, sharex='col')
# plt.show()

# # Share a Y axis with each row of subplots
# plt.subplots(2, 2, sharey='row')

# # Share both X and Y axes with all subplots
# plt.subplots(2, 2, sharex='all', sharey='all')

# # Note that this is the same as
# plt.subplots(2, 2, sharex=True, sharey=True)

# # Creates figure number 10 with a single subplot
# # and clears it if it already exists.
# fig, ax=plt.subplots(num=10, clear=True)

    # g.despine(left=True)
    # g.set_ylabels("survival probability")
    # sns.catplot(x='site_density_km2', y='received_power_dBm', hue="frequency_GHz",
    #     kind="bar", data=thirty_m, ax=axs[0,0])
    # sns.catplot(x='site_density_km2', y='received_power_dBm', hue="frequency_GHz",
    #     kind="bar", data=forty_m, ax=axs[0,1])

    # sns.catplot(x='site_density_km2', y='i_plus_n_dBm', hue="frequency_GHz",
    #     kind="bar", data=thirty_m, ax=axs[1,0])
    # sns.catplot(x='site_density_km2', y='i_plus_n_dBm', hue="frequency_GHz",
    #     kind="bar", data=forty_m, ax=axs[1,1])

    # sns.catplot(x='site_density_km2', y='sinr', hue="frequency_GHz",
    #     kind="bar", data=thirty_m, ax=axs[2,0])
    # sns.catplot(x='site_density_km2', y='sinr', hue="frequency_GHz",
    #     kind="bar", data=forty_m, ax=axs[2,1])

    # sns.catplot(x='site_density_km2', y='capacity_per_MHz_km2', hue="frequency_GHz",
    #     kind="bar", data=thirty_m, ax=axs[3,0])
    # sns.catplot(x='site_density_km2', y='capacity_per_MHz_km2', hue="frequency_GHz",
    #     kind="bar", data=forty_m, ax=axs[3,1])
