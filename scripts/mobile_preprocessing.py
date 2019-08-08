import os
import sys
import configparser
import csv
import fiona

from shapely.geometry import shape, Point, LineString, Polygon, MultiPolygon, mapping, MultiPoint
from shapely.ops import unary_union, cascaded_union
from shapely.wkt import loads
from shapely.prepared import prep
from pyproj import Proj, transform

from rtree import index
import tqdm as tqdm

from collections import OrderedDict
import osmnx as ox
import networkx as nx

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# setup file locations and data files
#####################################

DATA_RAW_INPUTS = os.path.join(BASE_PATH, 'raw', 'b_mobile_model')
DATA_FIXED_INPUTS = os.path.join(BASE_PATH, 'raw', 'a_fixed_model')
DATA_RAW_SHAPES = os.path.join(BASE_PATH, 'raw', 'd_shapes')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')

#####################################
# READ MAIN DATA
#####################################

def read_lads():
    """
    Read in all lad shapes.

    """
    lad_shapes = os.path.join(
        DATA_RAW_SHAPES, 'lad_uk_2016-12', 'lad_uk_2016-12.shp'
        )

    with fiona.open(lad_shapes, 'r') as lad_shape:
        return [lad for lad in lad_shape if #lad['properties']['name'].startswith('E07000191')]
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
        #if lad['properties']['name'].startswith('E07000191'):
        yield lad['properties']['name']


def load_geotype_lut(lad_id):

    directory = os.path.join(
        DATA_INTERMEDIATE, 'mobile_geotype_lut', lad_id
    )

    path = os.path.join(directory, lad_id + '.csv')

    with open(path, 'r') as source:
        reader = csv.DictReader(source)
        for line in reader:
            total_premises = (
                int(float(line['residential_count'])) +
                int(float(line['non_residential_count']))
                )
            yield {
                'postcode_sector': line['postcode_sector'],
                'total_premises': total_premises,
                'area_km2': float(line['area']),
                'premises_density_km2': total_premises / float(line['area']),
            }

def read_postcode_sectors(path):
    """
    Read all postcode sector shapes.

    """
    with fiona.open(path, 'r') as pcd_sector_shapes:
        return [pcd for pcd in pcd_sector_shapes]# if pcd['properties']['postcode'].startswith('CB')]


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
                        'postcode': postcode_sector['properties']['RMSect'],
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
        DATA_RAW_INPUTS, 'ofcom_2018', '201809_mobile_laua_r02.csv'
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
        DATA_RAW_INPUTS, 'mobile_model_1.0',
        'scenario_data', 'population_baseline_pcd.csv'
        )

    population_data = []

    with open(path, 'r') as source:
        reader = csv.reader(source)
        for line in reader:
            if int(line[0]) == 2015:
                population_data.append({
                    'postcode_sector': line[1],
                    'population': int(line[2]),
                })

    return population_data


def add_weights_to_postcode_sector(postcode_sectors, weights):
    """
    Add weights to postcode sector

    """
    output = []

    for postcode_sector in postcode_sectors:
        pcd_id = postcode_sector['properties']['postcode'].replace(' ', '')
        for weight in weights:
            weight_id = weight['postcode_sector'].replace(' ', '')
            if pcd_id == weight_id:
                output.append({
                    'type': postcode_sector['type'],
                    'geometry': postcode_sector['geometry'],
                    'properties': {
                        'pcd_sector': pcd_id,
                        'lad': postcode_sector['properties']['lad'],
                        'population_weight': weight['population'],
                        'area_km2': (postcode_sector['properties']['area'] / 1e6),
                    }
                })


    return output


def calculate_lad_population(postcode_sectors):

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
                        'pcd_sector': pcd_sector['properties']['pcd_sector'],
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

    folder = os.path.join(DATA_RAW_INPUTS, 'arc_scenarios')

    with open(os.path.join(folder, filename), 'r') as source:
        reader = csv.DictReader(source)
        for line in reader:
            yield {
                'year': line['timestep'],
                'lad': line['lad_uk_2016'],
                'population': line['population'],
            }

