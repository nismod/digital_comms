import time
start = time.time()
import os
import configparser
import csv
import fiona
import numpy as np

from itertools import groupby
from operator import itemgetter

from rtree import index
from shapely.geometry import shape, Point, LineString, Polygon, mapping, MultiPolygon
from shapely.ops import unary_union
from collections import OrderedDict, defaultdict
from functools import partial
import pyproj
from shapely.ops import transform

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# SETUP SYSTEM FILE LOCATIONS
#####################################

SYSTEM_INPUT_PATH = os.path.join(BASE_PATH, 'raw')
SYSTEM_OUTPUT_PATH = os.path.join(BASE_PATH, 'processed')

#####################################
# SETUP CODEPOINT FILE LOCATIONS
#####################################

CODEPOINT_INPUT_PATH = os.path.join(BASE_PATH, 'raw', 'codepoint')
CODEPOINT_OUTPUT_PATH = os.path.join(BASE_PATH, 'raw', 'codepoint')

#####################################
# IMPORT CODEPOINT SHAPES
#####################################

def import_postcodes(data):

    my_postcode_data = []

    # Initialze Rtree
    idx = index.Index()

    for dirpath, subdirs, files in os.walk(data):
        for x in files:
            if x.endswith(".shp"):
                with fiona.open(os.path.join(dirpath, x), 'r') as source:

                    # Store shapes in Rtree
                    for src_shape in source:
                        idx.insert(int(src_shape['id']), shape(src_shape['geometry']).bounds, src_shape)

                    # Split list in regular and vertical postcodes
                    postcodes = {}
                    vertical_postcodes = {}

                    for x in source:

                        x['properties']['POSTCODE'] = x['properties']['POSTCODE'].replace(" ", "")
                        if x['properties']['POSTCODE'].startswith('V'):
                            vertical_postcodes[x['id']] = x
                        else:
                            postcodes[x['id']] = x

                    for key, f in vertical_postcodes.items():

                        vpost_geom = shape(f['geometry'])
                        best_neighbour = {'id': 0, 'intersection': 0}

                        # Find best neighbour
                        for n in idx.intersection((vpost_geom.bounds), objects=True):
                            if shape(n.object['geometry']).intersection(vpost_geom).length > best_neighbour['intersection'] and n.object['id'] != f['id']:
                                best_neighbour['id'] = n.object['id']
                                best_neighbour['intersection'] = shape(n.object['geometry']).intersection(vpost_geom).length

                        # Merge with best neighbour
                        neighbour = postcodes[best_neighbour['id']]
                        merged_geom = unary_union([shape(neighbour['geometry']), vpost_geom])

                        merged_postcode = {
                            'id': neighbour['id'].replace(" ", ""),
                            'properties': neighbour['properties'],
                            'geometry': mapping(merged_geom)
                        }

                        try:
                            postcodes[merged_postcode['id']] = merged_postcode
                        except:
                            raise Exception

                    for key, p in postcodes.items():
                        p.pop('id')
                        my_postcode_data.append(p)

    return my_postcode_data

def add_postcode_sector_indicator(data):

    my_postcode_data = []

    for x in data:
        x['properties']['pcd_sector'] = x['properties']['POSTCODE'][:-2]
        my_postcode_data.append(x)

    return my_postcode_data

