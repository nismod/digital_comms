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
import imageio

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..','..','scripts', 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA = os.path.join(BASE_PATH, '..', 'results', 'mobile_outputs')
DATA_OUTPUT_PLOTS = os.path.join(BASE_PATH,'..','data_visualisation','uk_5g_assessment','plots')
DATA_OUTPUT_GIFS = os.path.join(BASE_PATH,'..','data_visualisation','uk_5g_assessment','gifs')

def load_in_lad_results():

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


def transform_lad_data_labels(data):

    data = data.rename(index=str,
        columns =
        {
            'year': 'Year',
            'area_id': 'Area ID',
            'area_name': 'Name',
            'capex': 'Capex',
            'opex': 'Opex',
            'demand': 'Demand',
            'capacity': 'Capacity',
            'capacity_deficit': 'Capacity Margin',
            'population': 'Population',
            'area': 'Area',
            'pop_density': 'Population Density',
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

    #data scenario and population scenario should be the same,
    #so one can just be copied for the general scenario
    data['Scenario'] = data['Population Scenario']

    data['Strategy'] = data['Strategy'].replace(
        {
            'minimal': 'No Investment',
            'macrocell-700-3500': 'Spectrum Integration',
            'deregulation': 'Deregulation',
            'macro-densification': 'Macro Densification',
            'small-cell-and-spectrum': 'Hybrid Deployment'
        }
    )

    data['Capex'] = data['Capex'] / 1e6

    data['Opex'] = data['Opex'] / 1e3

    return data


def strategy_line_plots(data, filename):

    data = data[['Year', 'Scenario', 'Strategy',
        'Capacity', 'Capacity Margin',
        'Capex', 'Opex']]

    data = data.groupby([
        'Year', 'Scenario', 'Strategy'
        ]).median().reset_index()

    long_data = pd.melt(data,
        id_vars=['Year', 'Scenario', 'Strategy'],
        value_vars=['Capacity', 'Capacity Margin',
        'Capex', 'Opex']
        )

    long_data.columns = ['Year', 'Scenario', 'Strategy',
        'Metric', 'Value']

    sns.set(font_scale=1.3)

    palette = dict(zip(long_data.Strategy.unique(),
        sns.color_palette("Set2", 5)))

    plot = sns.relplot(x='Year', y='Value',
        hue='Strategy', hue_order=["No Investment", "Spectrum Integration",
            "Deregulation", "Macro Densification", "Hybrid Deployment"],
        col="Scenario", col_order=["Low", "Baseline", "High",],
        row="Metric", palette=palette,
        facet_kws=dict(sharex=False, sharey=False),
        kind="line", legend="full", data=long_data)

    #rotate labels and label y axis
    [plt.setp(ax.get_xticklabels(), rotation=45) for ax in plot.axes.flat]

    plot.axes[0,0].set_ylabel('Capacity (Mbps km^2)')
    plot.axes[1,0].set_ylabel('Capacity Margin (Mbps km^2)')
    plot.axes[2,0].set_ylabel('Capex (£ Millions)')
    plot.axes[3,0].set_ylabel('Opex (£ Thousands)')

    plot.axes[0,0].set(xlim=(2019, 2030), ylim=(0, 50))
    plot.axes[0,1].set(xlim=(2019, 2030), ylim=(0, 50))
    plot.axes[0,2].set(xlim=(2019, 2030), ylim=(0, 50))
    plot.axes[1,0].set(xlim=(2019, 2030), ylim=(-70, 35))
    plot.axes[1,1].set(xlim=(2019, 2030), ylim=(-70, 35))
    plot.axes[1,2].set(xlim=(2019, 2030), ylim=(-70, 35))
    plot.axes[2,0].set(xlim=(2019, 2030), ylim=(0, 1.2))
    plot.axes[2,1].set(xlim=(2019, 2030), ylim=(0, 1.2))
    plot.axes[2,2].set(xlim=(2019, 2030), ylim=(0, 1.2))
    plot.axes[3,0].set(xlim=(2019, 2030), ylim=(0, 60))
    plot.axes[3,1].set(xlim=(2019, 2030), ylim=(0, 60))
    plot.axes[3,2].set(xlim=(2019, 2030), ylim=(0, 60))

    #plot spacing
    plt.subplots_adjust(hspace=0.3, wspace=0.2, bottom=0.08)

    #sort out legend and move to bottom
    handles = plot._legend_data.values()
    labels = plot._legend_data.keys()
    plot._legend.remove()
    plot.fig.legend(handles=handles, labels=labels, loc='lower center', ncol=8)

    plot.savefig(DATA_OUTPUT_PLOTS + '/strategy_line_plot_{}.png'.format(filename))

    return print('completed line plots')


def load_in_pcd_results():

    filenames = glob.iglob(os.path.join(DATA, '*pcd_metrics*'))

    data = []
    for filename in filenames:
        df = pd.read_csv(filename)
        base = os.path.basename(filename).split('_')
        df['scenario_pop'] = base[2][4:]
        df['scenario_data'] = base[3][11:]
        df['strategy'] = base[4][9:-4]
        data.append(df)

    output = pd.concat(data)

    return output


def transform_pcd_data_labels(data):

    data = data.rename(index=str,
        columns =
        {
            'year': 'Year',
            'postcode': 'Postcode',
            'capex': 'Capex',
            'opex': 'Opex',
            'user_throughput': 'User Throughput',
            'demand': 'Demand',
            'capacity': 'Capacity',
            'capacity_deficit': 'Capacity Margin',
            'population': 'Population',
            'area': 'Area',
            'pop_density': 'Population Density',
            'environment': 'Environment',
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

    data['Environment'] = data['Environment'].replace(
        {
            'urban': 'Urban',
            'suburban': 'Suburban',
            'rural': 'Rural'
        }
    )

    #data scenario and population scenario should be the same,
    #so one can just be copied for the general scenario
    data['Scenario'] = data['Population Scenario']

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


def demand_line_plots(data, filename):

    data = data.loc[(data['Strategy'] == 'No Investment')]

    data['Year'] = pd.to_datetime(data["Year"].astype(str), format="%Y")

    data = data[['Year', 'Scenario', 'User Throughput', 'Area',
        'Demand', 'Population', 'Population Density']]

    data = data.groupby([
        'Year', 'Scenario',
        ]).median().reset_index()

    long_data = pd.melt(data,
        id_vars=['Year', 'Scenario'],
        value_vars=['User Throughput', #'Area', 'Population Density'
        'Population', 'Demand',]
        )

    long_data.columns = ['Year', 'Scenario',
        'Metric', 'Value']

    # print(long_data.Value.unique())
    sns.set(font_scale=1.3)

    palette = dict(zip(data.Scenario.unique(),
        sns.color_palette("Set2", 3)))

    plot = sns.relplot(x='Year', y='Value',
        hue='Scenario', hue_order=['Low', 'Baseline', 'High'],
        # col="Scenario", col_order=["Low", "Baseline", "High"],
        col="Metric", palette=palette,
        facet_kws=dict(sharex=False, sharey=False),
        kind="line", legend="full", data=long_data)


    #rotate labels and label y axis
    [plt.setp(ax.get_xticklabels(), rotation=45) for ax in plot.axes.flat]

    plot.axes[0,0].set_ylabel('Monthly User Data Demand (Mbps)')
    plot.axes[0,1].set_ylabel('Median Population')
    plot.axes[0,2].set_ylabel('Median Data Demand (km^2 Mbps)')

    #plot spacing
    plt.subplots_adjust(hspace=0.5, wspace=0.3, bottom=0.3)
    # plt.gca().set_xticks(data["Year"].unique())
    # plt.locator_params(integer=True)
    # plot.axes[].set(xlim=(2019, 2030), ylim=(0, 70))
    # plot.axes[].set(xlim=(2019, 2030), ylim=(0, 70))
    # plot.axes[].set(xlim=(2019, 2030), ylim=(0, 70))

    #sort out legend and move to bottom
    handles = plot._legend_data.values()
    labels = plot._legend_data.keys()
    plot._legend.remove()
    plot.fig.legend(handles=handles, labels=labels, loc='lower center', ncol=4)

    plot.savefig(DATA_OUTPUT_PLOTS + '/demand_line_plot_{}.png'.format(filename))

    return print('demand plots completed')


def plot_pcd_pairplot(data, category, year, scenario, strategy):

    data = data.loc[(data['Year'] == year)]
    data = data.loc[(data['Scenario'] == scenario)]
    data = data.loc[(data['Strategy'] == strategy)]

    data = data[['Population Density', 'Demand', 'Capacity',
        'Capacity Margin', category]]

    plot = sns.pairplot(data, hue=category, markers=".")

    plot.fig.subplots_adjust(top=0.9)
    plot.fig.suptitle(
        'Scenario: {}, Strategy: {}, Year: {}'.format(scenario, strategy, year), fontsize=16)

    plot.axes[0,0].set_ylabel('Pop. Density (km^2)')
    plot.axes[1,0].set_ylabel('Demand (Mbps km^2)')
    plot.axes[2,0].set_ylabel('Capacity (Mbps km^2)')
    plot.axes[3,0].set_ylabel('Capacity Margin (Mbps km^2)')
    plot.axes[3,0].set_xlabel('Pop. Density (km^2)')
    plot.axes[3,1].set_xlabel('Demand (Mbps km^2)')
    plot.axes[3,2].set_xlabel('Capacity (Mbps km^2)')
    plot.axes[3,3].set_xlabel('Capacity Margin (Mbps km^2)')

    plot.axes[0,0].set(xlim=(0, 60000), ylim=(0, 40000))
    plot.axes[1,0].set(xlim=(0, 60000), ylim=(0, 3000))
    plot.axes[2,0].set(xlim=(0, 60000), ylim=(0, 1500))
    plot.axes[3,0].set(xlim=(0, 60000), ylim=(-2000, 1000))
    plot.axes[0,1].set(xlim=(0, 3000), ylim=(0, 40000))
    plot.axes[1,1].set(xlim=(0, 3000), ylim=(0, 3000))
    plot.axes[2,1].set(xlim=(0, 3000), ylim=(0, 1500))
    plot.axes[3,1].set(xlim=(0, 3000), ylim=(-2000, 1000))
    plot.axes[0,2].set(xlim=(0, 5000), ylim=(0, 40000))
    plot.axes[1,2].set(xlim=(0, 5000), ylim=(0, 3000))
    plot.axes[2,2].set(xlim=(0, 5000), ylim=(0, 1500))
    plot.axes[3,2].set(xlim=(0, 5000), ylim=(-2000, 1000))
    plot.axes[0,3].set(xlim=(-2000, 1000), ylim=(0, 40000))
    plot.axes[1,3].set(xlim=(-2000, 1000), ylim=(0, 3000))
    plot.axes[2,3].set(xlim=(-2000, 1000), ylim=(0, 1500))
    plot.axes[3,3].set(xlim=(-2000, 1000), ylim=(-2000, 1000))

    plot.savefig(DATA_OUTPUT_PLOTS + '/pcd_pairplot_{}_{}_{}_{}.png'.format(
        scenario.lower(), strategy.lower(), year, category.lower())
        )

    plt.close()

    return print('completed {}, {}, {}, {}'.format(
        category, year, scenario, strategy))


def get_unique_categories(data):

    # scenarios = ['baseline']
    # strategies = ['hybrid deployment']#,'no investment']

    scenarios = data.Scenario.unique()
    strategies = data.Strategy.unique()
    years = data.Year.unique()

    return scenarios, strategies, years


def generate_plot_sequences(data):

    scenarios, strategies, years = get_unique_categories(data)

    for scenario in scenarios:
        # if scenario == 'Baseline':
        for strategy in strategies:
            # if strategy == 'No Investment':
            for year in years:
                # if year == 2019 or year == 2030:
                plot_pcd_pairplot(
                    data, 'Environment', year, scenario, strategy
                    )

    return print('completed all plot sequences')


# def plot_pcd_distplot(data):

#     data = data.loc[(data['Scenario'] == 'Baseline')]
#     data = data.loc[(data['Strategy'] == 'Spectrum Integration')]

#     # plot = sns.FacetGrid(data, col="", hue="")

#     pop_density_plot = sns.distplot(data[['Population Density']])
#     pop_density_plot.figure.savefig(DATA_OUTPUT_PLOTS + '/pcd_pop_density.png')

#     demand_plot = sns.distplot(data[['Demand']])
#     demand_plot.figure.savefig(DATA_OUTPUT_PLOTS + '/pcd_demand.png')

#     capacity_plot = sns.distplot(data[['Capacity']])
#     capacity_plot.figure.savefig(DATA_OUTPUT_PLOTS + '/pcd_capacity.png')

#     capacity_margin_plot = sns.distplot(data[['Capacity Margin']])
#     capacity_margin_plot.figure.savefig(DATA_OUTPUT_PLOTS + '/pcd_capacity_margin.png')

#     return print('completed plots')


def aggregate_pcd_data(data):

    data = data[['Year', 'Scenario', 'Strategy',
        'Demand', 'Capacity', 'Capacity Margin',
        'Population Density', 'Environment',
        'Capex', 'Opex']]

    long_data = pd.melt(data,
        id_vars=['Year', 'Scenario', 'Strategy'],
        value_vars=['Demand', 'Capacity', 'Capacity Margin',
        'Capex', 'Opex']
        )

    long_data.columns = ['Year', 'Scenario', 'Strategy',
        'Metric', 'Value']

    return long_data


def plot_pcd_distributions(data, filename):

    sns.set(font_scale=1.4)

    palette = dict(zip(data.Strategy.unique(),
        sns.color_palette("Set2", 5)))

    plot = sns.relplot(x='Year', y='Value',
        hue='Strategy', hue_order=["No Investment", "Spectrum Integration",
            "Deregulation", "Macro Densification", "Hybrid Deployment"],
        col="Scenario", col_order=["Low", "Baseline", "High",],
        row="Metric", palette=palette,
        facet_kws=dict(sharex=False, sharey=False),
        kind="line", legend="full", data=data)

    # #rotate labels and label y axis
    # [plt.setp(ax.get_xticklabels(), rotation=45) for ax in plot.axes.flat]
    # plot.axes[0,0].set_ylabel('Demand (Mbps km^2)')
    # plot.axes[1,0].set_ylabel('Capacity (Mbps km^2)')
    # plot.axes[2,0].set_ylabel('Capacity Margin (Mbps km^2)')
    # plot.axes[3,0].set_ylabel('Capex (£ Millions)')
    # plot.axes[4,0].set_ylabel('Opex (£ Thousands)')

    # plot.axes[0,0].set(xlim=(2019, 2030), ylim=(0, 70))
    # plot.axes[0,1].set(xlim=(2019, 2030), ylim=(0, 70))
    # plot.axes[0,2].set(xlim=(2019, 2030), ylim=(0, 70))
    # plot.axes[1,0].set(xlim=(2019, 2030), ylim=(0, 50))
    # plot.axes[1,1].set(xlim=(2019, 2030), ylim=(0, 50))
    # plot.axes[1,2].set(xlim=(2019, 2030), ylim=(0, 50))
    # plot.axes[2,0].set(xlim=(2019, 2030), ylim=(-70, 35))
    # plot.axes[2,1].set(xlim=(2019, 2030), ylim=(-70, 35))
    # plot.axes[2,2].set(xlim=(2019, 2030), ylim=(-70, 35))
    # plot.axes[3,0].set(xlim=(2019, 2030), ylim=(0, 1.2))
    # plot.axes[3,1].set(xlim=(2019, 2030), ylim=(0, 1.2))
    # plot.axes[3,2].set(xlim=(2019, 2030), ylim=(0, 1.2))
    # plot.axes[4,0].set(xlim=(2019, 2030), ylim=(0, 60))
    # plot.axes[4,1].set(xlim=(2019, 2030), ylim=(0, 60))
    # plot.axes[4,2].set(xlim=(2019, 2030), ylim=(0, 60))

    # #plot spacing
    # plt.subplots_adjust(hspace=0.3, wspace=0.2, bottom=0.06)

    # #sort out legend and move to bottom
    # handles = plot._legend_data.values()
    # labels = plot._legend_data.keys()
    # plot._legend.remove()
    # plot.fig.legend(handles=handles, labels=labels, loc='lower center', ncol=8)

    plot.savefig(DATA_OUTPUT_PLOTS + '/pcd_distributions.svg')

    return print('completed pcd distribution plots')


def generate_fig(scenario, strategy):

    filenames = glob.iglob(os.path.join(DATA_OUTPUT_PLOTS, '*pcd_pairplot*'))

    images = []

    for filename in filenames:
        base = os.path.basename(filename).split('_')
        file_scenario = base[2]
        file_strategy = base[3]
        if scenario.lower() == file_scenario.lower():
            if strategy.lower() == file_strategy.lower():
                images.append(imageio.imread(filename))

    gif_name = 'pcd_pairplot_{}_{}.gif'.format(scenario, strategy)

    imageio.mimsave(os.path.join(DATA_OUTPUT_GIFS, gif_name), images)

    return print('generated {}, {}'.format(scenario, strategy))


def generate_gifs(data):

    scenarios, strategies, years = get_unique_categories(data)

    for scenario in scenarios:
        for strategy in strategies:
            generate_fig(scenario, strategy)

    return print('generated gifs')


def generate_lad_results():

    lad_data = load_in_lad_results()
    lad_data = transform_lad_data_labels(lad_data)
    strategy_line_plots(lad_data, 'median_strategy_metrics')

    return print('generated lad results')


def generate_pcd_results():

    pcd_data = load_in_pcd_results()
    pcd_data = transform_pcd_data_labels(pcd_data)
    demand_line_plots(pcd_data, 'median_demand_metrics')
    # generate_plot_sequences(pcd_data)
    # generate_gifs(pcd_data)

    return print('generated postcode gifs')


def run_functions():

    # generate_lad_results()

    generate_pcd_results()

    # plot_pcd_distplot(pcd_data)
    # long_data = aggregate_pcd_data(pcd_data)
    # plot_pcd_distributions(log_data, 'pcd_distributions')


if __name__ == '__main__':

    run_functions()
