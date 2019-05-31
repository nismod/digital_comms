"""
Runner for system_simulator.py

Written by Edward Oughton
May 2019

"""
import os
import sys
import configparser
import csv

import math
import fiona
from shapely.geometry import shape, Point, Polygon, mapping
import numpy as np
from geographiclib.geodesic import Geodesic
from scipy.spatial import Delaunay, Voronoi, voronoi_plot_2d
from random import shuffle
from rtree import index

from itertools import tee
from collections import OrderedDict

from digital_comms.mobile_network.system_simulator import NetworkManager

np.random.seed(42)

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')


# def read_postcode_sector(postcode_sector, path):

#     with fiona.open(path, 'r') as source:

#         return [
#             sector for sector in source \
#             if (sector['properties']['RMSect'].replace(' ', '') ==
#                 postcode_sector.replace(' ', ''))][0]


def calculate_polygons(startx, starty, endx, endy, radius):
    """
    Calculate a grid of hexagon coordinates of the given radius
    given lower-left and upper-right coordinates
    Returns a list of lists containing 6 tuples of x, y point coordinates
    These can be used to construct valid regular hexagonal polygons

    You will probably want to use projected coordinates for this
    """
    # calculate side length given radius
    sl = (2 * radius) * math.tan(math.pi / 6)
    # calculate radius for a given side-length
    # (a * (math.cos(math.pi / 6) / math.sin(math.pi / 6)) / 2)
    # see http://www.calculatorsoup.com/calculators/geometry-plane/polygon.php

    # calculate coordinates of the hexagon points
    # sin(30)
    p = sl * 0.5
    b = sl * math.cos(math.radians(30))
    w = b * 2
    h = 2 * sl

    # offset start and end coordinates by hex widths and heights to guarantee coverage
    startx = startx - w
    starty = starty - h
    endx = endx + w
    endy = endy + h

    origx = startx
    origy = starty


    # offsets for moving along and up rows
    xoffset = b
    yoffset = 3 * p

    polygons = []
    row = 1
    counter = 0

    while starty < endy:
        if row % 2 == 0:
            startx = origx + xoffset
        else:
            startx = origx
        while startx < endx:
            p1x = startx
            p1y = starty + p
            p2x = startx
            p2y = starty + (3 * p)
            p3x = startx + b
            p3y = starty + h
            p4x = startx + w
            p4y = starty + (3 * p)
            p5x = startx + w
            p5y = starty + p
            p6x = startx + b
            p6y = starty
            poly = [
                (p1x, p1y),
                (p2x, p2y),
                (p3x, p3y),
                (p4x, p4y),
                (p5x, p5y),
                (p6x, p6y),
                (p1x, p1y)]
            polygons.append(poly)
            counter += 1
            startx += w
        starty += yoffset
        row += 1
    return polygons

def get_local_authority_ids(postcode_sector):

    postcode_sector_geom = shape(postcode_sector['geometry'])

    with fiona.open(os.path.join(
        DATA_RAW, 'd_shapes','lad_uk_2016-12', 'lad_uk_2016-12.shp'),
        'r') as source:
        return [
            lad['properties']['name'] for lad in source \
            if postcode_sector_geom.intersection(shape(lad['geometry']))
            ]


def import_area_lut(postcode_sector_name, lad_ids):

    postcode_sector_name = postcode_sector_name.replace(' ', '')

    for lad in lad_ids:
        path = os.path.join(
            DATA_RAW, '..', 'intermediate', 'mobile_geotype_lut',
            lad, lad + '.csv'
            )
        with open(path, 'r') as system_file:
            reader = csv.DictReader(system_file)
            for line in reader:
                if line['postcode_sector'].replace(' ', '') == postcode_sector_name:
                    lut = {
                        'postcode_sector': line['postcode_sector'],
                        'indoor_probability': line['indoor_probability'],
                        'outdoor_probability': line['outdoor_probability'],
                        'residential_count': line['residential_count'],
                        'non_residential_count': line['non_residential_count'],
                        'estimated_population': int(float(line['residential_count'])*2.5),
                        'area': line['area'],
                    }

    return lut