def disaggregate(forecast, postcode_sectors):

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
                    'pcd_sector': postcode_sector['properties']['pcd_sector'],
                    'population': int(
                        float(line['population']) *
                        float(postcode_sector['properties']['weight'])
                        )
                })

    return output


def generate_scenario_variants(postcode_sectors):
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
            csv_writer_forecasts(disaggregated_forecast, filename)


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
                        'id': 'site_' + str(site_id),
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
                'id': asset['properties']['id'],
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
                        'pcd_sector': postcode_sector['properties']['pcd_sector'],
                        'id': n.object['properties']['id'],
                        'lte_4G': postcode_sector['properties']['lte']
                        }
                    })

    return final_sites


def read_exchanges():
    """
    Reads in exchanges from 'final_exchange_pcds.csv'.

    """
    path = os.path.join(
        DATA_FIXED_INPUTS, 'layer_2_exchanges', 'final_exchange_pcds.csv'
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
                    'id': 'exchange_' + line['OLO'],
                    'Name': line['Name'],
                    'pcd': line['exchange_pcd'],
                }
            }


def read_exchange_areas():
    """
    Read exchange polygons

    """
    path = os.path.join(
        DATA_RAW_SHAPES, 'all_exchange_areas', '_exchange_areas_fixed.shp'
        )

    with fiona.open(path, 'r') as source:
        for area in source:
            yield area


def select_routing_points(origin_point, dest_points, areas):

    idx = index.Index(
        (i, Point(dest_point['geometry']['coordinates']).bounds, dest_point)
        for i, dest_point in enumerate(dest_points)
        )

    nearest_exchange = list(idx.nearest(
            Point(origin_point['geometry']['coordinates']).bounds,
            1, objects='raw'))[0]

    exchange_id = nearest_exchange['properties']['id']

    for exchange_area in areas:
        if exchange_area['properties']['id'] == exchange_id:
            return nearest_exchange, exchange_area


def return_object_coordinates(object):

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


def generate_shortest_path(origin_points, dest_points, areas):
    """
    Calculate distance between each site (origin_points) and the
    nearest exchange (dest_points).

    """
    processed_sites = []
    links = []

    idx = index.Index(
        (i, Point(dest_point['geometry']['coordinates']).bounds, dest_point)
        for i, dest_point in enumerate(dest_points)
        )

    for site in origin_points:

        exchange = list(idx.nearest(
            Point(site['geometry']['coordinates']).bounds,
            1, objects='raw'))[0]

        exchange_id = exchange['properties']['id']

        for exchange_polygon in areas:
            if exchange_polygon['properties']['id'] == exchange_id:
                exchange_area = exchange_polygon

        ox.config(log_file=False, log_console=False, use_cache=True)

        projUTM = Proj(init='epsg:27700')
        projWGS84 = Proj(init='epsg:4326')

        east, north = transform(
            projUTM, projWGS84, shape(exchange_area['geometry']).bounds[2],
            shape(exchange_area['geometry']).bounds[3]
            )

        west, south = transform(
            projUTM, projWGS84, shape(exchange_area['geometry']).bounds[0],
            shape(exchange_area['geometry']).bounds[1]
            )

        G = ox.graph_from_bbox(
            north, south, east, west, network_type='all',
            truncate_by_edge=True
            )

        origin_x, origin_y = return_object_coordinates(site)
        dest_x, dest_y = return_object_coordinates(exchange)

        # Find shortest path between the two
        point1_x, point1_y = transform(projUTM, projWGS84, origin_x, origin_y)
        point2_x, point2_y = transform(projUTM, projWGS84, dest_x, dest_y)

        # Find shortest path between the two
        point1 = (point1_y, point1_x)
        point2 = (point2_y, point2_x)

        # TODO improve by finding nearest edge,
        # routing to/from node at either end
        origin_node = ox.get_nearest_node(G, point1)
        destination_node = ox.get_nearest_node(G, point2)

        try:
            if origin_node != destination_node:
                route = nx.shortest_path(
                    G, origin_node, destination_node, weight='length'
                    )

                # Retrieve route nodes and lookup geographical location
                routeline = []
                routeline.append((origin_x, origin_y))
                for node in route:
                    routeline.append((
                        transform(projWGS84, projUTM,
                        G.nodes[node]['x'], G.nodes[node]['y'])
                        ))
                routeline.append((dest_x, dest_y))
                line = routeline
            else:
                line = [(origin_x, origin_y), (dest_x, dest_y)]
        except nx.exception.NetworkXNoPath:
            line = [(origin_x, origin_y), (dest_x, dest_y)]

        # Map to line
        processed_sites.append({
            'type': 'Feature',
            'geometry': site['geometry'],
            'properties':{
                'id': site['properties']['id'],
                'Antennaht': site['properties']['Antennaht'],
                'Transtype': site['properties']['Transtype'],
                'Freqband': site['properties']['Freqband'],
                'Anttype': site['properties']['Anttype'],
                'Powerdbw': site['properties']['Powerdbw'],
                'Maxpwrdbw': site['properties']['Maxpwrdbw'],
                'Maxpwrdbm': site['properties']['Maxpwrdbm'],
                'lte_4G': site['properties']['lte_4G'],
                'exchange': exchange['properties']['id'],
                'backhaul_length_m': LineString(line).length
                }
        })

        # Map to line
        links.append({
            'type': "Feature",
            'geometry': {
                "type": "LineString",
                "coordinates": line
            },
            'properties': {
                "site": site['properties']['id'],
                "exchange": exchange['properties']['id'],
                "length": LineString(line).length
            }
        })

    return links, processed_sites


