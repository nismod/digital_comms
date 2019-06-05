"""
Infrastructure deployment module for system_simulator.py

Written by Edward Oughton
May 2019

"""
import os
import sys
import configparser
import csv

import fiona
from shapely.geometry import shape, Point, Polygon, mapping
import numpy as np
from scipy.spatial import Delaunay, Voronoi, voronoi_plot_2d
from random import shuffle
from rtree import index

np.random.seed(42)

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__),'..','..','scripts','script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')


def find_and_deploy_new_site(existing_sites, sites, interfering_sites, geojson_postcode_sector,
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
    geom = shape(geojson_postcode_sector['geometry'])

    existing_site_coordinates = []
    for interfering_site in interfering_sites:
        existing_site_coordinates.append(
            interfering_site['geometry']['coordinates']
            )

    for existing_site in existing_sites:
        existing_site_coordinates.append(
            existing_site['geometry']['coordinates']
            )

    existing_site_coordinates = np.array(
        existing_site_coordinates
        )

    tri = Delaunay(existing_site_coordinates)

    coord_groups = [tri.points[x] for x in tri.simplices]

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

    polygons = sorted(polygons, key=lambda x: x.area, reverse=True)

    points = []
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

    new_transmitters = []

    idx = len(existing_sites)

    for point in points:
        while len(new_transmitters) < sites:
            new_transmitters.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [point.x, point.y]
                },
                'properties': {
                        "sitengr": "{new}{GEN" + str(idx) + "}",
                        "ant_height": simulation_parameters['tx_baseline_height'],
                        "tech": '4G',
                        "freq": 'lte bands',#[800, 1800, 2600],
                        "type": '3 sectored macrocell',
                        "power": simulation_parameters['tx_power'],
                        "gain": simulation_parameters['tx_gain'],
                        "losses": simulation_parameters['tx_losses'],
                    }
                })
            idx += 1

    for site in existing_sites:
        new_transmitters.append(site)

    site_areas = generate_site_areas(
        new_transmitters, interfering_sites, geojson_postcode_sector
        )

    return new_transmitters, site_areas


def generate_site_areas(existing_sites, interfering_sites, geojson_postcode_sector):
    """
    Generate Voronoi site polygons.

    """
    all_sites = []

    for site in existing_sites:
        all_sites.append(site)

    for site in interfering_sites:
        all_sites.append(site)

    site_areas = generate_voronoi_areas(
        all_sites,
        geojson_postcode_sector
        )

    return site_areas

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
                    'sitengr': asset_point['properties']['sitengr']
                }
            })
        else:
            pass

    return asset_areas
