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


def transform_data_labels(data):

    data = data.rename(index=str,
        columns =
        {
            'year': 'Year',
            'area_id': 'Area',
            'area_name': 'Name',
            'capex': 'Capex',
            'opex': 'opex',
            'demand': 'Demand (Mbps/km^2)',
            'capacity': 'Capacity (Mbps/km^2)',
            'capacity_deficit': 'Capacity Margin (Mbps/km^2)',
            'population': 'Population',
            'area': 'Area (km^2)',
            'pop_density': 'Population Density (Persons per km^2)',
            'scenario_pop': 'Population Scenario',
            'scenario_data': 'Data Scenario',
            'strategy': 'Strategy'
        }
    )

    data['Data Scenario'] = data['Data Scenario'].replace(
        {
            'low': 'Low',
            'base': 'Baseline',
            'high': 'High'
        }
    )

    data['Population Scenario'] = data['Population Scenario'].replace(
        {
            'low': 'Low',
            'base': 'Baseline',
            'high': 'High'
        }
    )


    data['Strategy'] = data['Strategy'].replace(
        {
            'minimal': 'No Investment',
            'macrocell-700-3500': 'Spectrum Integration',
            'deregulation': 'Deregulation',
            'macro-densification': 'Macro Densification',
            'small-cell-and-spectrum': 'Hybrid Deployment'
        }
    )

    return data

def aggregate_data(data):

    data = data[data['Strategy'] != 'minimal']

    average_capacity = data.groupby([
        'Year','Population Scenario','Data Scenario','Strategy'
        ]).mean().reset_index()

    plot = plotting_function(average_capacity, 'average_capacity')


    # plot = sns.relplot(x="year", y="capex",
    #             kind="line", legend="full", data=average_capacity)

    # figure = plot.fig
    # figure.savefig(os.path.join(DATA_OUTPUT + '/cost_average_capacity.png'))

    # data.groupby('total', as_index=False).agg({"year": "sum"})

    # aggreagted_costs = data.groupby('year','scenario_pop','scenario_data','strategy', as_index=False).agg({"cost": "sum"})

    # aggreagted_costs.plot(kind='bar')

    # # aggreagted_costs['cost'] = aggreagted_costs.index

    # print(aggreagted_costs)
    # # sns.set(style="ticks")
    # # data.groupby('month')['duration'].sum()
    # # palette = dict(zip(dots.coherence.unique(),
    # #                 sns.color_palette("rocket_r", 6)))

    return print('completed')


def plotting_function(data, filename):


    sns.set(font_scale=1.1)

    plot = sns.catplot(x='Year', y='Capex', kind="bar",
        col="Population Scenario",
        row="Strategy", row_order=[
            "Spectrum Integration",
            "Deregulation",
            "Macro Densification",
            "Hybrid Deployment"
            ], sharex=False, data=data)

    [plt.setp(ax.get_xticklabels(), rotation=45) for ax in plot.axes.flat]
    plot.axes[0,0].set_ylabel('Capex (£Bn)')
    plot.axes[1,0].set_ylabel('Capex (£Bn)')
    plot.axes[2,0].set_ylabel('Capex (£Bn)')
    plot.axes[3,0].set_ylabel('Capex (£Bn)')
    plt.subplots_adjust(hspace=0.4, wspace=0.4)

    plot.savefig(DATA_OUTPUT + '/capacity_plot_{}.png'.format(filename))

    return 'completed {}'.format(filename)


if __name__ == '__main__':

    data = load_in_results()

    data = transform_data_labels(data)

    aggregated_data = aggregate_data(data)

    # lut_plot(data)