def generate_link_straight_line(origin_points, dest_points):

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

            # Get length
            geom = LineString([
                (origin_x, origin_y), (dest_x, dest_y)
                ])

            processed_sites.append({
                'type': 'Feature',
                'geometry': origin_point['geometry'],
                'properties':{
                    'pcd_sector': origin_point['properties']['pcd_sector'],
                    'id': origin_point['properties']['id'],
                    'lte_4G': origin_point['properties']['lte_4G'],
                    'exchange': exchange['properties']['id'],
                    'backhaul_length_m': geom.length * 1.60934
                    }
                })

            links.append({
                'type': "Feature",
                'geometry': mapping(geom),
                'properties': {
                    "origin_id": origin_point['properties']['id'],
                    "dest_id": exchange['properties']['id'],
                    "length": geom.length * 1.60934
                }
            })

        except:
            print('- Problem with straight line link for:')
            print(origin_point['properties'])

    return processed_sites, links


def write_shapefile(data, folder_name, filename):

    # Translate props to Fiona sink schema
    prop_schema = []
    for name, value in data[0]['properties'].items():
        fiona_prop_type = next((fiona_type for fiona_type, python_type in
        fiona.FIELD_TYPES_MAP.items() if python_type == type(value)), None)
        prop_schema.append((name, fiona_prop_type))

    sink_driver = 'ESRI Shapefile'
    sink_crs = {'init': 'epsg:27700'}
    sink_schema = {
        'geometry': data[0]['geometry']['type'],
        'properties': OrderedDict(prop_schema)
    }

    # Create path
    directory = os.path.join(DATA_INTERMEDIATE, folder_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    print(os.path.join(directory, filename))
    # Write all elements to output file
    with fiona.open(os.path.join(directory, filename), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        [sink.write(feature) for feature in data]


def csv_writer_forecasts(data, filename):
    """
    Write data to a CSV file path
    """
    # Create path
    directory = os.path.join(DATA_INTERMEDIATE, 'arc_scenarios')
    if not os.path.exists(directory):
        os.makedirs(directory)

    fieldnames = []
    for name, value in data[0].items():
        fieldnames.append(name)

    with open(os.path.join(directory, filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)


def csv_writer_sites(data, filename):
    """
    Write data to a CSV file path

    """
    data_for_writing = []
    for asset in data:
        data_for_writing.append({
            'pcd_sector': asset['properties']['pcd_sector'],
            'id': asset['properties']['id'],
            'lte_4G':  asset['properties']['lte_4G'],
            'exchange':  asset['properties']['exchange'],
            'backhaul_length_m':  asset['properties']['backhaul_length_m'],
        })

    #get fieldnames
    fieldnames = []
    for name, value in data_for_writing[0].items():
        fieldnames.append(name)

    #create path
    directory = os.path.join(BASE_PATH, 'processed')
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(os.path.join(directory, filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data_for_writing)


def csv_writer_postcode_sectors(data, filename):
    """
    Write data to a CSV file path

    """
    data_for_writing = []
    for datum in data:
        data_for_writing.append({
            'pcd_sector': datum['properties']['pcd_sector'],
            'lad': datum['properties']['lad'],
            'population': datum['properties']['population'],
            'area_km2': datum['properties']['area_km2'],
            'pop_density_km2': datum['properties']['pop_density_km2'],
            'lte_4G': datum['properties']['lte'],
        })

    #get fieldnames
    fieldnames = []
    for name, value in data_for_writing[0].items():
        fieldnames.append(name)

    #create path
    directory = os.path.join(BASE_PATH, 'processed')
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(os.path.join(directory, filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data_for_writing)


if __name__ == "__main__":

    print('Loading local authority district shapes')
    lads = read_lads()

    print('Loading lad lookup')
    lad_lut = lad_lut(lads)

    print('Loading postcode sector shapes')
    path = os.path.join(
        DATA_RAW_SHAPES, 'datashare_pcd_sectors', 'PostalSector.shp'
        )
    postcode_sectors = read_postcode_sectors(path)

    print('Adding lad IDs to postcode sectors... might take a few minutes...')
    postcode_sectors = add_lad_to_postcode_sector(postcode_sectors, lads)

    print('Loading in population weights' )
    weights = load_in_weights()

    print('Adding weights to postcode sectors')
    postcode_sectors = add_weights_to_postcode_sector(postcode_sectors, weights)

    print('Calculating lad population weight for each postcode sector')
    postcode_sectors = calculate_lad_population(postcode_sectors)

    print('Generating scenario variants')
    generate_scenario_variants(postcode_sectors)

    print('Disaggregate 4G coverage to postcode sectors')
    postcode_sectors = allocate_4G_coverage(
        postcode_sectors, lad_lut
        )
    print('postcode_sectors length is {}'.format(len(postcode_sectors)))

    print('Importing sitefinder data')
    folder = os.path.join(BASE_PATH,'raw','b_mobile_model','sitefinder')
    sitefinder_data = import_sitefinder_data(os.path.join(folder, 'sitefinder.csv'))

    print('Preprocessing sitefinder data with 50m buffer')
    sitefinder_data = process_asset_data(sitefinder_data)

    print('Allocate 4G coverage to sites from postcode sectors')
    processed_sites = add_coverage_to_sites(sitefinder_data, postcode_sectors)

    print('Reading exchanges')
    exchanges = read_exchanges()

    print('Reading exchange areas')
    exchange_areas = read_exchange_areas()

    # print('Generating shortest path link')
    # backhaul_links, processed_sites = generate_shortest_path(
    #     processed_sites, exchanges, exchange_areas
    #     )

    print('Generating straight line distance from each site to the nearest exchange')
    processed_sites, backhaul_links = generate_link_straight_line(processed_sites, exchanges)

    print('Writing processed sites to .csv')
    csv_writer_sites(processed_sites, 'final_processed_sites.csv')

    print('Writing postcode sectors to .csv')
    csv_writer_postcode_sectors(postcode_sectors, '_processed_postcode_sectors.csv')

    # write_shapefile(
    #     postcode_sectors, 'postcode_sectors', '_processed_postcode_sectors.shp'
    #     )
    # write_shapefile(
    #     processed_sites, 'sitefinder', 'final_processed_sites.shp'
    #     )
    # write_shapefile(
    #     backhaul_links, 'sitefinder', 'backhaul_routes.shp'
    #     )
