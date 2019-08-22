import os
import sys
import configparser
import csv
import fiona
import time

from shapely.geometry import shape, Point, LineString, mapping
from shapely.ops import  cascaded_union

from rtree import index

from collections import OrderedDict

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# setup file locations and data files
#####################################

DATA_RAW = os.path.join(BASE_PATH, '..', 'data_raw')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')

#####################################
# READ MAIN DATA
#####################################

def read_lads():
    """
    Read in all lad shapes.

    """
    lad_shapes = os.path.join(
        DATA_RAW, 'shapes', 'lad_uk_2016-12.shp'
        )

    with fiona.open(lad_shapes, 'r') as lad_shape:
        return [lad for lad in lad_shape if
        not lad['properties']['name'].startswith((
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
            ))]


def lad_lut(lads):
    """
    Yield lad IDs for use as a lookup.

    """
    for lad in lads:
        yield lad['properties']['name']


def read_postcode_sectors(path):
    """
    Read all postcode sector shapes.

    """
    with fiona.open(path, 'r') as pcd_sector_shapes:
        return [pcd for pcd in pcd_sector_shapes]


def add_lad_to_postcode_sector(postcode_sectors, lads):
    """
    Add the LAD indicator(s) to the relevant postcode sector.

    """
    final_postcode_sectors = []

    idx = index.Index(
        (i, shape(lad['geometry']).bounds, lad)
        for i, lad in enumerate(lads)
    )

    for postcode_sector in postcode_sectors:
        for n in idx.intersection(
            (shape(postcode_sector['geometry']).bounds), objects=True):
            postcode_sector_centroid = shape(postcode_sector['geometry']).centroid
            postcode_sector_shape = shape(postcode_sector['geometry'])
            lad_shape = shape(n.object['geometry'])
            if postcode_sector_centroid.intersects(lad_shape):
                final_postcode_sectors.append({
                    'type': postcode_sector['type'],
                    'geometry': postcode_sector['geometry'],
                    'properties':{
                        'id': postcode_sector['properties']['RMSect'],
                        'lad': n.object['properties']['name'],
                        'area': postcode_sector_shape.area,
                        },
                    })
                break

    return final_postcode_sectors


def load_coverage_data(lad_id):
    """
    Import Ofcom Connected Nations coverage data (2018).

    """
    path = os.path.join(
        DATA_RAW, 'ofcom_2018', '201809_mobile_laua_r02.csv'
        )

    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        for line in reader:
            if line['laua'] == lad_id:
                return {
                    'lad_id': line['laua'],
                    'lad_name': line['laua_name'],
                    '4G_geo_out_0': line['4G_geo_out_0'],
                    '4G_geo_out_1': line['4G_geo_out_1'],
                    '4G_geo_out_2': line['4G_geo_out_2'],
                    '4G_geo_out_3': line['4G_geo_out_3'],
                    '4G_geo_out_4': line['4G_geo_out_4'],
                }

def load_in_weights():
    """
    Load in postcode sector population to use as weights.

    """
    path = os.path.join(
        DATA_RAW, 'population_scenarios', 'population_baseline_pcd.csv'
        )

    population_data = []

    with open(path, 'r') as source:
        reader = csv.reader(source)
        for line in reader:
            if int(line[0]) == 2015:
                population_data.append({
                    'id': line[1],
                    'population': int(line[2]),
                })

    return population_data


def add_weights_to_postcode_sector(postcode_sectors, weights):
    """
    Add weights to postcode sector

    """
    output = []

    for postcode_sector in postcode_sectors:
        pcd_id = postcode_sector['properties']['id'].replace(' ', '')
        for weight in weights:
            weight_id = weight['id'].replace(' ', '')
            if pcd_id == weight_id:
                output.append({
                    'type': postcode_sector['type'],
                    'geometry': postcode_sector['geometry'],
                    'properties': {
                        'id': pcd_id,
                        'lad': postcode_sector['properties']['lad'],
                        'population_weight': weight['population'],
                        'area_km2': (postcode_sector['properties']['area'] / 1e6),
                    }
                })


    return output


