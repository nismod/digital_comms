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
            print(line)
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

def process_asset_data(data):
    """Add buffer to each site, dissolve overlaps and take centroid.

    """
    buffered_assets = []

    for asset in data:
        asset_geom = shape(asset['geometry'])
        buffered_asset = asset_geom.buffer(50)
        final_geom = unary_union(buffered_asset)
        buffered_assets.append(final_geom)

    copy_of_assets = buffered_assets
    dissolved_assets = []

    for asset in buffered_assets:
        touching_assets = [
            other_asset for other_asset in copy_of_assets if asset.intersects(other_asset)
            ]
        dissolved_shape = cascaded_union(touching_assets)
        final_centroid = dissolved_shape.representative_point()
        dissolved_assets.append((final_centroid.coords[0][0], final_centroid.coords[0][1]))

    final_assets = list(set(dissolved_assets))

    output = []

    for asset in final_assets:
        output.append({
            'type': "Feature",
            'geometry': {
                "type": "Point",
                "coordinates": [asset[0], asset[1]],
            },
            'properties':{}
        })

    return output

def write_shapefile(data, filename):

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
    directory = os.path.join(BASE_PATH, 'intermediate', 'sitefinder')
    if not os.path.exists(directory):
        os.makedirs(directory)

    print(os.path.join(directory, filename))
    # Write all elements to output file
    with fiona.open(os.path.join(directory, filename),
        'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        [sink.write(feature) for feature in data]

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
            BASE_PATH,'raw','b_mobile_model','sitefinder','sitefinder_cambridgeshire'+'.csv'
            )
        )

    #process points using 50m buffer
    points = process_asset_data(asset_data)
    print(points)
    #write shapefile
    write_shapefile(points, 'sitefinder_processed.shp')

    #write csv
    csv_writer(points, 'sitefinder_processed.csv')
