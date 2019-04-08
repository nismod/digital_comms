import os
import configparser
import csv
from shapely.geometry import shape, Point, Polygon, mapping
from shapely.ops import unary_union, cascaded_union
import fiona
from collections import OrderedDict

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

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
            else:
                pass

    return asset_data

def find_average(my_property):

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
    """Add buffer to each site, dissolve overlaps and take centroid.

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
                'Antennaht': find_average('Antennaht'),
                'Transtype': [a['properties']['Transtype'] for a in touching_assets],
                'Freqband': [a['properties']['Freqband'] for a in touching_assets],
                'Anttype': [a['properties']['Anttype'] for a in touching_assets],
                'Powerdbw': find_average('Powerdbw'),
                'Maxpwrdbw': find_average('Maxpwrdbw'),
                'Maxpwrdbm': find_average('Maxpwrdbm'),
            }
        })

    return output

# def write_shapefile(data, filename):

#     # Translate props to Fiona sink schema
#     prop_schema = []

#     for name, value in data[0]['properties'].items():
#         fiona_prop_type = next((fiona_type for fiona_type, python_type in
#         fiona.FIELD_TYPES_MAP.items() if python_type == type(value)), None)
#         prop_schema.append((name, fiona_prop_type))

#     sink_driver = 'ESRI Shapefile'
#     sink_crs = {'init': 'epsg:27700'}
#     sink_schema = {
#         'geometry': data[0]['geometry']['type'],
#         'properties': OrderedDict(prop_schema)
#     }

#     # Create path
#     directory = os.path.join(BASE_PATH, 'intermediate', 'sitefinder')
#     if not os.path.exists(directory):
#         os.makedirs(directory)

#     print(os.path.join(directory, filename))
#     # Write all elements to output file
#     with fiona.open(os.path.join(directory, filename),
#         'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
#         for feature in data:
#             sink.write(feature)

def csv_writer(data, filename):
    """
    Write data to a CSV file path

    """
    #process_data
    data_for_writing = []
    for asset in data:
        data_for_writing.append({
            'longitude': asset['geometry']['coordinates'][0],
            'latitude': asset['geometry']['coordinates'][1],
            'Antennaht': asset['properties']['Antennaht'],
            'Transtype': asset['properties']['Transtype'],
            'Freqband': asset['properties']['Freqband'],
            'Anttype': asset['properties']['Anttype'],
            'Powerdbw':  asset['properties']['Powerdbw'],
            'Maxpwrdbw':  asset['properties']['Maxpwrdbw'],
            'Maxpwrdbm':  asset['properties']['Maxpwrdbm'],
        })

    #get fieldnames
    fieldnames = []
    for name, value in data_for_writing[0].items():
        fieldnames.append(name)

    #create path
    directory = os.path.join(BASE_PATH, 'intermediate', 'sitefinder')
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(os.path.join(directory, filename), 'w') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames, lineterminator = '\n')
        writer.writeheader()
        writer.writerows(data_for_writing)

if __name__ == "__main__":

    #import desired assets
    asset_data = import_sitefinder_data(
        os.path.join(
            BASE_PATH,'raw','b_mobile_model','sitefinder','sitefinder'+'.csv'
            )
        )

    #process points using 50m buffer
    points = process_asset_data(asset_data)#[:1000]

    # #write shapefile
    # write_shapefile(points, 'sitefinder_processed_test.shp')

    #write csv
    csv_writer(points, 'sitefinder_processed.csv')