def get_sites(postcode_sector, transmitter_type, simulation_parameters):
    """
    This function either reads in existing site data, or generates it
    from scratch.

    Parameters
    ----------
    postcode_sector : geojson
        Shape file for the postcode sector being assessed
    transmitter_type : string
        Inidcates whether 'real' or 'synthetic' data should be used.

    """
    id_number = 0

    if transmitter_type == 'real':

        sites = []

        geom = shape(postcode_sector['geometry'])
        geom_length = geom.length
        geom_buffer = geom.buffer(geom_length)
        geom_box = geom_buffer.bounds

        with open(
            os.path.join(
                DATA_INTERMEDIATE, 'sitefinder', 'sitefinder_processed.csv'), 'r'
                ) as system_file:
                reader = csv.DictReader(system_file)
                for line in reader:
                    if (
                        geom_box[0] <= float(line['longitude']) and
                        geom_box[1] <= float(line['latitude']) and
                        geom_box[2] >= float(line['longitude']) and
                        geom_box[3] >= float(line['latitude'])
                        ):
                        sites.append({
                            'type': "Feature",
                            'geometry': {
                                "type": "Point",
                                "coordinates": [
                                    float(line['longitude']),
                                    float(line['latitude'])
                                    ]
                            },
                            'properties': {
                                # "operator": line[2],
                                "sitengr": 'site_id_{}'.format(id_number),
                                "ant_height": line['Antennaht'],
                                "tech": line['Transtype'],
                                "freq": 'lte bands',#line['Freqband'],
                                "type": line['Anttype'],
                                "power": simulation_parameters['tx_power'],
                                # "power_dbw": line['Powerdbw'],
                                # "max_power_dbw": line['Maxpwrdbw'],
                                # "max_power_dbm": line['Maxpwrdbm'],
                                "gain": simulation_parameters['tx_gain'],
                                "losses": simulation_parameters['tx_losses'],
                            }
                        })

                        id_number += 1
                    else:
                        pass

    elif transmitter_type == 'synthetic':

        sites = []

        geom = shape(postcode_sector['geometry'])
        geom_box = geom.bounds

        minx = geom_box[0]
        miny = geom_box[1]
        maxx = geom_box[2]
        maxy = geom_box[3]


        while len(sites) < 2:

            x_coord = np.random.uniform(low=minx, high=maxx, size=1)
            y_coord = np.random.uniform(low=miny, high=maxy, size=1)

            coordinates = list(zip(x_coord, y_coord))

            postcode_sector_shape = shape(postcode_sector['geometry'])
            site = Point((x_coord, y_coord))
            if not postcode_sector_shape.contains(site):
                sites.append({
                    'type': "Feature",
                    'geometry': {
                        "type": "Point",
                        "coordinates": [coordinates[0][0],coordinates[0][1]],
                    },
                    'properties': {
                        "sitengr": 'site_id_{}'.format(id_number),
                        "ant_height": 30,
                        "tech": '4G',
                        "freq": 'lte bands',#[800, 1800, 2600],
                        "type": '3 sectored macrocell',
                        "power": simulation_parameters['tx_power'],
                        "gain": simulation_parameters['tx_gain'],
                        "losses": simulation_parameters['tx_losses'],
                    }
                })
                id_number += 1

        else:
            pass

        while len(sites) < 3:

            postcode_sector_centroid = shape(postcode_sector['geometry']).centroid

            sites.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [postcode_sector_centroid.x, postcode_sector_centroid.y],
                },
                'properties': {
                    "sitengr": 'site_id_{}'.format(id_number),
                    "ant_height": 30,
                    "tech": '4G',
                    "freq": 'lte bands',#[800, 1800, 2600],
                    "type": '3 sectored macrocell',
                    "power": simulation_parameters['tx_power'],
                    "gain": simulation_parameters['tx_gain'],
                    "losses": simulation_parameters['tx_losses'],
                }
            })
            id_number += 1

        else:
            pass
    else:
        print('Error: Did you type an incorrect site type?')
        print('Site types must either be "real" or "synthetic"')

    return sites


def generate_receivers(postcode_sector, postcode_sector_lut, simulation_parameters):
    """
    The indoor probability provides a likelihood of a user being indoor,
    given the building footprint area and number of floors for all
    building stock, in a postcode sector.

    Parameters
    ----------
    postcode_sector : polygon
        Shape of the area we want to generate receivers within.
    postcode_sector_lut : dict
        Contains information on indoor and outdoor probability.
    simulation_parameters : dict
        Contains all necessary simulation parameters.

    Output
    ------
    receivers : List of dicts
        Contains the quantity of desired receivers within the area boundary.

    """
    indoor_probability = postcode_sector_lut['indoor_probability']

    coordinates = []

    geom = shape(postcode_sector['geometry'])
    geom_box = geom.bounds

    minx = geom_box[0]
    miny = geom_box[1]
    maxx = geom_box[2]
    maxy = geom_box[3]

    receivers = []

    id_number = 0

    while len(receivers) < simulation_parameters['iterations']:

        x_coord = np.random.uniform(low=minx, high=maxx, size=1)
        y_coord = np.random.uniform(low=miny, high=maxy, size=1)

        indoor_outdoor_probability = np.random.rand(1,1)[0][0]

        coordinates = list(zip(x_coord, y_coord))

        # Join the two
        postcode_sector_shape = shape(postcode_sector['geometry'])
        receiver = Point((x_coord, y_coord))
        if postcode_sector_shape.contains(receiver):
            receivers.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [coordinates[0][0],coordinates[0][1]],
                },
                'properties': {
                    'ue_id': "id_{}".format(id_number),
                    #"sitengr": 'TL4454059600',
                    "misc_losses": simulation_parameters['rx_misc_losses'],
                    "gain": simulation_parameters['rx_gain'],
                    "losses": simulation_parameters['rx_losses'],
                    "ue_height": float(simulation_parameters['rx_height']),
                    "indoor": str((True if float(indoor_outdoor_probability) < \
                        float(indoor_probability) else False)),
                }
            })
            id_number += 1

        else:
            pass

    return receivers


