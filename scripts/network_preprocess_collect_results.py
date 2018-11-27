import os
import sys
import fiona
import configparser
from collections import OrderedDict, defaultdict
import glob
import csv

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

DATA_RAW = os.path.join(BASE_PATH, 'raw', 'a_fixed_model')
DATA_INTERMEDIATE = os.path.join(BASE_PATH, 'intermediate')
DATA_PROCESSED = os.path.join(BASE_PATH, 'processed')

def collect_results(selection, name):

    results = []
    for entry in selection:
        results.append(os.path.join(DATA_INTERMEDIATE, entry, name))

    geojson_results = []
    for result_file in results:
        try:
            with fiona.open(os.path.join(result_file), 'r') as source:
                [geojson_results.append(entry) for entry in source]
        except:
            print('Error: Cannot open results for ' + result_file)

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
    directory = os.path.join(DATA_PROCESSED)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Write all elements to output file
    with fiona.open(os.path.join(directory, filename), 'w', driver=sink_driver, crs=sink_crs, schema=sink_schema) as sink:
        [sink.write(feature) for feature in data]

def get_exchange_ids(key, value):

    exchange_data = []

    with open(os.path.join(DATA_RAW, 'layer_2_exchanges', 'final_exchange_pcds.csv'), 'r') as my_file:
        reader = csv.reader(my_file)
        next(reader, None)
        for row in reader:
            exchange_data.append({
                'id': row[1],
                'region': row[3],
                'county': row[4],
                'country': row[7]
            })
    exchange_ids = []

    for exchange in exchange_data:
        if exchange[key] == value:
            single_id = 'exchange_{}'.format(exchange['id'])
            exchange_ids.append(single_id)

    return exchange_ids

def cut_out_unwanted_premises_data(data):

    premises_data = []

    for premises in data:
        premises_data.append(
            {
                'type': "Feature",
                'geometry': {
                    "type": "Point",
                    "coordinates": premises['geometry']['coordinates'],
                },
                'properties': {
                    'id': premises['properties']['id'], 
                    'connection': premises['properties']['connection'],
                    'FTTP': premises['properties']['FTTP'],
                    'GFast': premises['properties']['GFast'],
                    'FTTC': premises['properties']['FTTC'],
                    'DOCSIS3': premises['properties']['DOCSIS3'],
                    'ADSL':  premises['properties']['ADSL'],
                    'wtp': premises['properties']['wtp'],
                    'wta': premises['properties']['wta'],
                    'lad': premises['properties']['lad']
                }
            })

    return premises_data

