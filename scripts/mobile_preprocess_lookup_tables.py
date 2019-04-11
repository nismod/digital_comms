import os
import sys
import configparser
import csv
import glob

from rtree import index
import fiona
from shapely.geometry import shape, Point, Polygon, MultiPoint, mapping
from shapely.wkt import loads
from shapely.prepared import prep

from collections import OrderedDict

CONFIG = configparser.ConfigParser()
CONFIG.read(
    os.path.join(os.path.dirname(__file__), 'script_config.ini')
)
BASE_PATH = CONFIG['file_locations']['base_path']

#data locations
DATA_RAW = os.path.join(BASE_PATH, 'raw')
DATA_RESULTS = os.path.join(BASE_PATH, 'intermediate')

def get_local_authority_district(lad_id):

    with fiona.open(os.path.join(
        DATA_RAW, 'd_shapes','lad_uk_2016-12', 'lad_uk_2016-12.shp'), 'r') as source:

        return [lad for lad in source if lad['properties']['name'] == lad_id][0]

def find_existing_processed_postcode_sectors(lad):

    processed_postcode_sectors = []

    path = os.path.join(BASE_PATH, 'intermediate', 'mobile_geotype_lut', lad, lad + '.csv')

    if not os.path.exists(path):

        pass

    else:

        with open(path, 'r') as system_file:
            reader = csv.DictReader(system_file)
            for line in reader:
                processed_postcode_sectors.append(
                    line['postcode_sector']
                    )

    return processed_postcode_sectors

def get_postcode_sectors(processed_postcode_sectors, lad_id):

    lut_directory = os.path.join(DATA_RAW, '..', 'intermediate',
    'pcd_sector_to_lad_lut', 'pcd_sector_to_lad_lut.csv'
    )

    pcd_sector_to_lad_lut = []

    with open(lut_directory, 'r') as system_file:
        reader = csv.DictReader(system_file)
        next(reader)
        for line in reader:
            if line['lad'] == lad_id:
                pcd_sector_to_lad_lut.append(
                    line['postcode_sector']
                    )

    all_postcode_sectors = []

    directory = os.path.join(DATA_RAW, 'd_shapes', 'postcode_sectors')
    pathlist = glob.iglob(directory + '/*.shp', recursive=True)
    for path in pathlist:
        with fiona.open(path, 'r') as source:
            for postcode_sector in source:
                if postcode_sector['properties']['postcode'] not in processed_postcode_sectors:
                    all_postcode_sectors.append(postcode_sector)
                else:
                    pass

    intersecting_postcode_sectors = []
    postcode_sector_ids = []

    for postcode_sector in all_postcode_sectors:
        if postcode_sector['properties']['postcode'] in pcd_sector_to_lad_lut:
            intersecting_postcode_sectors.append(postcode_sector)
            postcode_sector_ids.append(postcode_sector['properties']['postcode'])

    touching_lad_ids =  set()

    with open(lut_directory, 'r') as system_file:
        reader = csv.DictReader(system_file)
        next(reader)
        for line in reader:
            if line['postcode_sector'] in postcode_sector_ids:
                touching_lad_ids.add(
                    line['lad']
                    )

    return intersecting_postcode_sectors, touching_lad_ids

def read_building_polygons(postcode_sectors, lad_ids):
    """
    This function imports the building polygons from
    the relevant local authority lookup tables.

    """
    idx = index.Index()

    def premises():
        i = 0
        for lad_id in lad_ids:
            directory = os.path.join(DATA_RAW, 'e_dem_and_buildings', 'prems_by_lad', lad_id)
            pathlist = glob.iglob(directory + '/*.csv', recursive=True)
            for path in pathlist:
                with open(path, 'r') as system_file:
                    reader = csv.DictReader(system_file)
                    next(reader)
                    for line in reader:
                        geom = loads(line['geom'])
                        geom_point = geom.representative_point()
                        feature = {
                            'type': 'Feature',
                            'geometry': mapping(geom),
                            'representative_point': geom_point,
                            'properties':{
                                'res_count': line['res_count'],
                                'floor_area': line['floor_area'],
                                'height_toroofbase': line['height_toroofbase'],
                                'height_torooftop': line['height_torooftop'],
                                'number_of_floors': line['number_of_floors'],
                                'footprint_area': line['footprint_area'],
                            }
                        }
                        yield (i, geom_point.bounds, feature)

    idx = index.Index(premises())

    output = []

    for postcode_sector in postcode_sectors:
        postcode_shape = shape(postcode_sector['geometry'])
        prepared_area = prep(postcode_shape)
        for n in idx.intersection((postcode_shape.bounds), objects=True):
            point = n.object['representative_point']
            if prepared_area.contains(point):
                del n.object['representative_point']
                output.append(n.object)

    return output

def get_intersecting_buildings(postcode_sector, buildings):

    intersecting_buildings = []

    # Initialze Rtree
    idx = index.Index()
    [idx.insert(0, shape(building['geometry']).bounds, building) for building in buildings]

    for n in idx.intersection((shape(postcode_sector['geometry']).bounds), objects=True):
        postcode_sector_shape = shape(postcode_sector['geometry'])
        premise_shape = shape(n.object['geometry'])
        if postcode_sector_shape.contains(premise_shape.representative_point()):
            intersecting_buildings.append(n.object)


    return intersecting_buildings