def determine_environment(postcode_sector_lut):

    population_density = (
        postcode_sector_lut['estimated_population'] / float(postcode_sector_lut['area'])
        )
    print('population_density {}'.format(population_density))
    if population_density >= 7959:
        environment = 'urban'
    elif 3119 <= population_density < 7959:
        environment = 'suburban'
    elif 782 <= population_density < 3119:
        environment = 'suburban'
    elif 112 <= population_density < 782:
        environment = 'rural'
    elif 47 <= population_density < 112:
        environment = 'rural'
    elif 25 <= population_density < 47:
        environment = 'rural'
    elif population_density < 25:
        environment = 'rural'
    else:
        environment = 'Environment not determined'
        raise ValueError('Could not determine environment')

    return environment


def generate_interfering_sites(postcode_sector, simulation_parameters):
    """

    """
    coordinates = []

    geom = shape(postcode_sector['geometry'])
    geom_length = geom.length/8
    geom_buffer = geom.buffer(geom_length)
    geom_box = geom_buffer.bounds

    minx = geom_box[0]
    miny = geom_box[1]
    maxx = geom_box[2]
    maxy = geom_box[3]

    interfering_sites = []

    id_number = 0

    while len(interfering_sites) < simulation_parameters['interfering_sites']:

        x_coord = np.random.uniform(low=minx, high=maxx, size=1)
        y_coord = np.random.uniform(low=miny, high=maxy, size=1)

        coordinates = list(zip(x_coord, y_coord))

        # Join the two
        postcode_sector_shape = shape(postcode_sector['geometry'])
        interfering_site = Point((x_coord, y_coord))
        if not postcode_sector_shape.contains(interfering_site):
            interfering_sites.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [coordinates[0][0],coordinates[0][1]],
                },
                'properties': {
                    "sitengr": 'site_id_interfering_{}'.format(id_number),
                    "ant_height": 30,
                    "tech": '4G',
                    "freq": 'lte bands',#[800, 1800, 2600],
                    "type": '3 sectored macrocell',
                    "power": simulation_parameters['tx_power'],
                    "gain": simulation_parameters['tx_gain'],
                    "losses": simulation_parameters['tx_losses'],
                }
            })
            id_number += 1

        else:
            pass

    return interfering_sites


