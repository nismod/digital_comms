"""
Model runner to use in place of smif for standalone modelruns
- run over multiple years
- make rule-based intervention decisions at each timestep

"""
import configparser
import csv
import itertools
import os
import pprint
import glob
import pprint

import fiona
from collections import defaultdict

from digital_comms.mobile_network.model import NetworkManager
from digital_comms.mobile_network.interventions import decide_interventions

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')
SHAPES_INPUT_PATH = os.path.join(BASE_PATH, 'raw', 'd_shapes')
SYSTEM_OUTPUT_PATH = os.path.join(BASE_PATH, '..','results')


def load_local_authority_districts():
    """
    Load in Local Authority District (LAD) shapes and extract id information.

    """
    lads = []

    lad_shapes = os.path.join(
        SHAPES_INPUT_PATH, 'lad_uk_2016-12', 'lad_uk_2016-12.shp'
        )

    with fiona.open(lad_shapes, 'r') as lad_shape:
        for lad in lad_shape:
            if not lad['properties']['name'].startswith((
                'E06000053',
                'S12000027',
                'N09000001',
                'N09000002',
                'N09000003',
                'N09000004',
                'N09000005',
                'N09000006',
                'N09000007',
                'N09000008',
                'N09000009',
                'N09000010',
                'N09000011',
                )):
                lads.append({
                    "id": lad['properties']['name'],
                    "name": lad['properties']['desc'],
                })
    return lads


def load_postcode_sectors():
    """
    Load in postcode sector information.

    """
    pcd_sectors = []
    PCD_SECTOR_FILENAME = os.path.join(INTERMEDIATE, 'mobile_model_inputs',
        '_processed_postcode_sectors.csv'
    )

    with open(PCD_SECTOR_FILENAME, 'r') as source:
        reader = csv.DictReader(source)
        for pcd_sector in reader:
            pcd_sectors.append({
                "id": pcd_sector['id'].replace(" ", ""),
                "lad_id": pcd_sector['lad'],
                "area_km2": float(pcd_sector['area_km2'])
                })

    return pcd_sectors


def load_population_scenario_data():
    """
    Load in population scenario data.

    """
    scenario_files = {
        scenario: os.path.join(BASE_PATH, 'intermediate',
        'mobile_model_inputs', 'pcd_arc_population__{}.csv'.format(scenario))
        for scenario in POPULATION_SCENARIOS
    }

    population_by_scenario_year_pcd = {
        scenario: {
            year: {} for year in TIMESTEPS
        }
        for scenario in POPULATION_SCENARIOS
    }

    for scenario, filename in scenario_files.items():
        with open(filename, 'r') as scenario_file:
            scenario_reader = csv.DictReader(scenario_file)
            for item in scenario_reader:
                year = int(item['year'])
                if year in TIMESTEPS:
                    population_by_scenario_year_pcd[scenario][year][item['id']] = (
                        int(item['population'])
                    )

    return population_by_scenario_year_pcd


def load_user_throughput_scenarios():
    """
    Load in user throughput scenario data.

    """
    user_throughput_by_scenario_year = {
        scenario: {} for scenario in THROUGHPUT_SCENARIOS
    }

    THROUGHPUT_FILENAME = os.path.join(BASE_PATH, 'raw', 'b_mobile_model',
        'monthly_data_growth_scenarios.csv'
    )

    with open(THROUGHPUT_FILENAME, 'r') as throughput_file:
        reader = csv.reader(throughput_file)
        next(reader)
        for year, low, base, high in reader:
            year = int(year)
            if "high" in THROUGHPUT_SCENARIOS:
                user_throughput_by_scenario_year["high"][year] = float(high)
            if "baseline" in THROUGHPUT_SCENARIOS:
                user_throughput_by_scenario_year["baseline"][year] = float(base)
            if "low" in THROUGHPUT_SCENARIOS:
                user_throughput_by_scenario_year["low"][year] = float(low)

    return user_throughput_by_scenario_year