def write_shapefile(data, path, crs):

    # Translate props to Fiona sink schema
    prop_schema = []
    for name, value in data[0]['properties'].items():
        fiona_prop_type = next((fiona_type for fiona_type, python_type in fiona.FIELD_TYPES_MAP.items() if python_type == type(value)), None)
        prop_schema.append((name, fiona_prop_type))

    sink_driver = 'ESRI Shapefile'
    sink_crs = {'init':crs}
    sink_schema = {
        'geometry': data[0]['geometry']['type'],
        'properties': OrderedDict(prop_schema)
    }

    # Write all elements to output file
    with fiona.open(path, 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        for feature in data:
            sink.write(feature)

def dissolve(input, output, fields):
    with fiona.open(os.path.join(CODEPOINT_INPUT_PATH, input)) as input:
        with fiona.open(os.path.join(SYSTEM_OUTPUT_PATH, output), 'w', **input.meta) as output:
            grouper = itemgetter(*fields)
            key = lambda k: grouper(k['properties'])
            for k, group in groupby(sorted(input, key=key), key):
                properties, geom = zip(*[(feature['properties'], shape(feature['geometry'])) for feature in group])
                output.write({'geometry': mapping(unary_union(geom)), 'properties': properties[0]})

def import_shapes(file_path):
    with fiona.open(file_path, 'r') as source:
        return [shape for shape in source]

#####################################
# CONVERT PROTECTIONS
#####################################

def convert_projection(data):

    project = partial(
        pyproj.transform,
        pyproj.Proj(init='epsg:4326'),
        pyproj.Proj(init='epsg:27700')
    )

    for feature in data:
        feature['geometry'] = mapping(transform(project, shape(feature['geometry'])))

    return data

# def convert_projection(data):

#     converted_data = []

#     projOSGB1936 = pyproj.Proj(init='epsg:27700')
#     projWGS84 = pyproj.Proj(init='epsg:4326')

#     for feature in data:

#         new_geom = []
#         coords = feature['geometry']['coordinates']

#         for coordList in coords:

#             try:
#                 coordList = list(pyproj.transform(projWGS84, projOSGB1936, coordList[0], coordList[1]))
#                 new_geom.append(coordList)

#             except:
#                 print("Warning: Some loss of postcode sectors during projection conversion")
                
#         feature['geometry']['coordinates'] = new_geom

#         converted_data.append(feature)
        
#     return converted_data

#####################################
# IMPORT SUPPLY SIDE DATA
#####################################

def import_unique_cell_data(data):

    os_unique_cell_data = []

    with open(data, 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            os_unique_cell_data.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [float(line[1]), float(line[0])]
                },
                'properties': {
                    'lte_ci': line[2],
                    'lte_pci': line[3],
                }
            })
    
    return os_unique_cell_data

def add_polygon_id_to_point(points, polygons):

    joined_data = []

    # Initialze Rtree
    idx = index.Index()

    for rtree_idx, point in enumerate(points):
        idx.insert(rtree_idx, shape(point['geometry']).bounds, point)

    # Join the two
    for polygon in polygons:
        for n in idx.intersection((shape(polygon['geometry']).bounds), objects=True):
            polygon_area_shape = shape(polygon['geometry'])
            polygon_shape = shape(n.object['geometry'])
            if polygon_area_shape.contains(polygon_shape):
                n.object['properties']['pcd_sector'] = polygon['properties']['pcd_sector']
                joined_data.append(n.object)
            else:
                n.object['properties']['pcd_sector'] = 'not in pcd_sector'
                joined_data.append(n.object)

    return joined_data

def sum_cells_by_pcd_sectors(data):
    
    #group premises by lads
    cells_per_pcd_sector = defaultdict(list)

    for datum in data:
        """
        'pcd_sector': [
            cell1,
            cell2
        ]
        """
        #print(postcode)
        cells_per_pcd_sector[datum['properties']['pcd_sector']].append(datum['properties']['lte_ci'])       

    # run statistics on each lad
    cells_results = defaultdict(dict)
    for cell in cells_per_pcd_sector.keys():

        sum_of_cells = len(cells_per_pcd_sector[cell]) # contain  list of premises objects in the lad

        if sum_of_cells > 0:
            cells_results[cell] = {
                'cells': sum_of_cells,
                'pcd_sector': cell
            }
        else:
            cells_results[cell] = {
                'cells': 0,
                'pcd_sector': cell
            }

    return cells_results

def calculate_area_of_pcd_sectors(data):
    
    my_pcd_sectors = defaultdict(list)

    for datum in data:
        geom = shape(datum['geometry'])

        # Transform polygon to projected equal area coordinates
        geom_area = transform(
            partial(
                pyproj.transform,
                pyproj.Proj(init='EPSG:27700'),
                pyproj.Proj(
                    proj='aea',
                    lat1=geom.bounds[1],
                    lat2=geom.bounds[3])),
                    geom
                )
        polygon_area = round(geom_area.area / 1000000, 2)

        if polygon_area > 0:
            my_pcd_sectors[datum['properties']['pcd_sector']] = {
                'area': polygon_area
            } 
        else:
            my_pcd_sectors[datum['properties']['pcd_sector']] = {
                'area': 'not available'
            }             

    return my_pcd_sectors