def find_and_deploy_new_site(existing_sites, sites, geojson_postcode_sector,
    simulation_parameters):
    """
    Given existing site locations, try deploy a new one in the area
    which has the largest existing gap between sites.

    Parameters
    ----------
    existing_sites : List of objects
        Contains existing sites
    iteration_number : int
        The loop index, used for the providing the id for a new asset
    geojson_postcode_sector : GeoJson
        The postcode sector boundary in GeoJson format.

    """
    new_transmitters = []
    # print('number of sites {}'.format(sites))
    # print('len(existing_sites) {}'.format(len(existing_sites)))
    # print(geojson_postcode_sector['properties'])
    # postcode_sector_name = geojson_postcode_sector['properties']['RMSect']
    geom = shape(geojson_postcode_sector['geometry'])
    idx = 0

    points = []

    existing_site_coordinates = []
    for existing_site in existing_sites:
        existing_site_coordinates.append(
            existing_site['geometry']['coordinates']
            )

    #convert to numpy array
    existing_site_coordinates = np.array(
        existing_site_coordinates
        )

    #get delaunay grid
    tri = Delaunay(existing_site_coordinates)

    #get coordinates from grid
    coord_groups = [tri.points[x] for x in tri.simplices]

    #convert coordinate groups to polygons
    polygons = [Polygon(x) for x in coord_groups]

    to_write = []
    idx = 0
    for polygon in polygons:
        get_diff = geom.intersection(polygon)
        if get_diff.is_empty:
            pass
        else:
            to_write.append({
                'type': "GeometryCollection ",
                'geometry': mapping(get_diff),
                'properties': {
                    'id': str(idx),
                }
            })
        idx += 1

    # write_shapefile(
    #     to_write, postcode_sector_name,
    #     '{}_delaunay_{}.shp'.format(postcode_sector_name, sites)
    #     )

    #sort based on area
    polygons = sorted(polygons, key=lambda x: x.area, reverse=True)

    #try to allocate using the delauney polygon with the largest area first

    while len(points) < sites:
        for area in polygons:
            centroid = area.centroid
            if geom.contains(centroid):
                points.append(centroid)
                continue
            else:
                continue

        geom_box = geom.bounds

        minx = geom_box[0]
        miny = geom_box[1]
        maxx = geom_box[2]
        maxy = geom_box[3]

        while len(points) < sites:

            x_coord = np.random.uniform(low=minx, high=maxx, size=1)
            y_coord = np.random.uniform(low=miny, high=maxy, size=1)

            site = Point((x_coord, y_coord))

            if geom.contains(site):
                centroid = site.centroid
                points.append(centroid)
            else:
                continue

    for site in existing_sites:
        new_transmitters.append(site)

    # idx += 1
    # print('len(points) {}'.format(len(points)))
    for point in points:
        idx += 1
        new_transmitters.append({
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [point.x, point.y]
            },
            'properties': {
                    "sitengr": "{" + 'new' + "}{GEN" + str(idx) + '}',
                    "ant_height": simulation_parameters['tx_baseline_height'],
                    "tech": '4G',
                    "freq": 'lte bands',#[800, 1800, 2600],
                    "type": '3 sectored macrocell',
                    "power": simulation_parameters['tx_power'],
                    "gain": simulation_parameters['tx_gain'],
                    "losses": simulation_parameters['tx_losses'],
                }
            })
    if len(new_transmitters) > sites:
        new_transmitters = new_transmitters[:(sites+len(existing_sites))]

        # print(idx)
    # print('len(new_transmitters) {}'.format(len(new_transmitters)))
    return new_transmitters


def voronoi_finite_polygons_2d(vor, radius=None):

    """
    Reconstruct infinite voronoi regions in a 2D diagram to     -
    * vor : Voronoi
        Input diagram
    * radius : float, optional
        Distance to 'points at infinity'.
    Returns
    -------
    regions : list of tuples
        Indices of vertices in each revised Voronoi regions.
    vertices : list of tuples
        Coordinates for revised Voronoi vertices. Same as coordinates
        of input vertices, with 'points at infinity' appended to the
        end.
    """

    if vor.points.shape[1] != 2:
        raise ValueError("Requires 2D input")

    new_regions = []
    new_vertices = vor.vertices.tolist()

    center = vor.points.mean(axis=0)
    if radius is None:
        radius = vor.points.ptp().max()

    # Construct a map containing all ridges for a given point
    all_ridges = {}
    for (p1, p2), (v1, v2) in zip(vor.ridge_points, vor.ridge_vertices):
        all_ridges.setdefault(p1, []).append((p2, v1, v2))
        all_ridges.setdefault(p2, []).append((p1, v1, v2))

    # Reconstruct infinite regions
    for p1, region in enumerate(vor.point_region):
        vertices = vor.regions[region]

        if all(v >= 0 for v in vertices):
            # finite region
            new_regions.append(vertices)
            continue

        # reconstruct a non-finite region
        ridges = all_ridges[p1]
        new_region = [v for v in vertices if v >= 0]

        for p2, v1, v2 in ridges:
            if v2 < 0:
                v1, v2 = v2, v1
            if v1 >= 0:
                # finite ridge: already in the region
                continue

            # Compute the missing endpoint of an infinite ridge

            t = vor.points[p2] - vor.points[p1] # tangent
            t /= np.linalg.norm(t)
            n = np.array([-t[1], t[0]])  # normal

            midpoint = vor.points[[p1, p2]].mean(axis=0)
            direction = np.sign(np.dot(midpoint - center, n)) * n
            far_point = vor.vertices[v2] + direction * radius

            new_region.append(len(new_vertices))
            new_vertices.append(far_point.tolist())

        # sort region counterclockwise
        vs = np.asarray([new_vertices[v] for v in new_region])
        c = vs.mean(axis=0)
        angles = np.arctan2(vs[:,1] - c[1], vs[:,0] - c[0])
        new_region = np.array(new_region)[np.argsort(angles)]

        # finish
        new_regions.append(new_region.tolist())

    return new_regions, np.asarray(new_vertices)