def load_initial_system(site_share):
    """
    Load in initial system of mobile sites.

    """
    SYSTEM_FILENAME = os.path.join(INTERMEDIATE, 'mobile_model_inputs',
        'final_processed_sites.csv'
    )

    pcd_sectors = set()
    initial_system = []

    with open(SYSTEM_FILENAME, 'r') as system_file:
        reader = csv.DictReader(system_file)
        for pcd_sector in reader:
            if int(pcd_sector['lte_4G']):
                frequency = ['800', '1800', '2600']
                technology = 'LTE'
            else:
                frequency = []
                technology = ''
            pcd_sectors.add(pcd_sector['id'].replace(' ', ''))
            initial_system.append({
                'pcd_sector': pcd_sector['id'].replace(' ', ''),
                'site_ngr': pcd_sector['name'],
                'build_date': 2016,
                'technology': technology,
                'frequency': frequency,
                'type': 'macrocell_site',
                'capex': 0,
                'opex': 20000
            })

    output = []

    for pcd_sector in pcd_sectors:
        total_pcd_sectors = []
        for item in initial_system:
            if item['pcd_sector'] == pcd_sector:
                total_pcd_sectors.append(item)
        if len(total_pcd_sectors) == 0:
            # print('no sites in sector')
            continue
        if len(total_pcd_sectors) == 1:
            # print('only one site in sector')
            output.extend(total_pcd_sectors)
        if len(total_pcd_sectors) >= 2:
            number_to_append = round(len(total_pcd_sectors) * (site_share/100))
            appended_so_far = 0
            for item in total_pcd_sectors:
                if appended_so_far <= number_to_append:
                    output.append(item)
                else:
                    pass
                appended_so_far += 1

    return output


def load_capacity_lookup_table():
    """
    Load in capacity density lookup table.

    """
    PATH_LIST = glob.iglob(os.path.join(INTERMEDIATE,
        'system_simulator', '*capacity_lookup_table*.csv'), recursive=True
    )
    # print([p for p in PATH_LIST])
    capacity_lookup_table = {}

    for path in PATH_LIST:
        with open(path, 'r') as capacity_lookup_file:
            reader = csv.DictReader(capacity_lookup_file)
            for row in reader:
                if float(row["capacity_mbps_km2"]) <= 0:
                    continue
                environment = row["environment"].lower()
                frequency = str(int(float(row["frequency_GHz"]) * 1e3))
                bandwidth = str(row["bandwidth_MHz"])
                generation = str(row["generation"])
                density = float(row["sites_per_km2"])
                capacity = float(row["capacity_mbps_km2"])

                if (environment, frequency, bandwidth, generation) \
                    not in capacity_lookup_table:
                    capacity_lookup_table[(
                        environment, frequency, bandwidth, generation)
                        ] = []

                capacity_lookup_table[(
                    environment, frequency, bandwidth, generation
                    )].append((
                        density, capacity
                    ))

            for key, value_list in capacity_lookup_table.items():
                value_list.sort(key=lambda tup: tup[0])

    return capacity_lookup_table


def load_clutter_geotype_lookup_table():
    """
    Load in clutter geotype lookup table.

    """
    CLUTTER_GEOTYPE_FILENAME = os.path.join(INTERMEDIATE, 'mobile_model_inputs',
        'lookup_table_geotype.csv'
    )

    clutter_lookup = []

    with open(CLUTTER_GEOTYPE_FILENAME, 'r') as clutter_geotype_file:
        reader = csv.DictReader(clutter_geotype_file)
        for row in reader:
            geotype = row['geotype'].lower()
            population_density = float(row['population_density'])
            clutter_lookup.append((population_density, geotype))

        clutter_lookup.sort(key=lambda tup: tup[0])

    return clutter_lookup