def covert_data_into_list_of_dicts(data, metric):
    my_data = []

    # output and report results for this timestep
    for datum in data:
        my_data.append({
        'pcd_sector': datum,
         metric: data[datum][metric],
        })

    return my_data


def deal_with_missing_values(data):

    my_data = []

    for datum in data:
        
        if 'area' in datum:
            my_data.append({
                'pcd_sector': datum['pcd_sector'],
                'cells': datum['cells'],
                'area': datum['area'],
            })

        else:
            my_data.append({
                'pcd_sector': datum['pcd_sector'],
                'cells': datum['cells'],
                'area': 'not available'
            })

    return my_data

def calculate_cell_densities(data):

    my_data = []

    for datum in data:

        if datum['area'] != 'not available':
            if datum['cells'] > 0.01:
                #print(datum)
                cell_density = round(float(datum['cells']) / float(datum['area']), 3)
                my_data.append({
                    'pcd_sector': datum['pcd_sector'],
                    'cells': datum['cells'],
                    'area': datum['area'],
                    'cell_density': cell_density
                    })
            else:
                my_data.append({
                    'pcd_sector': datum['pcd_sector'],
                    'cells': 0,
                    'area': datum['area'],
                    'cell_density': 'not available'
                    })     
        else:
            my_data.append({
                'pcd_sector': datum['pcd_sector'],
                'cells': datum['cells'],
                'area': datum['area'],
                'cell_density': 'not available'
                })

    return my_data

def read_in_os_open_roads(data):

    open_roads_network = []

    for my_file in os.listdir(data):
        if my_file.endswith("RoadLink.shp"):
            with fiona.open(os.path.join(data, my_file), 'r') as source:
                for src_shape in source:   
                    open_roads_network.extend([src_shape for src_shape in source if src_shape['properties']['function'] == 'Motorway' or src_shape['properties']['function'] == 'A Road' or src_shape['properties']['function'] == 'B Road' or src_shape['properties']['function'] == 'Minor Road' or src_shape['properties']['function'] == 'Local Road']) 
                    #open_roads_network.extend([src_shape for src_shape in source]) 
                    for element in open_roads_network:

                        if element['properties']['name1'] in element['properties']:
                            del element['properties']['name1']
                        else:
                            pass 

                        if element['properties']['name1_lang'] in element['properties']:
                            del element['properties']['name1_lang']
                        else:
                            pass 

                        if element['properties']['name2'] in element['properties']:
                            del element['properties']['name2']
                        else:
                            pass 

                        if element['properties']['name2_lang'] in element['properties']:
                            del element['properties']['name2_lang']
                        else:
                            pass 

                        if element['properties']['structure'] in element['properties']:
                            del element['properties']['structure']
                        else:
                            pass 

                        if element['properties']['nameTOID'] in element['properties']:
                            del element['properties']['nameTOID']
                        else:
                            pass 

                        if element['properties']['numberTOID'] in element['properties']:
                            del element['properties']['numberTOID']
                        else:
                            pass 

    return open_roads_network

def read_in_built_up_areas():

    built_up_area_polygon_data = []

    # with fiona.open(os.path.join(SYSTEM_INPUT_PATH, 'built_up_areas', 'built_up_areas_cambridgeshire.shp'), 'r') as source:
    #     for src_shape in source:           
    #         built_up_area_polygon_data.extend([src_shape for src_shape in source]) 

    with fiona.open(os.path.join(SYSTEM_INPUT_PATH, 'built_up_areas', 'Builtup_Areas_December_2011_Boundaries_V2_england_and_wales', 'urban_areas_england_and_wales_27700.shp'), 'r') as source:
        for src_shape in source:           
            built_up_area_polygon_data.extend([src_shape for src_shape in source]) 

    with fiona.open(os.path.join(SYSTEM_INPUT_PATH, 'built_up_areas', 'shapefiles-mid-2016-settlements-localities_scotland', 'urban_areas_27700.shp'), 'r') as source:
        for src_shape in source:           
            built_up_area_polygon_data.extend([src_shape for src_shape in source]) 

    return built_up_area_polygon_data