def generate_voronoi_areas(asset_points, clip_region):

    postcode_sector = shape(clip_region['geometry'])
    # Get Points
    idx_asset_areas = index.Index()
    points = np.empty([len(list(asset_points)), 2])
    for idx, asset_point in enumerate(asset_points):

        # Prepare voronoi lookup
        points[idx] = asset_point['geometry']['coordinates']

        # Prepare Rtree lookup
        idx_asset_areas.insert(idx, shape(asset_point['geometry']).bounds, asset_point)

    # Compute Voronoi tesselation
    vor = Voronoi(points)
    regions, vertices = voronoi_finite_polygons_2d(vor)

    # Write voronoi polygons
    asset_areas = []
    for region in regions:
        polygon = vertices[region]
        geom = Polygon(polygon)
        #geom = postcode_sector.intersection(geom)
        if len(geom.bounds) >= 1:
            asset_points = list(idx_asset_areas.nearest(geom.bounds, 1, objects='raw'))

            for point in asset_points:
                # if point.is_empty:
                #     pass
                # else:
                if geom.contains(shape(point['geometry'])):
                    asset_point = point

            asset_areas.append({
                'geometry': mapping(geom),
                'properties': {
                    'id': asset_point['properties']['sitengr']
                }
            })
        else:
            pass

    return asset_areas


def obtain_threshold_values(results, simulation_parameters):
    """
    Get the threshold capacity based on a given percentile.

    """
    received_power = []
    interference = []
    noise = []
    i_plus_n = []
    sinr = []
    spectral_efficency = []
    threshold_capacity_value = []

    percentile = simulation_parameters['percentile']

    for result in results:

        rp = result['received_power']
        if rp == None:
            pass
        else:
            received_power.append(rp)

        i = result['interference']
        if i == None:
            pass
        else:
            interference.append(i)

        n = result['noise']
        if n == None:
            pass
        else:
            noise.append(n)

        i_plus_n = result['i_plus_n']
        if i_plus_n == None:
            pass
        else:
            noise.append(i_plus_n)

        sinr_value = result['sinr']
        if sinr_value == None:
            pass
        else:
            sinr.append(sinr_value)

        se = result['spectral_efficiency']
        if se == None:
            pass
        else:
            spectral_efficency.append(se)

        capacity_mbps = result['capacity_mbps']
        if capacity_mbps == None:
            pass
        else:
            threshold_capacity_value.append(capacity_mbps)

    received_power = np.percentile(received_power, percentile)
    interference = np.percentile(interference, percentile)
    noise = np.percentile(noise, percentile)
    i_plus_n = np.percentile(i_plus_n, percentile)
    spectral_efficency = np.percentile(spectral_efficency, percentile)
    sinr = np.percentile(sinr, percentile)
    capacity_mbps = np.percentile(threshold_capacity_value, percentile)

    return received_power, interference, noise, i_plus_n, \
        spectral_efficency, sinr, capacity_mbps


def calculate_network_efficiency(spectral_efficency, energy_consumption):

    if spectral_efficency == 0 or energy_consumption == 0:
        network_efficiency = 0
    else:
        network_efficiency = (
            float(spectral_efficency) / float(energy_consumption)
        )

    return network_efficiency