def calculate_indoor_outdoor_ratio(postcode_sector, buildings):
    """
    Gets the percentage probability of a user being either indoor or outdoor.

    Note: the sum of total_inside_floor_area and total_outside_area will not sum up to
    the postcode_sector_area, as total_inside_floor_area takes into account all floors
    in a building, not just the building footprint.

    If there is no floor_area data, use the footprint_area data.

    Parameters
    ----------
    footprint_area : float
        Estimate of a building's geographical area.
    floor_area : float
        Estimate of a building's indoor area across all floors.

    """
    #start with total building footprint area
    building_footprint = 0
    for building in buildings:
        try:
            footprint_area = float(building['properties']['footprint_area'])
        except ValueError:
            footprint_area = 0
        building_footprint += footprint_area

    #start with gross indoor area
    total_inside_floor_area = 0
    for building in buildings:
        try:
            floor_area = float(building['properties']['floor_area'])
        except ValueError:
            floor_area = float(building['properties']['footprint_area'])
        total_inside_floor_area += floor_area

    #now calculate gross outside area
    geom = shape(postcode_sector['geometry'])
    postcode_sector_area = geom.area
    total_outside_area = postcode_sector_area - building_footprint

    #get total potential usage area (note: greater than postcode sector area)
    total_usage_area = total_outside_area + total_inside_floor_area

    #calculate percentage probability between indoor/outdoor
    indoor_probability = total_inside_floor_area/total_usage_area*100
    outdoor_probability = total_outside_area/total_usage_area*100

    return (indoor_probability, outdoor_probability)

def get_geotype_information(postcode_sector, buildings):
    """
    Use the building density to estimate the geotype

    """
    #count residential address points
    residential_count = 0
    non_residential_count = 0
    non_res_count = 0
    for building in buildings:
        try:
            res_count = float(building['properties']['res_count'])
            non_res_count = 0
        except ValueError:
            res_count = 0
            non_res_count = 1
        residential_count += res_count
        non_residential_count += non_res_count
    print('residential_count is {}'.format(residential_count))
    #get area in km^2
    geom = shape(postcode_sector['geometry'])
    area = geom.area/1000000
    print('non_residential_count is {}'.format(non_residential_count))
    return residential_count, non_residential_count, area

def csv_writer(data_for_writing, lad):
    """
    Write data to a CSV file path

    """
    #get fieldnames
    fieldnames = []
    for name, value in data_for_writing[0].items():
        fieldnames.append(name)

    data_for_writing = data_for_writing[0]

    #create path
    directory = os.path.join(BASE_PATH, 'intermediate', 'mobile_geotype_lut', lad)
    if not os.path.exists(directory):
        os.makedirs(directory)

    path = os.path.join(directory, lad + '.csv')

    if not os.path.exists(path):
        lut_file = open(path, 'w', newline='')
        lut_writer = csv.writer(lut_file)
        lut_writer.writerow(
            ('postcode_sector', 'indoor_probability', 'outdoor_probability',
            'residential_count', 'non_residential_count', 'area'))

    else:
        lut_file = open(path, 'a', newline='')
        lut_writer = csv.writer(lut_file)
        print('added {} to csv'.format(data_for_writing['postcode_sector']))


    # output and report results for this timestep
    lut_writer.writerow(
        (data_for_writing['postcode_sector'],
        data_for_writing['indoor_probability'],
        data_for_writing['outdoor_probability'],
        data_for_writing['residential_count'],
        data_for_writing['non_residential_count'],
        data_for_writing['area']),
        )

    lut_file.close()

#####################################
# APPLY METHODS
#####################################

if __name__ == "__main__":

    SYSTEM_INPUT = os.path.join('data', 'raw')

    if len(sys.argv) != 2:
        print("Error: no exchange or abbreviation provided")
        print("Usage: {} <lad>".format(os.path.basename(__file__)))
        exit(-1)

    # Read LUTs
    print('Process ' + sys.argv[1])
    lad_name = sys.argv[1]

    #get lad shape
    print('get lad shape')
    lad = get_local_authority_district(lad_name)

    #find unprocessed postcode sectors
    print('finding unprocessed postcode sectors')
    processed_postcode_sectors = find_existing_processed_postcode_sectors(lad_name)

    #get lut of all postcode sectors in or intersecting the lad
    print('get pcd_sectors intersecting with lad boundary')
    postcode_sectors, touching_lad_ids = get_postcode_sectors(
        processed_postcode_sectors, lad_name
        )
    if len(postcode_sectors) == 0:

        pass

    else:

        #get buildings
        print('loading in buildings')
        buildings = read_building_polygons(postcode_sectors, touching_lad_ids)

        for postcode_sector in postcode_sectors:

            print('processing {}'.format(postcode_sector['properties']['postcode']))
            postcode_sector_name = postcode_sector['properties']['postcode']

            #intersect buildings and pcd_sector
            postcode_sector_buildings = get_intersecting_buildings(postcode_sector, buildings)

            #get the probability for inside versus outside calls
            indoor_outdoor_probability = calculate_indoor_outdoor_ratio(
                postcode_sector, postcode_sector_buildings
                )

            print('indoor is {} and outdoor is {}'.format(
                indoor_outdoor_probability[0],
                indoor_outdoor_probability[1]))

            residential_count, non_residential_count, area = \
                get_geotype_information(postcode_sector, postcode_sector_buildings)

            data_for_writing = []
            data_for_writing.append({
                'postcode_sector': postcode_sector_name,
                'indoor_probability': indoor_outdoor_probability[0],
                'outdoor_probability': indoor_outdoor_probability[1],
                'residential_count': residential_count,
                'non_residential_count': non_residential_count,
                'area': area,
            })

            csv_writer(data_for_writing, lad_name)