def write_lad_results(network_manager, folder, year, pop_scenario,
    throughput_scenario, intervention_strategy, cost_by_lad, lad_areas):
    """
    Write LAD results to .csv file.

    """
    suffix = _get_suffix(pop_scenario, throughput_scenario, intervention_strategy)
    if not os.path.exists(folder):
        os.mkdir(folder)
    metrics_filename = os.path.join(folder, 'metrics_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        metrics_file = open(metrics_filename, 'w', newline='')
        metrics_writer = csv.writer(metrics_file)
        metrics_writer.writerow(
            ('year', 'area_id', 'area_name', 'area', 'cost', 'demand',
            'capacity', 'capacity_deficit', 'population', 'pop_density'))

    else:
        metrics_file = open(metrics_filename, 'a', newline='')
        metrics_writer = csv.writer(metrics_file)

    population = 0
    for lad in network_manager.lads.values():
        if lad.id in lad_areas:
            area_id = lad.id
            area_name = lad.name
            area = lad.area
            cost = cost_by_lad[lad.id]
            demand = lad.demand()
            capacity = lad.capacity()
            capacity_deficit = capacity - demand
            pop = lad.population
            pop_d = lad.population_density

            metrics_writer.writerow(
                (year, area_id, area_name, area, cost, demand, capacity,
                capacity_deficit, pop, pop_d))

            population += lad.population

    print('population written is {}'.format(round(population/1e6,1)))

    metrics_file.close()


def write_pcd_results(network_manager, folder, year, pop_scenario,
    throughput_scenario, intervention_strategy, cost_by_pcd, lad_areas):
    """
    Write postcode sector results to .csv file.

    """
    suffix = _get_suffix(pop_scenario, throughput_scenario, intervention_strategy)
    if not os.path.exists(folder):
        os.mkdir(folder)
    metrics_filename = os.path.join(folder,
        'pcd_metrics_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        metrics_file = open(metrics_filename, 'w', newline='')
        metrics_writer = csv.writer(metrics_file)
        metrics_writer.writerow(
            ('year', 'postcode', 'lad_id','cost', 'demand', 'demand_density',
            'user_demand','site_density_macrocells','site_density_small_cells',
            'capacity','capacity_deficit', 'population', 'area', 'pop_density',
            'clutter_env'))
    else:
        metrics_file = open(metrics_filename, 'a', newline='')
        metrics_writer = csv.writer(metrics_file)

    for pcd in network_manager.postcode_sectors.values():
        if pcd.lad_id in lad_areas:
            demand = pcd.demand
            demand_density = pcd.demand_density
            site_density_macrocells = pcd.site_density_macrocells
            site_density_small_cells = pcd.site_density_small_cells
            capacity = pcd.capacity
            capacity_deficit = capacity - demand
            population = pcd.population
            area = pcd.area
            pop_d = pcd.population_density
            cost = cost_by_pcd[pcd.id]
            user_demand = pcd.user_demand
            clutter_env = pcd.clutter_environment

            metrics_writer.writerow(
                (year, pcd.id, pcd.lad_id, cost, demand, demand_density, user_demand,
                site_density_macrocells, site_density_small_cells, capacity,
                capacity_deficit, population, area, pop_d, clutter_env)
            )

    metrics_file.close()


def write_decisions(decisions, folder, year, pop_scenario,
    throughput_scenario, intervention_strategy, lad_areas):
    """
    Write decisions to .csv file.

    """
    suffix = _get_suffix(pop_scenario, throughput_scenario, intervention_strategy)
    # folder = os.path.join(BASE_PATH, '..', 'results')
    if not os.path.exists(folder):
        os.mkdir(folder)
        # os.mkdir(os.path.join(folder, 'mobile_model_1.0'))
    decisions_filename =  os.path.join(folder, 'decisions_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        decisions_file = open(decisions_filename, 'w', newline='')
        decisions_writer = csv.writer(decisions_file)
        decisions_writer.writerow(
            ('year', 'pcd_sector', 'site_ngr', 'build_date',
            'type', 'technology', 'frequency', 'bandwidth'))
    else:
        decisions_file = open(decisions_filename, 'a', newline='')
        decisions_writer = csv.writer(decisions_file)

    for intervention in decisions:

        pcd_sector = intervention['pcd_sector']
        site_ngr = intervention['site_ngr']
        build_date = intervention['build_date']
        intervention_type = intervention['type']
        technology = intervention['technology']
        frequency = intervention['frequency']
        bandwidth = intervention['bandwidth']

        decisions_writer.writerow(
            (year, pcd_sector, site_ngr, build_date, intervention_type,
            technology, frequency, bandwidth))

    decisions_file.close()


def write_spend(spend, folder, year, pop_scenario,
    throughput_scenario, intervention_strategy, lad_areas):
    """
    Write asset spending results to .csv file.

    """
    suffix = _get_suffix(pop_scenario, throughput_scenario, intervention_strategy)
    if not os.path.exists(folder):
        os.mkdir(folder)
    spend_filename = os.path.join(folder, 'spend_{}.csv'.format(suffix))

    if year == BASE_YEAR:
        spend_file = open(spend_filename, 'w', newline='')
        spend_writer = csv.writer(spend_file)
        spend_writer.writerow(
            ('year', 'pcd_sector', 'lad', 'item', 'cost'))
    else:
        spend_file = open(spend_filename, 'a', newline='')
        spend_writer = csv.writer(spend_file)

    for pcd_sector, lad, item, cost in spend:
        if lad in lad_areas:
            spend_writer.writerow(
                (year, pcd_sector, lad, item, cost))

    spend_file.close()


def _get_suffix(pop_scenario, throughput_scenario, intervention_strategy):
    """
    Get the filename suffix for each scenario and strategy variant.

    """
    suffix = '{}_{}_{}'.format(
        pop_scenario, throughput_scenario, intervention_strategy)

    suffix = suffix.replace('baseline', 'base')

    return suffix


if __name__ == '__main__':

    ################################################################
    # START RUNNING MODEL
    # - run from BASE_YEAR to END_YEAR in TIMESTEP_INCREMENT steps
    # - run over population scenario / demand scenario / intervention
    #  strategy combinations
    # - output demand, capacity, opex, energy demand, built interventions,
    #   build costs per year
    ################################################################

    folder = os.path.join(BASE_PATH, '..', 'results', 'mobile_outputs')

    BASE_YEAR = 2020
    END_YEAR = 2030
    TIMESTEP_INCREMENT = 1
    TIMESTEPS = range(BASE_YEAR, END_YEAR + 1, TIMESTEP_INCREMENT)

    POPULATION_SCENARIOS = [
        'baseline',
        '0-unplanned',
        '1-new-cities-from-dwellings',
        '2-expansion',
        '3-new-cities23-from-dwellings',
        '4-expansion23',
    ]
    THROUGHPUT_SCENARIOS = [
        "high",
        "baseline",
        "low",
    ]
    INTERVENTION_STRATEGIES = [
        "minimal",
        "macrocell",
        "small-cell",
        "small-cell-and-spectrum"
    ]

    LAD_AREAS = [
        'E06000031',
        'E07000005',
        'E07000006',
        'E07000007',
        'E06000032',
        'E06000042',
        'E06000055',
        'E06000056',
        'E07000004',
        'E07000008',
        'E07000009',
        'E07000010',
        'E07000011',
        'E07000012',
        'E07000150',
        'E07000151',
        'E07000152',
        'E07000153',
        'E07000154',
        'E07000155',
        'E07000156',
        'E07000177',
        'E07000178',
        'E07000179',
        'E07000180',
        'E07000181',
    ]

    MARKET_SHARE = 0.30
    ANNUAL_BUDGET = (2 * 10 ** 9) * MARKET_SHARE
    SERVICE_OBLIGATION_CAPACITY = 0
    BUSY_HOUR_TRAFFIC_PERCENTAGE = 20
    COVERAGE_THRESHOLD = 2
    SITE_SHARE = 50

    simulation_parameters = {
        'market_share': MARKET_SHARE,
        'annual_budget': ANNUAL_BUDGET,
        'service_obligation_capacity': SERVICE_OBLIGATION_CAPACITY,
        'busy_hour_traffic_percentage': BUSY_HOUR_TRAFFIC_PERCENTAGE,
        'coverage_threshold': COVERAGE_THRESHOLD,
        'penetration': 80,
        'channel_bandwidth_700': '10',
        'channel_bandwidth_800': '10',
        'channel_bandwidth_1800': '10',
        'channel_bandwidth_2600': '10',
        'channel_bandwidth_3500': '40',
        'channel_bandwidth_26000': '100',
        'macro_sectors': 3,
        'small-cell_sectors': 1,
        'mast_height': 30,
    }

    print('Loading local authority districts')
    lads = load_local_authority_districts()

    print('Loading postcode sectors')
    pcd_sectors = load_postcode_sectors()

    print('Loading population scenario data')
    population_by_scenario_year_pcd = load_population_scenario_data()

    print('Loading user throughput scenario data')
    user_throughput_by_scenario_year = load_user_throughput_scenarios()

    print('Loading initial system')
    initial_system = load_initial_system(SITE_SHARE)
    print('loaded {} sites'.format(len(initial_system)))

    print('Loading lookup table')
    capacity_lookup_table = load_capacity_lookup_table()

    print('Loading lookup table')
    clutter_lookup = load_clutter_geotype_lookup_table()

    for pop_scenario, throughput_scenario, intervention_strategy in [

            ('baseline', 'low', 'minimal'),
            ('0-unplanned', 'low', 'minimal'),
            ('1-new-cities-from-dwellings', 'low', 'minimal'),
            ('2-expansion', 'low', 'minimal'),
            ('3-new-cities23-from-dwellings', 'low', 'minimal'),
            ('4-expansion23', 'low', 'minimal'),

            ('baseline', 'baseline', 'minimal'),
            ('0-unplanned', 'baseline', 'minimal'),
            ('1-new-cities-from-dwellings', 'baseline', 'minimal'),
            ('2-expansion', 'baseline', 'minimal'),
            ('3-new-cities23-from-dwellings', 'baseline', 'minimal'),
            ('4-expansion23', 'baseline', 'minimal'),

            ('baseline', 'high', 'minimal'),
            ('0-unplanned', 'high', 'minimal'),
            ('1-new-cities-from-dwellings', 'high', 'minimal'),
            ('2-expansion', 'high', 'minimal'),
            ('3-new-cities23-from-dwellings', 'high', 'minimal'),
            ('4-expansion23', 'high', 'minimal'),

            ('baseline', 'baseline', 'macrocell'),
            ('0-unplanned', 'baseline', 'macrocell'),
            ('1-new-cities-from-dwellings', 'baseline', 'macrocell'),
            ('2-expansion', 'baseline', 'macrocell'),
            ('3-new-cities23-from-dwellings', 'baseline', 'macrocell'),
            ('4-expansion23', 'baseline', 'macrocell'),

            ('baseline', 'baseline', 'small-cell'),
            ('0-unplanned', 'baseline', 'small-cell'),
            ('1-new-cities-from-dwellings', 'baseline', 'small-cell'),
            ('2-expansion', 'baseline', 'small-cell'),
            ('3-new-cities23-from-dwellings', 'baseline', 'small-cell'),
            ('4-expansion23', 'baseline', 'small-cell'),

            ('baseline', 'baseline', 'small-cell-and-spectrum'),
            ('0-unplanned', 'baseline', 'small-cell-and-spectrum'),
            ('1-new-cities-from-dwellings', 'baseline', 'small-cell-and-spectrum'),
            ('2-expansion', 'baseline', 'small-cell-and-spectrum'),
            ('3-new-cities23-from-dwellings', 'baseline', 'small-cell-and-spectrum'),
            ('4-expansion23', 'baseline', 'small-cell-and-spectrum'),

        ]:
        print("Running:", pop_scenario, throughput_scenario, intervention_strategy)

        assets = initial_system[:]

        for year in TIMESTEPS:
            print("-", year)

            for pcd_sector in pcd_sectors:
                try:
                    pcd_sector_id = pcd_sector["id"]
                    pcd_sector["population"] = (
                        population_by_scenario_year_pcd \
                            [pop_scenario][year][pcd_sector_id])
                    pcd_sector["user_throughput"] = (
                        user_throughput_by_scenario_year \
                            [throughput_scenario][year])
                except:
                    pass

            budget = simulation_parameters['annual_budget']
            service_obligation_capacity = (
                simulation_parameters['service_obligation_capacity'])

            if year == BASE_YEAR:
                system = NetworkManager(lads, pcd_sectors, assets,
                    capacity_lookup_table, clutter_lookup,
                    simulation_parameters)

            interventions_built, budget, spend = decide_interventions(
                intervention_strategy, budget, service_obligation_capacity,
                system, year, simulation_parameters)

            assets += interventions_built

            system = NetworkManager(lads, pcd_sectors, assets,
                capacity_lookup_table, clutter_lookup,
                simulation_parameters)

            cost_by_lad = defaultdict(int)
            cost_by_pcd = defaultdict(int)
            for pcd, lad, item, cost in spend:
                cost_by_lad[lad] += cost
                cost_by_pcd[pcd] += cost

            write_lad_results(system, folder, year, pop_scenario, throughput_scenario,
                intervention_strategy, cost_by_lad, LAD_AREAS)
            write_pcd_results(system, folder, year, pop_scenario, throughput_scenario,
                intervention_strategy, cost_by_pcd, LAD_AREAS)
            # write_decisions(interventions_built, folder, year, pop_scenario,
            #     throughput_scenario, intervention_strategy, LAD_AREAS)
            write_spend(spend, folder, year, pop_scenario, throughput_scenario,
                intervention_strategy, LAD_AREAS)