def write_results(results, frequency, bandwidth, num_sites, num_receivers,
    site_density, environment, technology, generation, mast_height, r_density,
    postcode_sector_name):

    suffix = 'freq_{}_bandwidth_{}_density_{}'.format(
        frequency, bandwidth, site_density
        )

    directory = os.path.join(DATA_INTERMEDIATE, 'system_simulator', postcode_sector_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = '{}.csv'.format(suffix)
    directory = os.path.join(directory, filename)

    if not os.path.exists(directory):
        results_file = open(directory, 'w', newline='')
        results_writer = csv.writer(results_file)
        results_writer.writerow((
            'environment', 'frequency_GHz','bandwidth_MHz','technology',
            'generation', 'mast_height_m', 'num_sites', 'num_receivers',
            'site_density_km2','r_density_km2',
            'received_power_dBm', 'receiver_path_loss_dB',
            'interference_dBm', 'ave_inference_pl_dB', 'inference_ave_distance',
            'network_load',  'noise_dBm', 'i_plus_n_dBm', 'sinr',
            'spectral_efficency_bps_hz', 'single_sector_capacity_mbps',
            'x', 'y'
            ))
    else:
        results_file = open(directory, 'a', newline='')
        results_writer = csv.writer(results_file)

    # output and report results for this timestep
    for result in results:
        # Output metrics
        results_writer.writerow(
            (environment,
            frequency,
            bandwidth,
            technology,
            generation,
            mast_height,
            num_sites,
            num_receivers,
            site_density,
            r_density,
            result['received_power'],
            result['path_loss'],
            result['interference'],
            result['ave_inf_pl'],
            result['ave_distance'],
            result['network_load'],
            result['noise'],
            result['i_plus_n'],
            result['sinr'],
            result['spectral_efficiency'],
            result['capacity_mbps'],
            result['x'],
            result['y'],
            ))

    results_file.close()


def write_lookup_table(
    received_power, interference, noise, i_plus_n,
    cell_edge_spectral_efficency, cell_edge_sinr, single_sector_capacity_mbps,
    area_capacity_mbps, network_efficiency, environment, operator, technology,
    frequency, bandwidth, mast_height, area_site_density, generation,
    postcode_sector_name):

    suffix = 'lookup_table_{}'.format(postcode_sector_name)

    directory = os.path.join(DATA_INTERMEDIATE, 'system_simulator', postcode_sector_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = '{}.csv'.format(suffix)
    directory = os.path.join(directory, filename)

    if not os.path.exists(directory):
        lut_file = open(directory, 'w', newline='')
        lut_writer = csv.writer(lut_file)
        lut_writer.writerow(
            ('environment', 'operator', 'technology',
            'frequency_GHz', 'bandwidth_MHz', 'mast_height_m',
            'site_density_km2', 'generation',
            'received_power_dBm', 'interference_dBm', 'noise_dBm',
            'i_plus_n_dBm', 'sinr', 'spectral_efficency_bps_hz',
            'single_sector_capacity_mbps',
            'area_capacity_mbps')
            )
    else:
        lut_file = open(directory, 'a', newline='')
        lut_writer = csv.writer(lut_file)

    # output and report results for this timestep
    lut_writer.writerow(
        (environment,
        operator,
        technology,
        frequency,
        bandwidth,
        mast_height,
        area_site_density,
        generation,
        received_power,
        interference,
        noise,
        i_plus_n,
        cell_edge_sinr,
        cell_edge_spectral_efficency,
        single_sector_capacity_mbps,
        area_capacity_mbps)
        )

    lut_file.close()


def write_shapefile(data, postcode_sector_name, filename):
    import pprint
    pprint.pprint(data)
    prop_schema = []
    for name, value in data[0]['properties'].items():
        fiona_prop_type = next((
            fiona_type for fiona_type, python_type in \
                fiona.FIELD_TYPES_MAP.items() if \
                python_type == type(value)), None
            )

        prop_schema.append((name, fiona_prop_type))

    sink_driver = 'ESRI Shapefile'
    sink_crs = {'init': 'epsg:27700'}
    sink_schema = {
        'geometry': data[0]['geometry']['type'],
        'properties': OrderedDict(prop_schema)
    }

    # Create path
    directory = os.path.join(DATA_INTERMEDIATE,
        'system_simulator', postcode_sector_name)
    if not os.path.exists(directory):
        os.makedirs(directory)

    print(os.path.join(directory, filename))
    # Write all elements to output file
    with fiona.open(
        os.path.join(directory, filename), 'w',
        driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        for feature in data:
            sink.write(feature)


def format_data(existing_data, new_data, frequency, bandwidth,
    postcode_sector_name):

    for datum in new_data:
        existing_data.append({
            'frequency': frequency,
            'bandwidth': bandwidth,
            'sinr': datum['sinr'],
            'capacity': datum['estimated_capacity']
        })

    return existing_data


def run_simulator(postcode_sector_name, environment, transmitter_type,
    simulation_parameters):

    # #get postcode sector
    # path = os.path.join(DATA_RAW, 'd_shapes', 'datashare_pcd_sectors', 'PostalSector.shp')
    # geojson_postcode_sector = read_postcode_sector(postcode_sector_name, path)

    geojson_postcode_sector = calculate_polygons(-165348, 7154206, -174173, 7146042, 200000)

    to_write = []
    idx = 0
    for hexagon in geojson_postcode_sector:
        print(hexagon)
        geom = Polygon(hexagon)
        to_write.append({
            "type": "Feature",
            "geometry": mapping(geom),
            "properties": {
                'id': 'cell_area_{}'.format(idx),
            }
        })
        idx += 1

    # print(geojson_postcode_sector)
    write_shapefile(
        to_write, 'hex',
        '{}_hex.shp'.format('test_hex')
        )

    # #get local authority district
    # local_authority_ids = get_local_authority_ids(geojson_postcode_sector)

    # #datashare_pcd_sectors lad information to postcode sectors
    # geojson_postcode_sector['properties']['local_authority_ids'] = (
    #     local_authority_ids
    #     )

    # #get the probability for inside versus outside calls
    # postcode_sector_lut = import_area_lut(
    #     postcode_sector_name, local_authority_ids
    #     )

    # # #get propagation environment (urban, suburban or rural)
    # # environment = determine_environment(postcode_sector_lut)

    # #generate receivers
    # RECEIVERS = generate_receivers(
    #     geojson_postcode_sector,
    #     postcode_sector_lut,
    #     simulation_parameters
    #     )

    # write_shapefile(
    #     RECEIVERS, postcode_sector_name,
    #     '{}_receivers.shp'.format(postcode_sector_name)
    #     )

    # interfering_sites = generate_interfering_sites(
    #     geojson_postcode_sector, simulation_parameters
    #     )

    # write_shapefile(
    #     interfering_sites, postcode_sector_name,
    #     '{}_interfering_sites.shp'.format(postcode_sector_name)
    #     )
    # idx = 0

    # for mast_height in MAST_HEIGHT:
    #     for operator, technology, frequency, bandwidth, generation in SPECTRUM_PORTFOLIO:
    #         for number_of_new_sites in [1,2,3,4]:#,5,6,7]:#[1, 2, 3, 4, 5, 6, 7]

    #             if idx == 0:
    #                 transmitters = find_and_deploy_new_site(
    #                         interfering_sites,
    #                         number_of_new_sites,
    #                         geojson_postcode_sector,
    #                         simulation_parameters
    #                         )
    #             else:
    #                 transmitters = find_and_deploy_new_site(
    #                         transmitters,
    #                         number_of_new_sites,
    #                         geojson_postcode_sector,
    #                         simulation_parameters
    #                         )

    #             manager = NetworkManager(
    #                 geojson_postcode_sector, transmitters, RECEIVERS, simulation_parameters
    #                 )

    #             current_site_density = manager.site_density()

    #             print("{} GHz {}m Height {} Density, {}".format(
    #                 frequency, mast_height, round(current_site_density, 4),
    #                 generation
    #                 ))

    #             idx += 1

    #             results = manager.estimate_link_budget(
    #                 frequency, bandwidth, generation, mast_height,
    #                 environment, MODULATION_AND_CODING_LUT,
    #                 simulation_parameters
    #                 )

    #             received_power, interference, noise, i_plus_n, spectral_efficency, \
    #                 sinr, single_sector_capacity_mbps = (
    #                     obtain_threshold_values(results, simulation_parameters)
    #                     )

    #             network_efficiency = calculate_network_efficiency(
    #                 spectral_efficency,
    #                 manager.energy_consumption(simulation_parameters)
    #                 )

    #             area_capacity_mbps = (
    #                 single_sector_capacity_mbps * simulation_parameters['sectorisation']
    #                 )
    #             print('area_capacity_mbps {}'.format(area_capacity_mbps))
    #             current_site_density = manager.site_density()
    #             print('current_site_density {}'.format(current_site_density))
    #             r_density = manager.receiver_density()

    #             write_shapefile(
    #                 transmitters, postcode_sector_name,
    #                 '{}_transmitters_{}.shp'.format(postcode_sector_name, current_site_density)
    #                 )

    #             num_sites = len(manager.sites)
    #             num_receivers = len(manager.receivers)

    #             write_results(results, frequency, bandwidth, num_sites, num_receivers,
    #                 current_site_density, environment, technology, generation, mast_height,
    #                 r_density, postcode_sector_name
    #                 )

    #             write_lookup_table(
    #                 received_power, interference, noise, i_plus_n,
    #                 spectral_efficency, sinr, single_sector_capacity_mbps,
    #                 area_capacity_mbps, network_efficiency, environment, operator,
    #                 technology, frequency, bandwidth, mast_height, current_site_density,
    #                 generation, postcode_sector_name
    #                 )

                # # cell_areas = generate_voronoi_areas(transmitters, geojson_postcode_sector)

                # # write_shapefile(
                # #     cell_areas, postcode_sector_name,
                # #     '{}_cell_areas_{}.shp'.format(postcode_sector_name, current_site_density)
                # #     )

                # manager = []

#####################################
# APPLY METHODS
#####################################

SPECTRUM_PORTFOLIO = [
    ('generic', 'FDD DL', 0.7, 10, '5G'),
    ('generic', 'FDD DL', 0.8, 10, '4G'),
    # ('generic', 'FDD DL', 1.8, 10, '4G'),
    # ('generic', 'FDD DL', 2.6, 10, '4G'),
    # ('generic', 'FDD DL', 3.5, 80, '5G'),
]

MAST_HEIGHT = [
    (30),
    #(40)
]

MODULATION_AND_CODING_LUT =[
    # CQI Index	Modulation	Coding rate
    # Spectral efficiency (bps/Hz) SINR estimate (dB)
    ('4G', 1, 'QPSK',	0.0762,	0.1523, -6.7),
    ('4G', 2, 'QPSK',	0.1172,	0.2344, -4.7),
    ('4G', 3, 'QPSK',	0.1885,	0.377, -2.3),
    ('4G', 4, 'QPSK',	0.3008,	0.6016, 0.2),
    ('4G', 5, 'QPSK',	0.4385,	0.877, 2.4),
    ('4G', 6, 'QPSK',	0.5879,	1.1758,	4.3),
    ('4G', 7, '16QAM', 0.3691, 1.4766, 5.9),
    ('4G', 8, '16QAM', 0.4785, 1.9141, 8.1),
    ('4G', 9, '16QAM', 0.6016, 2.4063, 10.3),
    ('4G', 10, '64QAM', 0.4551, 2.7305, 11.7),
    ('4G', 11, '64QAM', 0.5537, 3.3223, 14.1),
    ('4G', 12, '64QAM', 0.6504, 3.9023, 16.3),
    ('4G', 13, '64QAM', 0.7539, 4.5234, 18.7),
    ('4G', 14, '64QAM', 0.8525, 5.1152, 21),
    ('4G', 15, '64QAM', 0.9258, 5.5547, 22.7),
    ('5G', 1, 'QPSK', 78, 0.1523, -6.7),
    ('5G', 2, 'QPSK', 193, 0.377, -4.7),
    ('5G', 3, 'QPSK', 449, 0.877, -2.3),
    ('5G', 4, '16QAM', 378, 1.4766, 0.2),
    ('5G', 5, '16QAM', 490, 1.9141, 2.4),
    ('5G', 6, '16QAM', 616, 2.4063, 4.3),
    ('5G', 7, '64QAM', 466, 2.7305, 5.9),
    ('5G', 8, '64QAM', 567, 3.3223, 8.1),
    ('5G', 9, '64QAM', 666, 3.9023, 10.3),
    ('5G', 10, '64QAM', 772, 4.5234, 11.7),
    ('5G', 11, '64QAM', 873, 5.1152, 14.1),
    ('5G', 12, '256QAM', 711, 5.5547, 16.3),
    ('5G', 13, '256QAM', 797, 6.2266, 18.7),
    ('5G', 14, '256QAM', 885, 6.9141, 21),
    ('5G', 15, '256QAM', 948, 7.4063, 22.7),
]

site_densities = {
    'urban': [
        7.22, 3.21, 1.8, 1.15, 0.8, 0.59,
        0.45, 0.36, 0.29, 0.24, 0.2, 0.17,
        0.15, 0.13, 0.11, 0.1, 0.09, 0.08,
        0.07, 0.05, 0.03, 0.02
    ],
    'suburban': [
        0.59, 0.45, 0.36, 0.29, 0.24, 0.2,
        0.17, 0.15, 0.13, 0.09, 0.07, 0.06,
        0.05, 0.03, 0.0236, 0.018, 0.0143,
        0.0115, 0.0095, 0.008, 0.0321
    ],
    'rural': [
        0.0500, 0.0115, 0.0080, 0.0051,
        0.0040, 0.0029, 0.0024, 0.0018,
        0.0016, 0.0013, 0.0009, 0.0007,
        0.0006,
    ]
}

# if __name__ == "__main__":

    # SIMULATION_PARAMETERS = {
    #     'iterations': 5,
    #     'seed_value': None,
    #     'tx_baseline_height': 30,
    #     'tx_upper_height': 40,
    #     'tx_power': 40,
    #     'tx_gain': 16,
    #     'tx_losses': 1,
    #     'rx_gain': 4,
    #     'rx_losses': 4,
    #     'rx_misc_losses': 4,
    #     'rx_height': 1.5,
    #     'network_load': 50,
    #     'percentile': 5,
    #     'desired_transmitter_density': 10,
    #     'sectorisation': 3,
    # }

    # if len(sys.argv) != 3:
    #     print("Error: no postcode sector or transmitter type argument provided")
    #     exit(-1)
    # if sys.argv[2] != 'real' and sys.argv[2] != 'synthetic':
    #     print("Transmitter type error: must be either 'real' or 'synthetic'")
    #     exit(-1)

    # print('Process ' + sys.argv[1])
    # postcode_sector_name = sys.argv[1]

    # print('running')
    # run_simulator(postcode_sector_name, sys.argv[2], SIMULATION_PARAMETERS)