def add_urban_rural_indicator_to_roads(road_data, built_up_polygons): 

    joined_road_data = []

    # Initialze Rtree
    idx = index.Index()

    for rtree_idx, area in enumerate(built_up_polygons):
        idx.insert(rtree_idx, shape(area['geometry']).bounds, area)
    
    # Join the two
    for road in road_data:
        matches = [n for n in idx.intersection((shape(road['geometry']).bounds), objects=True)]
        if len(matches) > 0:
            road['properties']['urban_rural_indicator'] = 'urban'
        else:
            road['properties']['urban_rural_indicator'] = 'rural'

    return road_data


def deal_with_none_values(data):

    my_data = []

    for road in data:      
        if road['properties']['roadNumber'] == None:
            my_data.append({
                'type': "Feature",
                'geometry': {
                    "type": "LineString",
                    "coordinates": road['geometry']['coordinates']
                },
                'properties': {
                    'road': road['properties']['function'],
                    'formofway': road['properties']['formOfWay'],    
                    'length': int(road['properties']['length']),
                    'function': road['properties']['function'],   
                    'urban_rural_indicator': road['properties']['urban_rural_indicator']    
                }
            })
        else:
            my_data.append({
                'type': "Feature",
                'geometry': {
                    "type": "LineString",
                    "coordinates": road['geometry']['coordinates']
                },
                'properties': {
                    'road': road['properties']['function'],
                    'formofway': road['properties']['formOfWay'],    
                    'length': int(road['properties']['length']),
                    'function': road['properties']['function'],   
                    'urban_rural_indicator': road['properties']['urban_rural_indicator']    
                }
            })
        
    return my_data

def add_pcd_sector_indicator_to_roads(road_data, pcd_sector_polygons): 

    # Initialze Rtree
    idx = index.Index()

    for rtree_idx, area in enumerate(pcd_sector_polygons):
        idx.insert(rtree_idx, shape(area['geometry']).bounds, area)
    
    # Join the two
    for road in road_data:
        matches = [n for n in idx.intersection((shape(road['geometry']).bounds), objects=True)]
        if len(matches) > 0:
            road['properties']['pcd_sector'] = matches[0].object['properties']['pcd_sector']
        else:
            road['properties']['pcd_sector'] = 'undefined'

    return road_data

