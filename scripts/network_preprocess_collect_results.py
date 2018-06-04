import os
import fiona
import configparser
from collections import OrderedDict, defaultdict
import glob

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'processed_cluster')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'processed')

def collect_results(name):

    results = []
    for root, dirs, files in os.walk(SYSTEM_INPUT_FIXED):
        for file in files:
            if file == name:
                results.append(os.path.join(root, file))

    geojson_results = []
    for result_file in results:
        with fiona.open(os.path.join(result_file), 'r') as source:
            [geojson_results.append(entry) for entry in source]

    return geojson_results

def write_shapefile(data, filename):

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

    # Create path
    directory = os.path.join(SYSTEM_OUTPUT_FILENAME)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Write all elements to output file
    with fiona.open(os.path.join(directory, filename), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        [sink.write(feature) for feature in data]

if __name__ == "__main__":

    links_layer3_cabinets = collect_results('links_layer3_cabinets.shp')
    write_shapefile(links_layer3_cabinets, 'links_layer3_cabinets.shp')

    links_layer4_distributions = collect_results('links_layer4_distributions.shp')
    write_shapefile(links_layer4_distributions, 'links_layer4_distributions.shp')

    links_layer5_premises = collect_results('links_layer5_premises.shp')
    write_shapefile(links_layer5_premises, 'links_layer5_premises.shp')

    assets_layer2_exchanges = collect_results('assets_layer2_exchanges.shp')
    write_shapefile(assets_layer2_exchanges, 'assets_layer2_exchanges.shp')

    assets_layer3_cabinets = collect_results('assets_layer3_cabinets.shp')
    write_shapefile(assets_layer3_cabinets, 'assets_layer3_cabinets.shp')

    assets_layer4_distributions = collect_results('assets_layer4_distributions.shp')
    write_shapefile(assets_layer4_distributions, 'assets_layer4_distributions.shp')

    assets_layer5_premises = collect_results('assets_layer5_premises.shp')
    write_shapefile(assets_layer5_premises, 'assets_layer5_premises.shp')