def calculate_lad_population(postcode_sectors):
    """

    """
    lad_ids = set()

    for pcd_sector in postcode_sectors:
        lad_ids.add(pcd_sector['properties']['lad'])

    lad_population = []

    for lad_id in lad_ids:
        population = 0
        for pcd_sector in postcode_sectors:
            if pcd_sector['properties']['lad'] == lad_id:
                population += pcd_sector['properties']['population_weight']
        lad_population.append({
            'lad': lad_id,
            'population': population,
        })

    output = []

    for pcd_sector in postcode_sectors:
        for lad in lad_population:
            if pcd_sector['properties']['lad'] == lad['lad']:

                weight = (
                    pcd_sector['properties']['population_weight'] /
                    lad['population']
                )

                output.append({
                    'type': pcd_sector['type'],
                    'geometry': pcd_sector['geometry'],
                    'properties': {
                        'id': pcd_sector['properties']['id'],
                        'lad': pcd_sector['properties']['lad'],
                        'population': lad['population'] * weight,
                        'weight': weight,
                        'area_km2': pcd_sector['properties']['area_km2'],
                        'pop_density_km2': (
                            weight /
                            (pcd_sector['properties']['area_km2'] / 1e6)
                            ),
                    },
                })

    return output


def get_forecast(filename):
    """

    """
    folder = os.path.join(DATA_RAW, 'population_scenarios')

    with open(os.path.join(folder, filename), 'r') as source:
        reader = csv.DictReader(source)
        for line in reader:
            yield {
                'year': line['timestep'],
                'lad': line['lad_uk_2016'],
                'population': line['population'],
            }


def disaggregate(forecast, postcode_sectors):
    """

    """
    output = []

    seen_lads = set()

    for line in forecast:
        forecast_lad_id = line['lad']
        for postcode_sector in postcode_sectors:
            pcd_sector_lad_id = postcode_sector['properties']['lad']
            if forecast_lad_id == pcd_sector_lad_id:
                # print(postcode_sector)
                seen_lads.add(line['lad'])
                seen_lads.add(postcode_sector['properties']['lad'])
                output.append({
                    'year': line['year'],
                    'lad': line['lad'],
                    'id': postcode_sector['properties']['id'],
                    'population': int(
                        float(line['population']) *
                        float(postcode_sector['properties']['weight'])
                        )
                })

    return output


def generate_scenario_variants(postcode_sectors, directory):
        """
        Function to disaggregate LAD forecasts to postcode level.

        """
        print('Checking total GB population')
        population = 0
        for postcode_sector in postcode_sectors:
            population += postcode_sector['properties']['population']
        print('Total GB population is {}'.format(population))

        files = [
            'arc_population__baseline.csv',
            'arc_population__0-unplanned.csv',
            'arc_population__1-new-cities.csv',
            'arc_population__2-expansion.csv',
        ]

        print('loaded luts')
        for scenario_file in files:

            print('running {}'.format(scenario_file))
            forecast = get_forecast(scenario_file)

            disaggregated_forecast = disaggregate(forecast, postcode_sectors)

            filename = os.path.join('pcd_' + scenario_file)

            print('writing {}'.format(filename))
            csv_writer(disaggregated_forecast, directory, filename)


def allocate_4G_coverage(postcode_sectors, lad_lut):

    output = []

    for lad_id in lad_lut:

        sectors_in_lad = get_postcode_sectors_in_lad(postcode_sectors, lad_id)

        total_area = sum([s['properties']['area_km2'] for s in \
            get_postcode_sectors_in_lad(postcode_sectors, lad_id)])

        coverage_data = load_coverage_data(lad_id)

        coverage_amount = float(coverage_data['4G_geo_out_4'])

        covered_area = total_area * (coverage_amount/100)

        ranked_postcode_sectors = sorted(
            sectors_in_lad, key=lambda x: x['properties']['pop_density_km2'], reverse=True
            )

        area_allocated = 0

        for sector in ranked_postcode_sectors:

            area = sector['properties']['area_km2']
            total = area + area_allocated

            if total < covered_area:

                sector['properties']['lte'] = 1
                output.append(sector)
                area_allocated += area

            else:

                sector['properties']['lte'] = 0
                output.append(sector)

                continue

    return output


def get_postcode_sectors_in_lad(postcode_sectors, lad_id):

    for postcode_sector in postcode_sectors:
        if postcode_sector['properties']['lad'] == lad_id:
            if isinstance(postcode_sector['properties']['pop_density_km2'], float):
                yield postcode_sector