def write_road_network_shapefile(data, path):

    # Translate props to Fiona sink schema
    prop_schema = []
    for name, value in data[0]['properties'].items():
        fiona_prop_type = next((fiona_type for fiona_type, python_type in fiona.FIELD_TYPES_MAP.items() if python_type == type(value)), None)
        prop_schema.append((name, fiona_prop_type))

    sink_driver = 'ESRI Shapefile'
    sink_crs = {'init': 'epsg:27700'}
    sink_schema = {
        'geometry': data[0]['geometry']['type'],
        'properties': OrderedDict(prop_schema)
    }

    # Write all elements to output file
    with fiona.open(os.path.join(SYSTEM_OUTPUT_PATH, path), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        for feature in data:
            #print(feature)
            sink.write(feature)


def extract_geojson_properties(data):
    
    my_data = []

    for item in data:
        my_data.append({
            'road': item['properties']['road'],
            'formofway': item['properties']['formofway'], 
            'length': item['properties']['length'],
            'function': item['properties']['function'], 
            'urban_rural_indicator': item['properties']['urban_rura'],         
        })

    return my_data

def extract_geojson_properties_inc_pcd_sectors(data):
    
    my_data = []

    for item in data:
        my_data.append({
            'pcd_sector': item['properties']['pcd_sector'],
            'formofway': item['properties']['formofway'], 
            'length': item['properties']['length'],
            'function': item['properties']['function'], 
            'urban_rural_indicator': item['properties']['urban_rura'],         
        })

    return my_data

def grouper(data, aggregated_metric, group_item1, group_item2, group_item3, group_item4):

    my_grouper = itemgetter(group_item1, group_item2, group_item3, group_item4)
    result = []
    for key, grp in groupby(sorted(data, key = my_grouper), my_grouper):
        try:
            temp_dict = dict(zip([group_item1, group_item2, group_item3, group_item4], key))
            temp_dict[aggregated_metric] = sum(int(item[aggregated_metric]) for item in grp)
            result.append(temp_dict)
        except:
            pass
    
    return result


def aggregator(data, aggregated_metric, group_item1, group_item2, group_item3):

    my_grouper = itemgetter(group_item1, group_item2, group_item3)
    result = []
    for key, grp in groupby(sorted(data, key = my_grouper), my_grouper):
        try:
            temp_dict = dict(zip([group_item1, group_item2, group_item3], key))
            temp_dict[aggregated_metric] = sum(int(item[aggregated_metric]) for item in grp)
            result.append(temp_dict)
        except:
            pass
    
    return result


def merge_two_lists_of_dicts(msoa_list_of_dicts, oa_list_of_dicts, parameter1, parameter2):
    """
    Combine the msoa and oa dicts using the household indicator and year keys. 
    """
    d1 = {(d[parameter1], d[parameter2]):d for d in oa_list_of_dicts}

    msoa_list_of_dicts = [dict(d, **d1.get((d[parameter1], d[parameter2]), {})) for d in msoa_list_of_dicts]	

    return msoa_list_of_dicts

#####################################
# WRITE CSV DATA
#####################################

def csv_writer(data, output_fieldnames, filename):
    """
    Write data to a CSV file path
    """
    fieldnames = data[0].keys()
    with open(os.path.join(SYSTEM_OUTPUT_PATH, filename),'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)

#####################################
# RUN SCRIPTS
#####################################

# print("importing codepoint postcode data")
# #postcodes = import_postcodes(os.path.join(CODEPOINT_INPUT_PATH,'subset'))
# postcodes = import_postcodes(os.path.join(CODEPOINT_INPUT_PATH,'codepoint-poly_2429451'))

# print("adding pcd_sector indicator")
# postcodes = add_postcode_sector_indicator(postcodes)

# print("writing postcodes")
# write_shapefile(postcodes, os.path.join(CODEPOINT_OUTPUT_PATH, 'postcodes.shp'), 'epsg:27700')

# print("dissolving on pcd_sector indicator")
# dissolve('postcodes.shp', 'pcd_sectors.shp', ["pcd_sector"])

# print("reading in pcd_sector data")
# pcd_sectors = import_shapes(os.path.join(SYSTEM_OUTPUT_PATH, 'pcd_sectors.shp'))

# ####print("converting pcd_sector data to WSG84")
# ####pcd_sectors = convert_projection_pcd_sectors(pcd_sectors)

# print("writing postcode sectors")
# write_shapefile(pcd_sectors, os.path.join(SYSTEM_OUTPUT_PATH, 'pcd_sectors.shp'), 'epsg:27700')

# #####################################

# print("reading in pcd_sector data")
# pcd_sectors = import_shapes(os.path.join(SYSTEM_OUTPUT_PATH, 'pcd_sectors.shp'))

# print("reading in unique cell data")
# #unique_cells = import_unique_cell_data(os.path.join(SYSTEM_INPUT_PATH, 'received_signal_data', 'os_unique_cells_GB_27700.csv'))
# unique_cells = import_unique_cell_data(os.path.join(SYSTEM_INPUT_PATH, 'received_signal_data', 'os_unique_cells.csv'))

# print("converting data to GB grid 27700")
# unique_cells = convert_projection(unique_cells)

# print("adding pcd sector id to cells")
# unique_cells = add_polygon_id_to_point(unique_cells, pcd_sectors)

# print("writing unique_cells to shapefile")
# write_shapefile(unique_cells, os.path.join(SYSTEM_OUTPUT_PATH, 'unique_cells.shp'), 'epsg:27700')

# print("summing unique_cells by pcd_sector")
# summed_cells = sum_cells_by_pcd_sectors(unique_cells)

# print("coverting data to list of dict structure")
# summed_cells = covert_data_into_list_of_dicts(summed_cells, 'cells')

# print("calculate area of pcd_sectors")
# pcd_sector_area = calculate_area_of_pcd_sectors(pcd_sectors)

# print("coverting data to list of dict structure")
# pcd_sector_area = covert_data_into_list_of_dicts(pcd_sector_area, 'area')

# print("merge two list of dicts")
# pcd_sectors = merge_two_lists_of_dicts(summed_cells, pcd_sector_area, 'pcd_sector', 'pcd_sector')

# print("dealing with missing values")
# pcd_sectors = deal_with_missing_values(pcd_sectors)

# print("calculate cell densities")
# pcd_sectors = calculate_cell_densities (pcd_sectors)

# print('write pcd_sector data')
# summed_cells_fieldnames = ['pcd_sector', 'area', 'cells', 'cell_density']
# csv_writer(pcd_sectors, summed_cells_fieldnames, 'pcd_sector_cell_densities.csv')

#####################################

# # print("read in traffic flow data")
# # flow_data = read_in_traffic_counts()

# # print("calculating average count per road")
# # average_flow_data = find_average_count(flow_data)

# # print("converting to list of dicts structure")
# # average_flow_data = covert_data_into_list_of_dicts(average_flow_data, 'road', 'average_count', 'summed_count') 

# # print("categorising flow data")
# # # average_flow_data = apply_road_categories(average_flow_data)

#####################################

# print('read in road network')
# #road_network = read_in_os_open_roads((os.path.join(SYSTEM_INPUT_PATH, 'os_open_roads', 'open-roads_2438901_cambridge')))
# road_network = read_in_os_open_roads(os.path.join(SYSTEM_INPUT_PATH, 'os_open_roads', 'open-roads_2443825'))

# print('read in built up area polygons')
# built_up_areas = read_in_built_up_areas()

# print('add built up area indicator to urban roads')
# road_network = add_urban_rural_indicator_to_roads(road_network, built_up_areas)

# print('delaing with missing values')
# road_network = deal_with_none_values(road_network)

# print("writing road network")
# write_road_network_shapefile(road_network, 'road_network.shp')

#####################################

# print('read in road network')
# road_network = import_shapes(os.path.join(SYSTEM_OUTPUT_PATH, 'road_network.shp'))

# print("extracting geojson properties")
# aggegated_road_statistics = extract_geojson_properties(road_network)

# print("applying grouped aggregation")
# aggegated_road_statistics = grouper(aggegated_road_statistics, 'length', 'road', 'function', 'formofway', 'urban_rural_indicator')

# print('write all road statistics')
# road_statistics_fieldnames = ['road', 'function', 'formofway', 'length', 'urban_rural_indicator']
# csv_writer(aggegated_road_statistics, road_statistics_fieldnames, 'aggregated_road_statistics.csv')

# print("applying aggregation to road types")
# road_length_by_type = aggregator(aggegated_road_statistics, 'length', 'function', 'formofway', 'urban_rural_indicator')

# print('write road lengths')
# road_statistics_fieldnames = ['road', 'function', 'formofway', 'length', 'urban_rural_indicator']
# csv_writer(road_length_by_type, road_statistics_fieldnames, 'road_length_by_type.csv')

#####################################
# get road lengths by type, by pcd sector
#####################################

# print('read in road network')
# # road_network = read_in_os_open_roads((os.path.join(SYSTEM_INPUT_PATH, 'os_open_roads', 'open-roads_2438901_cambridge')))
# # road_network = read_in_os_open_roads(os.path.join(SYSTEM_INPUT_PATH, 'os_open_roads', 'open-roads_2443825'))
# road_network = import_shapes(os.path.join(SYSTEM_OUTPUT_PATH, 'road_network.shp'))

# print("reading in pcd_sector data")
# pcd_sectors = import_shapes(os.path.join(SYSTEM_OUTPUT_PATH, 'pcd_sectors.shp'))

# print('add pcd sector id to roads')
# road_network = add_pcd_sector_indicator_to_roads(road_network, pcd_sectors)

# print("writing road network")
# write_road_network_shapefile(road_network, 'road_network_with_pcd_sectors.shp')

# print("extracting geojson properties")
# road_stats_by_pcd_sector = extract_geojson_properties_inc_pcd_sectors(road_network)

# print("applying grouped aggregation")
# road_stats_by_pcd_sector = grouper(road_stats_by_pcd_sector, 'length', 'pcd_sector', 'function', 'formofway', 'urban_rural_indicator')

# print('write road lengths')
# road_statistics_fieldnames = ['pcd_sector', 'function', 'formofway', 'length', 'urban_rural_indicator']
# csv_writer(road_stats_by_pcd_sector, road_statistics_fieldnames, 'pcd_sector_road_length_by_type.csv')

end = time.time()
print("script finished")
print("script took {} minutes to complete".format(round((end - start)/60, 0))) 