if __name__ == "__main__":
    selection = []

    if len(sys.argv) < 2:
        selection = [item for item in os.listdir(DATA_INTERMEDIATE) if os.path.isdir(os.path.join(DATA_INTERMEDIATE, item))]
    elif sys.argv[1] == 'exchange_EACAM':
        selection = ['exchange_EACAM']
    elif sys.argv[1] == 'cambridge':
        selection = [
            'exchange_EAARR',
            'exchange_EABTM',
            'exchange_EABWL',
            'exchange_EACAM',
            'exchange_EACFH',
            'exchange_EACOM',
            'exchange_EACRH',
            'exchange_EACTM',
            'exchange_EAESW',
            'exchange_EAFUL',
            'exchange_EAGIR',
            'exchange_EAHIS',
            'exchange_EAHST',
            'exchange_EALNT',
            'exchange_EAMAD',
            'exchange_EAMBN',
            'exchange_EASCI',
            'exchange_EASIX',
            'exchange_EASST',
            'exchange_EASWV',
            'exchange_EATEV',
            'exchange_EATRU',
            'exchange_EAWLM',
            'exchange_EAWTB'
        ]

    elif sys.argv[1] == 'oxford':
        selection = [
            'exchange_SMSLK',
            'exchange_SMSNF',
            'exchange_SMFRD',
            'exchange_SMEY',
            'exchange_SMWC',
            'exchange_SMTAK',
            'exchange_SMCNR',
            'exchange_SMKI',
            'exchange_SMBZ',
            'exchange_SMCO',
            'exchange_SMOF',
            'exchange_SMAI',
            'exchange_SMWHY',
            'exchange_SMLW',
            'exchange_SMFH',
            'exchange_SMMCM',
            'exchange_SMSNC',
            'exchange_SMHD',
            'exchange_SMWLY',
            'exchange_SMICK',
            'exchange_SMSM',
            'exchange_SMSTJ',
            'exchange_SMBRL',
            'exchange_SMCHO',
            'exchange_SMBTN',
            'exchange_SMMSY',
            'exchange_SMBI',
            'exchange_SMWRB',
            'exchange_SMCTN',
            'exchange_SMSDM',
            'exchange_SMNHM',
            'exchange_SMGMT',
            'exchange_SMGN',
        ]

    elif sys.argv[1] == 'leeds':
        selection = [
            'exchange_MYTAD',
            'exchange_MYBOS',
            'exchange_MYDHS',
            'exchange_MYWEN',
            'exchange_MYLS',
            'exchange_MYLOF',
            'exchange_MYPON',
            'exchange_MYCHA',
            'exchange_MYSEA',
            'exchange_MYMOO',
            'exchange_MYHRW',
            'exchange_MYSPO',
            'exchange_MYOAT',
            'exchange_MYWEH',
            'exchange_MYWEH',
            'exchange_MYKKB',
            'exchange_MYSLA',
            'exchange_MYHON',
            'exchange_MYBRE',
            'exchange_MYFLO',
            'exchange_MYMIL',
            'exchange_MYHUD',
            'exchange_MYMIR',
            'exchange_MYELL',
            'exchange_MYHEC',
            'exchange_MYBRG',
            'exchange_MYSOW',
            'exchange_MYCLE',
            'exchange_MYHOB',
            'exchange_MYHAL',
            'exchange_MYBAT',
            'exchange_MYMOR',
            'exchange_MYHIP',
            'exchange_MYACO',
            'exchange_MYLOW',
            'exchange_MYILL',
            'exchange_MYTOC',
            'exchange_MYDUD',
            'exchange_MYDLT',
            'exchange_MYQUE',
            'exchange_MYRUF',
            'exchange_MYBD',
            'exchange_MYARM',
            'exchange_MYARM',
            'exchange_MYHBK',
            'exchange_MYTHT',
            'exchange_MYDEW',
            'exchange_SLADK',
            'exchange_MYSEM',
            'exchange_SLDR',
            'exchange_SLRY',
            'exchange_MYHMW',
            'exchange_SLASK',
            'exchange_MYWAK',
            'exchange_MYPUD',
            'exchange_MYSAN',
            'exchange_MYLAI',
            'exchange_MYMAN',
            'exchange_MYCUL',
            'exchange_MYNMN',
            'exchange_MYWBG',
            'exchange_MYCRF',
            'exchange_MYUND',
            'exchange_MYKNO',
            'exchange_MYHEA',
            'exchange_MYCAS',
            'exchange_MYBIN',
            'exchange_MYROT',
            'exchange_MYHSF',
            'exchange_MYSHI',
            'exchange_MYGAT',
            'exchange_MYIDL',
            'exchange_MYHLT',
            'exchange_MYRWD',
            'exchange_MYHLT',
            'exchange_MYADE',
            'exchange_MYGRF',
            'exchange_MYKEI',
            'exchange_MYSML',
            'exchange_MYGUI',
            'exchange_MYHHL',
            'exchange_MYART',
            'exchange_MYCSG',
            'exchange_MYART',
            'exchange_MYSEL',
            'exchange_MYBKA',
            'exchange_MYCAW',
            'exchange_MYSTE',
            'exchange_MYBKE',
            'exchange_MYBRW',
            'exchange_MYOTL',
            'exchange_MYTHR',
            'exchange_MYILK',
            'exchange_MYAPP',
            'exchange_MYHUB',
            'exchange_MYCOL',
            'exchange_MYADD',
        ]

    elif sys.argv[1] == 'newcastle':
        selection = [
            'exchange_NENTE',
            'exchange_NENT',
            'exchange_NEW',
            'exchange_NESS',
            'exchange_NEDB',
            'exchange_NEL',
            'exchange_NEJ',
            'exchange_NEGF',
            'exchange_NENS',
            'exchange_NEK',
            'exchange_NEB',
            'exchange_NEP',
            'exchange_NEWHP',
            'exchange_NEKI',
            'exchange_NEWB',
            'exchange_NEDUDL',
            'exchange_NESVL',
            'exchange_NEFN',
            'exchange_NESTN',
            'exchange_NEBEA',
            'exchange_NEEHN',
            'exchange_NEDP',
            'exchange_NEBR',
            'exchange_NEWAS',
            'exchange_NEHYL',
            'exchange_NESU',
            'exchange_NEBUR',
            'exchange_NERG',
            'exchange_NELF',
            'exchange_NEWK',
            'exchange_NESUN',
            'exchange_NECM',
            'exchange_NEBO',
            'exchange_NESGT',
            'exchange_NEF',
            'exchange_NEWN',
            'exchange_NED',
            'exchange_NED',
            'exchange_NEBL',
            'exchange_NEJW',
            'exchange_NERT',
            'exchange_NERT',
            'exchange_NEGHD',
            'exchange_NEWYL',
            'exchange_NEWYL',
            'exchange_NENTW',
        ]
    elif sys.argv[1] == 'Cambridgeshire':
        selection = get_exchange_ids('county', 'Cambridgeshire')

    elif sys.argv[1] == 'London':
        selection = get_exchange_ids('region', 'London')

    elif sys.argv[1] == 'East':
        selection = get_exchange_ids('region', 'East')

    elif sys.argv[1] == 'Wales':
        selection = get_exchange_ids('country', 'Wales')

    elif sys.argv[1] == 'England':
        selection = get_exchange_ids('country', 'England')

    links_layer3_cabinets = collect_results(selection, 'links_sl_layer3_cabinets.shp')
    write_shapefile(links_layer3_cabinets, 'links_layer3_cabinets.shp')

    links_layer4_distributions = collect_results(selection, 'links_sl_layer4_distributions.shp')
    write_shapefile(links_layer4_distributions, 'links_layer4_distributions.shp')

    links_layer5_premises = collect_results(selection, 'links_sl_layer5_premises.shp')
    write_shapefile(links_layer5_premises, 'links_layer5_premises.shp')

    assets_layer2_exchanges = collect_results(selection, 'assets_layer2_exchanges.shp')
    write_shapefile(assets_layer2_exchanges, 'assets_layer2_exchanges.shp')

    assets_layer3_cabinets = collect_results(selection, 'assets_layer3_cabinets.shp')
    write_shapefile(assets_layer3_cabinets, 'assets_layer3_cabinets.shp')

    assets_layer4_distributions = collect_results(selection, 'assets_layer4_distributions.shp')
    write_shapefile(assets_layer4_distributions, 'assets_layer4_distributions.shp')

    assets_layer5_premises = collect_results(selection, 'assets_layer5_premises.shp')
    assets_layer5_premises = cut_out_unwanted_premises_data(assets_layer5_premises)
    write_shapefile(assets_layer5_premises, 'assets_layer5_premises.shp')