def import_sitefinder_data(path):
    """
    Import sitefinder data, selecting desired asset types.
        - Select sites belonging to main operators:
            - Includes 'O2', 'Vodafone', BT EE (as 'Orange'/'T-Mobile') and 'Three'
            - Excludes 'Airwave' and 'Network Rail'
        - Select relevant cells:
            - Includes 'Macro', 'SECTOR', 'Sectored' and 'Directional'
            - Excludes 'micro', 'microcell', 'omni' or 'pico' antenna types.

    """
    asset_data = []

    site_id = 0

    with open(os.path.join(path), 'r') as system_file:
        reader = csv.DictReader(system_file)
        next(reader, None)
        for line in reader:
            #if line['Operator'] != 'Airwave' and line['Operator'] != 'Network Rail':
            if line['Operator'] == 'O2' or line['Operator'] == 'Vodafone':
                # if line['Anttype'] == 'MACRO' or \
                #     line['Anttype'] == 'SECTOR' or \
                #     line['Anttype'] == 'Sectored' or \
                #     line['Anttype'] == 'Directional':
                asset_data.append({
                    'type': "Feature",
                    'geometry': {
                        "type": "Point",
                        "coordinates": [float(line['X']), float(line['Y'])]
                    },
                    'properties':{
                        'name': 'site_' + str(site_id),
                        'Operator': line['Operator'],
                        'Opref': line['Opref'],
                        'Sitengr': line['Sitengr'],
                        'Antennaht': line['Antennaht'],
                        'Transtype': line['Transtype'],
                        'Freqband': line['Freqband'],
                        'Anttype': line['Anttype'],
                        'Powerdbw': line['Powerdbw'],
                        'Maxpwrdbw': line['Maxpwrdbw'],
                        'Maxpwrdbm': line['Maxpwrdbm'],
                        'Sitelat': float(line['Sitelat']),
                        'Sitelng': float(line['Sitelng']),
                    }
                })

            site_id += 1

        else:
            pass

    return asset_data


def find_average(my_property, touching_assets):

    numerator = sum([float(a['properties'][my_property]) for a in touching_assets
        if str(a['properties'][my_property]).isdigit()])
    denominator = len([a['properties'][my_property] for a in touching_assets
        if str(a['properties'][my_property]).isdigit()])

    try:
        output = numerator / denominator
    except ZeroDivisionError:
        output = numerator

    return output


def process_asset_data(data):
    """
    Add buffer to each site, dissolve overlaps and take centroid.

    """
    buffered_assets = []

    for asset in data:
        asset_geom = shape(asset['geometry'])
        buffered_geom = asset_geom.buffer(50)

        asset['buffer'] = buffered_geom
        buffered_assets.append(asset)

    output = []
    assets_seen = set()

    for asset in buffered_assets:
        if asset['properties']['Opref'] in assets_seen:
            continue
        assets_seen.add(asset['properties']['Opref'])
        touching_assets = []
        for other_asset in buffered_assets:
            if asset['buffer'].intersects(other_asset['buffer']):
                touching_assets.append(other_asset)
                assets_seen.add(other_asset['properties']['Opref'])

        dissolved_shape = cascaded_union([a['buffer'] for a in touching_assets])
        final_centroid = dissolved_shape.centroid
        output.append({
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [final_centroid.coords[0][0], final_centroid.coords[0][1]],
            },
            'properties':{
                'name': asset['properties']['name'],
            }
        })

    return output


def add_coverage_to_sites(sitefinder_data, postcode_sectors):

    final_sites = []

    idx = index.Index(
        (i, shape(site['geometry']).bounds, site)
        for i, site in enumerate(sitefinder_data)
    )

    for postcode_sector in postcode_sectors:
        for n in idx.intersection(
            (shape(postcode_sector['geometry']).bounds), objects=True):
            postcode_sector_shape = shape(postcode_sector['geometry'])
            site_shape = shape(n.object['geometry'])
            if postcode_sector_shape.intersects(site_shape):
                final_sites.append({
                    'type': 'Feature',
                    'geometry': n.object['geometry'],
                    'properties':{
                        'id': postcode_sector['properties']['id'],
                        'name': n.object['properties']['name'],
                        'lte_4G': postcode_sector['properties']['lte']
                        }
                    })

    return final_sites


def read_exchanges():
    """
    Reads in exchanges from 'final_exchange_pcds.csv'.

    """
    path = os.path.join(
        DATA_RAW, 'exchanges', 'final_exchange_pcds.csv'
        )

    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        for line in reader:
            yield {
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [float(line['E']), float(line['N'])]
                },
                'properties': {
                    'exchange_id': 'exchange_' + line['OLO'],
                    'exchange_name': line['Name'],
                    'id': line['exchange_pcd'],
                }
            }


