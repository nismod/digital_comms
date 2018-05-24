import os
from pprint import pprint
import configparser
import csv
import fiona
import numpy as np
import random 

from shapely.geometry import shape, Point, LineString, Polygon, MultiPolygon, mapping
from shapely.ops import unary_union, cascaded_union
from pyproj import Proj, transform
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from scipy.spatial import Voronoi, voronoi_plot_2d
from rtree import index

from collections import OrderedDict, defaultdict


CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################################
# SETUP FILE LOCATIONS
#####################################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'raw')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'processed')
SYSTEM_INPUT_NETWORK = os.path.join(SYSTEM_INPUT_FIXED, 'network_hierarchy_data')

#####################################
# PART 1 GENERATE EXCHANGE BOUNDARIES
#####################################

def read_pcd_to_exchange_lut():
    """
    Produces all unique postcode-to-exchange combinations from available data, including:

    'January 2013 PCP to Postcode File Part One.csv'
    'January 2013 PCP to Postcode File Part Two.csv'
    'pcp.to.pcd.dec.11.one.csv'
    'pcp.to.pcd.dec.11.two.csv'
    'from_tomasso_valletti.csv'

    Data Schema
    ----------
    * exchange_id: 'string'
        Unique Exchange ID
    * postcode: 'string'
        Unique Postcode 

    Returns
    -------
    pcd_to_exchange_data: List of dicts
    """
    pcd_to_exchange_data = []

    with open(os.path.join(SYSTEM_INPUT_NETWORK, 'January 2013 PCP to Postcode File Part One.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(SYSTEM_INPUT_NETWORK, 'January 2013 PCP to Postcode File Part One.csv'), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(SYSTEM_INPUT_NETWORK, 'pcp.to.pcd.dec.11.one.csv'), 'r',  encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(SYSTEM_INPUT_NETWORK, 'pcp.to.pcd.dec.11.two.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    with open(os.path.join(SYSTEM_INPUT_NETWORK, 'from_tomasso_valletti.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcd_to_exchange_data.append({
                'exchange_id': line[0],
                'postcode': line[1].replace(" ", "")
            })

    ### find unique values in list of dicts
    return list({pcd['postcode']:pcd for pcd in pcd_to_exchange_data}.values())

def read_pcd_to_cabinet_lut():
    """
    Produces all postcode-to-cabinet-to-exchange combinations from available data, including:

        - January 2013 PCP to Postcode File Part One.csv
        - January 2013 PCP to Postcode File Part Two.csv
        - pcp.to.pcd.dec.11.one.csv'
        - pcp.to.pcd.dec.11.two.csv'

    Data Schema
    -----------
    * exchange_id: 'string'
        Unique Exchange ID
    * name: 'string'
        Unique Exchange Name    
    * cabinet_id: 'string'
        Unique Cabinet ID
    * exchange_only_flag: 'int' 
        Exchange only binary
    
    Returns
    -------
    pcp_data: Dict of dicts
    """

    pcp_data = {}

    with open(os.path.join(SYSTEM_INPUT_NETWORK, 'January 2013 PCP to Postcode File Part One.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcp_data[line[2].replace(" ", "")] = {
                'exchange_id': line[0],
                'name': line[1],
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
            }

    with open(os.path.join(SYSTEM_INPUT_NETWORK, 'January 2013 PCP to Postcode File Part Two.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        for skip in range(11):
            next(reader)
        for line in reader:
            pcp_data[line[2].replace(" ", "")] = {
                'exchange_id': line[0],
                'name': line[1],
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
                ###skip other unwanted variables
            }

    with open(os.path.join(SYSTEM_INPUT_NETWORK, 'pcp.to.pcd.dec.11.one.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcp_data[line[2].replace(" ", "")] = {
                'exchange_id': line[0],
                'name': line[1],
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
                ###skip other unwanted variables
            }

    with open(os.path.join(SYSTEM_INPUT_NETWORK, 'pcp.to.pcd.dec.11.two.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)
        for line in reader:
            pcp_data[line[2].replace(" ", "")] = {
                'exchange_id': line[0],
                'name': line[1],
                'cabinet_id': line[3],
                'exchange_only_flag': line[4]
                ###skip other unwanted variables
            }

    return pcp_data

def read_postcode_areas():
    
    """
    Reads all postcodes shapes, removing vertical postcodes, and merging with closest neighbour.

    Data Schema
    -----------
    * POSTCODE: 'string'
        Unique Postcode

    Returns
    -------
    postcode_areas = list of dicts
    """

    postcode_areas = []

    # Initialze Rtree
    idx = index.Index()

    CODEPOINT_INPUT = os.path.join(SYSTEM_INPUT_FIXED,'codepoint', 'codepoint-poly_2429451')

    for dirpath, subdirs, files in os.walk(CODEPOINT_INPUT):
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
                        postcode_areas.append(p)

    return postcode_areas

def read_exchanges():

    """
    Reads in exchanges from 'final_exchange_pcds.csv'. 

    Data Schema
    ----------
    * id: 'string'
        Unique Exchange ID
    * Name: 'string'
        Unique Exchange Name
    * pcd: 'string'
        Unique Postcode
    * Region: 'string'
        Region ID
    * County: 'string'
        County IS
    
    Returns
    -------
    exchanges: List of dicts
    """

    exchanges = []

    with open(os.path.join(SYSTEM_INPUT_FIXED, 'layer_2_exchanges', 'final_exchange_pcds.csv'), 'r') as system_file:
        reader = csv.reader(system_file)
        next(reader)
    
        for line in reader:
            exchanges.append({
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": [float(line[5]), float(line[6])]
                },
                'properties': {
                    'id': line[1],
                    'Name': line[2],
                    'pcd': line[0],
                    'Region': line[3],
                    'County': line[4]
                }
            })

    return exchanges

def add_exchange_id_to_postcode_areas(exchanges, postcode_areas, exchange_to_postcode):

    """
    Either uses known data or estimates which exchange each postcode is likely attached to.

    Arguments
    ---------

    * exchanges: 'list of dicts'
        List of Exchanges from read_exchanges()
    * postcode_areas: 'list of dicts'
        List of Postcode Areas from read_postcode_areas()
    * exchange_to_postcode: 'list of dicts'
        List of Postcode to Exchange data procudes from read_pcd_to_exchange_lut()
    
    Returns
    -------
    postcode_areas: 'list of dicts'    
    """
    idx_exchanges = index.Index()
    lut_exchanges = {}

    # Read the exchange points
    for idx, exchange in enumerate(exchanges):

        # Add to Rtree and lookup table
        idx_exchanges.insert(idx, tuple(map(int, exchange['geometry']['coordinates'])) + tuple(map(int, exchange['geometry']['coordinates'])), exchange['properties']['id'])
        lut_exchanges[exchange['properties']['id']] = {
            'Name': exchange['properties']['Name'],
            'pcd': exchange['properties']['pcd'].replace(" ", ""),
            'Region': exchange['properties']['Region'],
            'County': exchange['properties']['County'],
        }

    # Read the postcode-to-cabinet-to-exchange lookup file
    lut_pcb2cab = {}

    for idx, row in enumerate(exchange_to_postcode):
        lut_pcb2cab[row['postcode']] = row['exchange_id']

    # Connect each postcode area to an exchange
    for postcode_area in postcode_areas:

        postcode = postcode_area['properties']['POSTCODE']

        if postcode in lut_pcb2cab:

            # Postcode-to-cabinet-to-exchange association
            postcode_area['properties']['EX_ID'] = lut_pcb2cab[postcode]
            postcode_area['properties']['EX_SRC'] = 'EXISTING POSTCODE DATA'

        else:

            # Find nearest exchange
            nearest = [n.object for n in idx_exchanges.nearest((shape(postcode_area['geometry']).bounds), 1, objects=True)]
            postcode_area['properties']['EX_ID'] = nearest[0]
            postcode_area['properties']['EX_SRC'] = 'ESTIMATED NEAREST'

        # Match the exchange ID with remaining exchange info
        if postcode_area['properties']['EX_ID'] in lut_exchanges:
            postcode_area['properties']['EX_NAME'] = lut_exchanges[postcode_area['properties']['EX_ID']]['Name']
            postcode_area['properties']['EX_PCD'] = lut_exchanges[postcode_area['properties']['EX_ID']]['pcd']
            postcode_area['properties']['EX_REGION'] = lut_exchanges[postcode_area['properties']['EX_ID']]['Region']
            postcode_area['properties']['EX_COUNTY'] = lut_exchanges[postcode_area['properties']['EX_ID']]['County']
        else:
            postcode_area['properties']['EX_NAME'] = ""
            postcode_area['properties']['EX_PCD'] = ""
            postcode_area['properties']['EX_REGION'] = ""
            postcode_area['properties']['EX_COUNTY'] = ""

    return postcode_areas

def add_cabinet_id_to_postcode_areas(postcode_areas, pcd_to_cabinet):
    
    for postcode_area in postcode_areas:
        if postcode_area['properties']['POSTCODE'] in pcd_to_cabinet:
            postcode_area['properties']['CAB_ID'] = pcd_to_cabinet[postcode_area['properties']['POSTCODE']]['cabinet_id']
        else:
            postcode_area['properties']['CAB_ID'] = ""
    
    return postcode_areas

def generate_exchange_area(exchanges, merge=True):

    exchanges_by_group = {}

    # Loop through all exchanges
    for f in exchanges:

        # Convert Multipolygons to list of polygons
        if (isinstance(shape(f['geometry']), MultiPolygon)):
            polygons = [p.buffer(0) for p in shape(f['geometry'])]
        else:
            polygons = [shape(f['geometry'])]

        # Extend list of geometries, create key (exchange_id) if non existing
        try:
            exchanges_by_group[f['properties']['EX_ID']].extend(polygons)
        except:
            exchanges_by_group[f['properties']['EX_ID']] = []
            exchanges_by_group[f['properties']['EX_ID']].extend(polygons)

    # Write Multipolygons per exchange
    exchange_areas = []
    for exchange, area in exchanges_by_group.items():

        exchange_multipolygon = MultiPolygon(area)
        exchange_areas.append({
            'type': "Feature",
            'geometry': mapping(exchange_multipolygon),
            'properties': {
                'id': exchange
            }
        })

    if merge:
        # Merge MultiPolygons into single Polygon
        removed_islands = []
        for area in exchange_areas:

            # Avoid intersections
            geom = shape(area['geometry']).buffer(0)
            cascaded_geom = unary_union(geom)

            # Remove islands
            # Add removed islands to a list so that they
            # can be merged in later
            if (isinstance(cascaded_geom, MultiPolygon)):
                for idx, p in enumerate(cascaded_geom):
                    if idx == 0:
                        geom = p
                    elif p.area > geom.area:
                        removed_islands.append(geom)
                        geom = p
                    else:
                        removed_islands.append(p)
            else:
                geom = cascaded_geom

            # Write exterior to file as polygon
            exterior = Polygon(list(geom.exterior.coords))

            # Write to output
            area['geometry'] = mapping(exterior)
        
        # Add islands that were removed because they were not 
        # connected to the main polygon and were not recovered
        # because they were on the edge of the map or inbetween
        # exchanges :-). Merge to largest intersecting exchange area.
        idx_exchange_areas = index.Index()
        for idx, exchange_area in enumerate(exchange_areas):
            idx_exchange_areas.insert(idx, shape(exchange_area['geometry']).bounds, exchange_area)
        for island in removed_islands:
            intersections = [n for n in idx_exchange_areas.intersection((island.bounds), objects=True)]

            if len(intersections) > 0:
                for idx, intersection in enumerate(intersections):
                    if idx == 0:
                        merge_with = intersection
                    elif shape(intersection.object['geometry']).intersection(island).length > shape(merge_with.object['geometry']).intersection(island).length:
                        merge_with = intersection

                merged_geom = merge_with.object
                merged_geom['geometry'] = mapping(shape(merged_geom['geometry']).union(island))
                idx_exchange_areas.delete(merge_with.id, shape(merge_with.object['geometry']).bounds)
                idx_exchange_areas.insert(merge_with.id, shape(merged_geom['geometry']).bounds, merged_geom)

        exchange_areas = [n.object for n in idx_exchange_areas.intersection(idx_exchange_areas.bounds, objects=True)]

    return exchange_areas

############################################
# PART 2 PROCESS TO SUM PREMISES BY EXCHANGE
############################################

def read_exchange_boundaries():
    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'exchange_boundaries.shp'), 'r') as source:
        return [boundary for boundary in source]

def get_postcode_centroids():

    postcode_shapes = []
    
    for dirpath, subdirs, files in os.walk(os.path.join(SYSTEM_INPUT_FIXED, 'codepoint', 'codepoint-poly_2429451')):
        for x in files:
            #print(files)
            if x.endswith(".shp"):
                with fiona.open(os.path.join(dirpath, x), 'r') as source:
                    postcode_shapes.extend([boundary for boundary in source])

    for postcode in postcode_shapes:
            centroid = shape(postcode['geometry']).centroid
            postcode['geometry'] = mapping(centroid)

    return postcode_shapes


def read_codepoint_lut():

    codepoint_lut_data = []

    SYSTEM_INPUT_NETWORK = os.path.join(SYSTEM_INPUT_FIXED,'codepoint', 'codepoint_2429650', 'all_codepoint')

    for filename in os.listdir(SYSTEM_INPUT_NETWORK):
        #print(filename)
        if filename.endswith(".csv"):
            with open(os.path.join(SYSTEM_INPUT_NETWORK, filename), 'r', encoding='utf8', errors='replace') as system_file:
                reader = csv.reader(system_file) #csv.reader((line.replace('\0','') for line in system_file))
                next(reader)    
                for line in reader:
                    if line[-1] == 'S':
                        codepoint_lut_data.append({
                            'POSTCODE': line[0],          #.replace(' ', ''),
                            'delivery_points': int(line[3]),
                            #'type': line[18],
                        })
                    else:
                        pass

    return codepoint_lut_data   

def add_codepoint_lut_to_postcode_shapes(data, lut):

    # Process lookup into dictionary
    codepoint_lut_data = {}
    for area in lut:
        codepoint_lut_data[area['POSTCODE']] = area
        del codepoint_lut_data[area['POSTCODE']]['POSTCODE']

    # Add properties
    for datum in data:        
        if datum['properties']['POSTCODE'] in codepoint_lut_data:
            datum['properties'].update({
                'delivery_points': codepoint_lut_data[datum['properties']['POSTCODE']]['delivery_points']
            })
        else:
            datum['properties'].update({
                'delivery_points': 0, 
            })
    
    return data

def add_exchange_to_postcodes(postcodes, exchanges):
    
    joined_postcodes = []

    # Initialze Rtree
    idx = index.Index()

    for rtree_idx, postcode in enumerate(postcodes):
        idx.insert(rtree_idx, shape(postcode['geometry']).bounds, postcode)

    # Join the two
    for exchange in exchanges:
        for n in idx.intersection((shape(exchange['geometry']).bounds), objects=True):
            exchange_shape = shape(exchange['geometry'])
            postcode_shape = shape(n.object['geometry'])
            if exchange_shape.contains(postcode_shape):
                n.object['properties']['id'] = exchange['properties']['id']
                joined_postcodes.append(n.object)

    return joined_postcodes

def sum_premises_by_exchange():
    
    #group premises by lads
    premises_per_exchange = defaultdict(list)

    for postcode in postcode_centroids:
        """
        'exchange1': [
            postcode1,
            postcode2
        ]
        """
        #print(postcode)
        premises_per_exchange[postcode['properties']['id']].append(postcode['properties']['delivery_points'])

    # run statistics on each lad
    premises_results = defaultdict(dict)
    for exchange in premises_per_exchange.keys():

        #print(lad)
        sum_of_delivery_points = sum([premise for premise in premises_per_exchange[exchange]]) # contain  list of premises objects in the lad

        if sum_of_delivery_points >= 20000:
            geotype = '>20k lines'

        elif sum_of_delivery_points >= 10000 and sum_of_delivery_points < 20000:
            geotype = '>10k lines'            

        elif sum_of_delivery_points >= 3000 and sum_of_delivery_points <= 10000:
            geotype = '>3k lines'     

        elif sum_of_delivery_points >= 1000 and sum_of_delivery_points <= 30000:
            geotype = '>1k lines' 

        elif sum_of_delivery_points < 1000:
            geotype = '<1k lines' 

        premises_results[exchange] = {
            'delivery_points': sum_of_delivery_points,
            'geotype': geotype
        }

    return premises_results

############################################
# PART 3 ALLOCATE EXCHANGE GEOTYPES 
############################################

def read_lads():
    with fiona.open(os.path.join(SYSTEM_INPUT_FIXED, 'lad_uk_2016-12', 'lad_uk_2016-12.shp'), 'r') as source:
        return [lad for lad in source]

def read_city_exchange_geotype_lut():

    exchange_geotypes = []
    with open(os.path.join(SYSTEM_INPUT_FIXED, 'exchange_geotype_lut', 'exchange_geotype_lut.csv'), 'r', encoding='utf8', errors='replace') as system_file:
        reader = csv.reader(system_file)
        next(reader)    
        for line in reader:
            exchange_geotypes.append({
                'lad': line[0],
                'geotype': line[1],                
            })

    return exchange_geotypes

def add_lad_to_exchange(postcodes, exchanges):
    
    joined_postcodes = []

    # Initialze Rtree
    idx = index.Index()

    for rtree_idx, postcode in enumerate(postcodes):
        idx.insert(rtree_idx, shape(postcode['geometry']).bounds, postcode)

    # Join the two
    for exchange in exchanges:
        for n in idx.intersection((shape(exchange['geometry']).bounds), objects=True):
            exchange_shape = shape(exchange['geometry'])
            postcode_shape = shape(n.object['geometry'])
            if exchange_shape.contains(postcode_shape):
                n.object['properties']['id'] = exchange['properties']['id']
                joined_postcodes.append(n.object)

    return joined_postcodes

def add_lad_to_exchanges(exchanges, lads):
    
    joined_exchanges = []

    # Initialze Rtree
    idx = index.Index()

    for rtree_idx, exchange in enumerate(exchanges):
        idx.insert(rtree_idx, shape(exchange['geometry']).bounds, exchange)

    # Join the two
    for lad in lads:
        for n in idx.intersection((shape(lad['geometry']).bounds), objects=True):
            lad_shape = shape(lad['geometry'])
            premise_shape = shape(n.object['geometry'])
            if lad_shape.contains(premise_shape):
                n.object['properties']['lad'] = lad['properties']['name']
                joined_exchanges.append(n.object)

    return joined_exchanges

def covert_data_into_list_of_dicts(data):
    my_data = []

    # output and report results for this timestep
    for exchange in data:
        my_data.append({
        'exchange_id': exchange,
        'delivery_points': data[exchange]['delivery_points'],
        'geotype': data[exchange]['geotype']
        })

    return my_data

def merge_exchanges_with_summed_prems(exchanges, summed_premises):

    # Process lookup into dictionary
    exchange_geotypes = {}
    for each_exchange in summed_premises:
        exchange_geotypes[each_exchange['exchange_id']] = each_exchange
        del exchange_geotypes[each_exchange['exchange_id']]['exchange_id']

    # Add properties
    for exchange in exchanges:
        if exchange['properties']['id'] in exchange_geotypes:
            #print(exchange)
            exchange['properties'].update({
                'geotype': exchange_geotypes[exchange['properties']['id']]['geotype'],
                'delivery_points': exchange_geotypes[exchange['properties']['id']]['delivery_points']
            })
        else:
            exchange['properties'].update({
                # 'geotype': 'other', 
                'delivery_points': 0,
            })
    
    return exchanges

def add_urban_geotype_to_exchanges(exchanges, exchange_geotype_lut):

    # Process lookup into dictionary
    exchange_geotypes = {}
    for lad in exchange_geotype_lut:
        exchange_geotypes[lad['lad']] = lad
        del exchange_geotypes[lad['lad']]['lad']

    # Add properties
    for exchange in exchanges:
        
        if 'geotype' not in exchange['properties']:
            exchange['properties'].update({
                'geotype': 'unknown',
            })
        
        if exchange['properties']['lad'] in exchange_geotypes:
            exchange['properties'].update({
                'geotype': exchange_geotypes[exchange['properties']['lad']]['geotype'],

            })
        else:
            pass

    return exchanges

def covert_geojson_exchanges_into_list_of_dicts(data):
    my_data = []

    for exchange in data:
        my_data.append({
        'exchange_id': exchange['properties']['id'],
        'lad': exchange['properties']['lad'],
        'delivery_points': exchange['properties']['delivery_points'],
        'geotype': exchange['properties']['geotype']
        })

    return my_data
    
#####################################
# WRITE DATA 
#####################################

def csv_writer(data, output_fieldnames, filename):
    """
    Write data to a CSV file path
    """
    with open(os.path.join(SYSTEM_OUTPUT_FILENAME, filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, output_fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data)

def write_shapefile(data, path):

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
    with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, path), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        for feature in data:
            sink.write(feature)

################################################
# RUN SCRIPTS
################################################

#### GENERATE EXCHANGE BOUNDARIES
print('read_pcd_to_exchange_lut')
lut_pcd_to_exchange = read_pcd_to_exchange_lut()

print('read pcd_to_cabinet_lut')
lut_pcd_to_cabinet = read_pcd_to_cabinet_lut()

print('read postcode_areas')
geojson_postcode_areas = read_postcode_areas()

print('read exchanges')
geojson_layer2_exchanges = read_exchanges()

print('add exchange id to postcode areas')
geojson_postcode_areas = add_exchange_id_to_postcode_areas(geojson_layer2_exchanges, geojson_postcode_areas, lut_pcd_to_exchange)

print('add cabinet id to postcode areas')
geojson_postcode_areas = add_cabinet_id_to_postcode_areas(geojson_postcode_areas, lut_pcd_to_cabinet)

print('generate exchange areas')
exchange_boundaries = generate_exchange_area(geojson_postcode_areas)

print('write exchange_boundaries')
write_shapefile(exchange_boundaries, 'exchange_boundaries.shp')

#### PART 2 PROCESS TO SUM PREMISES BY EXCHANGES
print('reading exchange boundaries')
exchange_boundaries = read_exchange_boundaries()

print("reading postcode boundaries")
postcode_centroids = get_postcode_centroids()
 
print("reading codepoint lut")
codepoint_lut = read_codepoint_lut()

print("adding codepoint lut to postcode shapes")
postcode_centroids = add_codepoint_lut_to_postcode_shapes(postcode_centroids, codepoint_lut)

print("adding intersecting exchange IDs to postcode points")
postcode_centroids = add_exchange_to_postcodes(postcode_centroids, exchange_boundaries)

print("summing delivery points by exchange area")
premises_by_exchange = sum_premises_by_exchange()

#### PART 3 ALLOCATE EXCHANGE GEOTYPES 
print('read lads')
geojson_lad_areas = read_lads()

print('read city exchange geotypes lut')
city_exchange_lad_lut = read_city_exchange_geotype_lut()

print('add LAD to exchanges')
geojson_layer2_exchanges = add_lad_to_exchanges(geojson_layer2_exchanges, geojson_lad_areas)

print("convert exchange areas to list of dicts")
premises_by_exchange = covert_data_into_list_of_dicts(premises_by_exchange)

print("merge geojason exchanges with premises summed by exchange")
geojson_layer2_exchanges = merge_exchanges_with_summed_prems(geojson_layer2_exchanges, premises_by_exchange)

print('merge geotype info by LAD to exchanges')
geojson_layer2_exchanges = add_urban_geotype_to_exchanges(geojson_layer2_exchanges, city_exchange_lad_lut)

print("convert exchange areas to list of dicts")
layer2_exchanges = covert_geojson_exchanges_into_list_of_dicts(geojson_layer2_exchanges)

#### WRITE DATA 
print('write geotype lut')
geotype_lut_fieldnames = ['exchange_id', 'lad', 'delivery_points', 'geotype']
csv_writer(layer2_exchanges, geotype_lut_fieldnames, 'exchange_geotype_lut.csv')

print('write postcode_centroids')
write_shapefile(postcode_centroids, 'postcode_centroids.shp')

print("script finished")