def read_exchange_areas():
    """
    Read exchange polygons

    """
    path = os.path.join(
        DATA_RAW, 'exchanges', '_exchange_areas_fixed.shp'
        )

    with fiona.open(path, 'r') as source:
        for area in source:
            yield area


def return_object_coordinates(object):
    """
    Function for returning the coordinates of a type of object.

    """
    if object['geometry']['type'] == 'Polygon':
        origin_geom = object['representative_point']
        x = origin_geom.x
        y = origin_geom.y
    elif object['geometry']['type'] == 'Point':
        x = object['geometry']['coordinates'][0]
        y = object['geometry']['coordinates'][1]
    else:
        print('non conforming geometry type {}'.format(object['geometry']['type']))

    return x, y


def generate_link_straight_line(origin_points, dest_points):
    """
    Calculate distance between two points.

    """
    idx = index.Index(
        (i, Point(dest_point['geometry']['coordinates']).bounds, dest_point)
        for i, dest_point in enumerate(dest_points)
        )

    processed_sites = []
    links = []

    for origin_point in origin_points:

        try:
            origin_x, origin_y = return_object_coordinates(origin_point)

            exchange = list(idx.nearest(
                Point(origin_point['geometry']['coordinates']).bounds,
                1, objects='raw'))[0]

            dest_x, dest_y = return_object_coordinates(exchange)

            # Get lengthFunction for returning the coordinates of
            # an object given the specific type.
            geom = LineString([
                (origin_x, origin_y), (dest_x, dest_y)
                ])

            processed_sites.append({
                'type': 'Feature',
                'geometry': origin_point['geometry'],
                'properties':{
                    'id': origin_point['properties']['id'],
                    'name': origin_point['properties']['name'],
                    'lte_4G': origin_point['properties']['lte_4G'],
                    'exchange_id': exchange['properties']['exchange_id'],
                    'backhaul_length_m': geom.length * 1.60934
                    }
                })

            links.append({
                'type': "Feature",
                'geometry': mapping(geom),
                'properties': {
                    "origin_id": origin_point['properties']['name'],
                    "dest_id": exchange['properties']['exchange_id'],
                    "length": geom.length * 1.60934
                }
            })

        except:
            print('- Problem with straight line link for:')
            print(origin_point['properties'])

    processed_sites_for_writing = []
    for asset in processed_sites:
        processed_sites_for_writing.append({
            'id': asset['properties']['id'],
            'name': asset['properties']['name'],
            'lte_4G':  asset['properties']['lte_4G'],
            'exchange_id':  asset['properties']['exchange_id'],
            'backhaul_length_m':  asset['properties']['backhaul_length_m'],
        })

    return processed_sites_for_writing, links


def convert_postcode_sectors_to_list(data):

    data_for_writing = []
    for datum in data:
        data_for_writing.append({
            'id': datum['properties']['id'],
            'lad': datum['properties']['lad'],
            'population': datum['properties']['population'],
            'area_km2': datum['properties']['area_km2'],
            'pop_density_km2': datum['properties']['pop_density_km2'],
            'lte_4G': datum['properties']['lte'],

        })

    return data_for_writing


def convert_assets_for_nismod2(data):

    output = []

    asset_id = 0
    for asset in data:
        lte_4G = asset['lte_4G']
        if lte_4G == 1:
            output.append(
                {
                    'name': 'macro_cell_{}_{}_{}_{}'.format(
                        '800', '4G', asset['name'], asset_id),
                    'build_year': 2015,
                    'frequency': '800',
                    'technology': '4G',
                    'type': 'macrocell_site',
                    'id': asset['id'].replace(' ', ''),
                    'technical_lifetime_value': 10,
                    'technical_lifetime_units': 'years',
                    'capex': 50917,
                    'opex': 2000,
                }
            )
            asset_id += 1

            output.append(
                {
                    'name': 'macro_cell_{}_{}_{}_{}'.format(
                        '2600', '4G', asset['name'], asset_id),
                    'build_year': 2015,
                    'frequency': '2600',
                    'technology': '4G',
                    'type': 'macrocell_site',
                    'id': asset['id'],
                    'technical_lifetime_value': 10,
                    'technical_lifetime_units': 'years',
                    'capex': 50917,
                    'opex': 2000,
                }
            )
            asset_id += 1

        elif lte_4G == 0:
            output.append(
                {
                    'name': 'macro_cell_{}_{}_{}_{}'.format(
                        None, None, asset['name'], asset_id),
                    'build_year': 2015,
                    'frequency': '800',
                    'technology': None,
                    'type': 'macrocell_site',
                    'id': asset['id'],
                    'technical_lifetime_value': 10,
                    'technical_lifetime_units': 'years',
                    'capex': 50917,
                    'opex': 2000,
                }
            )
            asset_id += 1

            output.append(
                {
                    'name': 'macro_cell_{}_{}_{}_{}'.format(
                        None, None, asset['name'], asset_id),
                    'build_year': 2015,
                    'frequency': '800',
                    'technology': None,
                    'type': 'macrocell_site',
                    'id': asset['id'],
                    'technical_lifetime_value': 10,
                    'technical_lifetime_units': 'years',
                    'capex': 50917,
                    'opex': 2000,
                }
            )
            asset_id += 1

    return output


def csv_writer(data, directory, filename):
    """
    Write data to a CSV file path

    """
    # Create path
    if not os.path.exists(directory):
        os.makedirs(directory)

    fieldnames = []
    for name, value in data[0].items():
        fieldnames.append(name)

    with open(os.path.join(directory, filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)


if __name__ == "__main__":

    start = time.time()

    directory = os.path.join(DATA_INTERMEDIATE, 'mobile_model_inputs')
    print('Output directory will be {}'.format(directory))

    print('Loading local authority district shapes')
    lads = read_lads()

    print('Loading lad lookup')
    lad_lut = lad_lut(lads)

    print('Loading postcode sector shapes')
    path = os.path.join(DATA_RAW, 'shapes', 'PostalSector.shp')
    postcode_sectors = read_postcode_sectors(path)

    print('Adding lad IDs to postcode sectors... might take a few minutes...')
    postcode_sectors = add_lad_to_postcode_sector(postcode_sectors[:200], lads)

    print('Loading in population weights' )
    weights = load_in_weights()

    print('Adding weights to postcode sectors')
    postcode_sectors = add_weights_to_postcode_sector(postcode_sectors, weights)

    print('Calculating lad population weight for each postcode sector')
    postcode_sectors = calculate_lad_population(postcode_sectors)

    print('Generating scenario variants')
    generate_scenario_variants(postcode_sectors, directory)

    print('Disaggregate 4G coverage to postcode sectors')
    postcode_sectors = allocate_4G_coverage(postcode_sectors, lad_lut)

    print('Importing sitefinder data')
    folder = os.path.join(DATA_RAW, 'sitefinder')
    sitefinder_data = import_sitefinder_data(os.path.join(folder, 'sitefinder.csv'))

    print('Preprocessing sitefinder data with 50m buffer')
    sitefinder_data = process_asset_data(sitefinder_data[:1000])

    print('Allocate 4G coverage to sites from postcode sectors')
    processed_sites = add_coverage_to_sites(sitefinder_data, postcode_sectors)

    print('Reading exchanges')
    exchanges = read_exchanges()

    print('Reading exchange areas')
    exchange_areas = read_exchange_areas()

    print('Generating straight line distance from each site to the nearest exchange')
    processed_sites, backhaul_links = generate_link_straight_line(processed_sites, exchanges)

    print('Convert geojson postcode sectors to list of dicts')
    postcode_sectors = convert_postcode_sectors_to_list(postcode_sectors)

    print('Specifying clutter geotypes')
    geotypes = [
        {'geotype': 'urban', 'population_density': 7959},
        {'geotype': 'suburban', 'population_density': 782},
        {'geotype': 'rural', 'population_density': 0},
    ]
    csv_writer(geotypes, directory, 'lookup_table_geotype.csv')

    print('Writing postcode sectors to .csv')
    csv_writer(postcode_sectors, directory, '_processed_postcode_sectors.csv')

    print('Writing processed sites to .csv')
    csv_writer(processed_sites, directory, 'final_processed_sites.csv')

    print('Convert assets for nismod2')
    nismod2_assets = convert_assets_for_nismod2(processed_sites)

    print('Writing digital_initial to .csv')
    nismod2_directory = os.path.join(DATA_INTERMEDIATE, 'nismod2_inputs')
    csv_writer(nismod2_assets, nismod2_directory, 'digital_initial_conditions.csv')

    end = time.time()
    print('time taken: {} minutes'.format(round((end - start) / 60,2)))
