import fiona
import os
import configparser

from shapely.geometry import Point, LineString, mapping
from collections import OrderedDict

#####################
# generate dummy data
#####################

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

# Config
input_shapefiles_dir = os.path.join('tests', 'fixed_model', 'fixtures')

# Helper functions
def write_points_to_shp(filename, data, schema):
    sink_driver = 'ESRI Shapefile'
    sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

    with fiona.open(filename, 'w', driver=sink_driver, crs=sink_crs, schema=schema) as sink:
        for geom in data:
            if schema['geometry'] == 'Point':
                sink.write({
                    'geometry': mapping(geom[0]),
                    'properties': geom[1]
                })
            elif schema['geometry'] == 'LineString':
                sink.write({
                    'geometry': mapping(geom[0]),
                    'properties': geom[1]
                })

def write_links_to_shp(filename, data):
    sink_driver = 'ESRI Shapefile'
    sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

    setup_linestring_schema = {
        'geometry': 'LineString',
        'properties': OrderedDict([('From', 'str:254'), ('To', 'str:254')])
    }

    with fiona.open(filename, 'w', driver=sink_driver, crs=sink_crs, schema=setup_linestring_schema) as sink:
        for link in data:
            sink.write({
                'geometry': mapping(link[0]),
                'properties': link[1]
            })

# Create shapefiles
setup_assets_layer5_premises_schema = {
    'geometry': 'Point',
    'properties': OrderedDict(
        [
            ('id',          'str:80'),
            ('connection',  'str:80'),
            ('FTTP',        'int:9'),
            ('GFast',       'int:9'),
            ('FTTC',        'int:9'),
            ('DOCSIS3',     'int:9'),
            ('ADSL',        'int:9')
        ]
    )
}

setup_assets_layer5_premises = [
    (Point(0.123026918434941,52.2165504829092), OrderedDict([('id', 'premise_1'), ('connection', 'distribution_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.122976797821796,52.2165813794341), OrderedDict([('id', 'premise_2'), ('connection', 'distribution_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.122923221944425,52.2166095174221), OrderedDict([('id', 'premise_3'), ('connection', 'distribution_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.122883253086023,52.2166385519268), OrderedDict([('id', 'premise_4'), ('connection', 'distribution_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.122832132472878,52.2166686554264), OrderedDict([('id', 'premise_5'), ('connection', 'distribution_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.122783132472878,52.2166938279235), OrderedDict([('id', 'premise_6'), ('connection', 'distribution_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.122648614925457,52.2167712069892), OrderedDict([('id', 'premise_7'), ('connection', 'distribution_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.122588735538602,52.2168061034969), OrderedDict([('id', 'premise_8'), ('connection', 'distribution_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.122603467123959,52.2169040350416), OrderedDict([('id', 'premise_9'), ('connection', 'distribution_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.122659525453909,52.2169508625585), OrderedDict([('id', 'premise_10'), ('connection', 'distribution_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.122725373699167,52.2169952421224), OrderedDict([('id', 'premise_11'), ('connection', 'distribution_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.122791614925457,52.2170374836873), OrderedDict([('id', 'premise_12'), ('connection', 'distribution_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.122847400887520,52.2170765182346), OrderedDict([('id', 'premise_13'), ('connection', 'distribution_2'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.122910793868552,52.2171207598228), OrderedDict([('id', 'premise_14'), ('connection', 'distribution_2'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.122974490359068,52.2171656908543), OrderedDict([('id', 'premise_15'), ('connection', 'distribution_2'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.123037852198502,52.2172047944235), OrderedDict([('id', 'premise_16'), ('connection', 'distribution_2'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.123172361839434,52.2172035183565), OrderedDict([('id', 'premise_17'), ('connection', 'distribution_2'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.123253817103661,52.2171583112688), OrderedDict([('id', 'premise_18'), ('connection', 'distribution_2'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.123332089471548,52.2171133112305), OrderedDict([('id', 'premise_19'), ('connection', 'distribution_2'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.123406210084692,52.2170664492107), OrderedDict([('id', 'premise_20'), ('connection', 'distribution_2'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.123488937716805,52.2170213456584), OrderedDict([('id', 'premise_21'), ('connection', 'distribution_2'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.123563634207321,52.2169773456193), OrderedDict([('id', 'premise_22'), ('connection', 'distribution_2'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
]

setup_links_layer5_premises_schema = {
    'geometry': 'LineString',
    'properties': OrderedDict([('origin', 'str:80'), ('dest', 'str:80'), ('length', 'float'), ('technology', 'str:80')])
}

setup_links_layer5_premises = [
    (LineString([(0.123026918434941,52.2165504829092), (0.123057923407583,52.2167734762701)]), OrderedDict([('origin', 'premise_1'), ('dest', 'distribution_1'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.122976797821796,52.2165813794341), (0.123057923407583,52.2167734762701)]), OrderedDict([('origin', 'premise_2'), ('dest', 'distribution_1'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.122923221944425,52.2166095174221), (0.123057923407583,52.2167734762701)]), OrderedDict([('origin', 'premise_3'), ('dest', 'distribution_1'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.122883253086023,52.2166385519268), (0.123057923407583,52.2167734762701)]), OrderedDict([('origin', 'premise_4'), ('dest', 'distribution_1'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.122832132472878,52.2166686554264), (0.123057923407583,52.2167734762701)]), OrderedDict([('origin', 'premise_5'), ('dest', 'distribution_1'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.122783132472878,52.2166938279235), (0.123057923407583,52.2167734762701)]), OrderedDict([('origin', 'premise_6'), ('dest', 'distribution_1'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.122648614925457,52.2167712069892), (0.123057923407583,52.2167734762701)]), OrderedDict([('origin', 'premise_7'), ('dest', 'distribution_1'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.122588735538602,52.2168061034969), (0.123057923407583,52.2167734762701)]), OrderedDict([('origin', 'premise_8'), ('dest', 'distribution_1'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.122603467123959,52.2169040350416), (0.123057923407583,52.2167734762701)]), OrderedDict([('origin', 'premise_9'), ('dest', 'distribution_1'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.122659525453909,52.2169508625585), (0.123057923407583,52.2167734762701)]), OrderedDict([('origin', 'premise_10'), ('dest', 'distribution_1'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.122725373699167,52.2169952421224), (0.123057923407583,52.2167734762701)]), OrderedDict([('origin', 'premise_11'), ('dest', 'distribution_1'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.122791614925457,52.2170374836873), (0.123057923407583,52.2167734762701)]), OrderedDict([('origin', 'premise_12'), ('dest', 'distribution_1'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.122847400887520,52.2170765182346), (0.123057923407583,52.2167734762701)]), OrderedDict([('origin', 'premise_13'), ('dest', 'distribution_1'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.122910793868552,52.2171207598228), (0.123111503238198,52.2169771966793)]), OrderedDict([('origin', 'premise_14'), ('dest', 'distribution_2'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.122974490359068,52.2171656908543), (0.123111503238198,52.2169771966793)]), OrderedDict([('origin', 'premise_15'), ('dest', 'distribution_2'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.123037852198502,52.2172047944235), (0.123111503238198,52.2169771966793)]), OrderedDict([('origin', 'premise_16'), ('dest', 'distribution_2'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.123172361839434,52.2172035183565), (0.123111503238198,52.2169771966793)]), OrderedDict([('origin', 'premise_17'), ('dest', 'distribution_2'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.123253817103661,52.2171583112688), (0.123111503238198,52.2169771966793)]), OrderedDict([('origin', 'premise_18'), ('dest', 'distribution_2'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.123332089471548,52.2171133112305), (0.123111503238198,52.2169771966793)]), OrderedDict([('origin', 'premise_19'), ('dest', 'distribution_2'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.123406210084692,52.2170664492107), (0.123111503238198,52.2169771966793)]), OrderedDict([('origin', 'premise_20'), ('dest', 'distribution_2'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.123488937716805,52.2170213456584), (0.123111503238198,52.2169771966793)]), OrderedDict([('origin', 'premise_21'), ('dest', 'distribution_2'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.123563634207321,52.2169773456193), (0.123111503238198,52.2169771966793)]), OrderedDict([('origin', 'premise_22'), ('dest', 'distribution_2'), ('length', 10), ('technology', 'fiberglass')]))
]

setup_assets_layer4_distributions_schema = {
    'geometry': 'Point',
    'properties': OrderedDict(
        [
            ('id',          'str:80'),
            ('connection',  'str:80'),
            ('FTTP',        'int:9'),
            ('GFast',       'int:9'),
            ('FTTC',        'int:9'),
            ('DOCSIS3',     'int:9'),
            ('ADSL',        'int:9')
        ]
    )
}

setup_assets_layer4_distributions = [
    (Point(0.123057923407583,52.2167734762701), OrderedDict([('id', 'distribution_1'), ('connection', 'cabinet_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
    (Point(0.123111503238198,52.2169771966793), OrderedDict([('id', 'distribution_2'), ('connection', 'cabinet_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
]

setup_links_layer4_distributions_schema = {
    'geometry': 'LineString',
    'properties': OrderedDict([('origin', 'str:80'), ('dest', 'str:80'), ('length', 'float'), ('technology', 'str:80')])
}

setup_links_layer4_distributions = [
    (LineString([(0.123057923407583,52.2167734762701), (0.124044422641854, 52.2167657522552)]), OrderedDict([('origin', 'distribution_1'), ('dest', 'cabinet_1'), ('length', 10), ('technology', 'fiberglass')])),
    (LineString([(0.123111503238198,52.2169771966793), (0.124044422641854, 52.2167657522552)]), OrderedDict([('origin', 'distribution_2'), ('dest', 'cabinet_1'), ('length', 10), ('technology', 'fiberglass')])),
]

setup_assets_layer3_cabinets_schema = {
    'geometry': 'Point',
    'properties': OrderedDict(
        [
            ('id',          'str:80'),
            ('connection',  'str:80'),
            ('FTTP',        'int:9'),
            ('GFast',       'int:9'),
            ('FTTC',        'int:9'),
            ('DOCSIS3',     'int:9'),
            ('ADSL',        'int:9')
        ]
    )
}

setup_assets_layer3_cabinets = [
    (Point(0.124044422641854, 52.2167657522552), OrderedDict([('id', 'cabinet_1'), ('connection', 'cabinet_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
]

setup_links_layer3_cabinets_schema = {
    'geometry': 'LineString',
    'properties': OrderedDict([('origin', 'str:80'), ('dest', 'str:80'), ('length', 'float'), ('technology', 'str:80')])
}

setup_links_layer3_cabinets = [
    (LineString([(0.124044422641854, 52.2167657522552), (0.121507260074479, 52.2047310714094)]), OrderedDict([('origin', 'cabinet_1'), ('dest', 'exchange_1'), ('length', 10), ('technology', 'fiberglass')]))
]

setup_assets_layer2_exchanges_schema = {
    'geometry': 'Point',
    'properties': OrderedDict(
        [
            ('id',          'str:80'),
            ('connection',  'str:80'),
            ('FTTP',        'int:9'),
            ('GFast',       'int:9'),
            ('FTTC',        'int:9'),
            ('DOCSIS3',     'int:9'),
            ('ADSL',        'int:9')
        ]
    )
}

setup_assets_layer2_exchanges = [
    (Point(0.121507260074479, 52.2047310714094), OrderedDict([('id', 'exchange_1'), ('connection', 'cabinet_1'), ('FTTP', 1), ('GFast', 0), ('FTTC', 0), ('DOCSIS3', 1), ('ADSL', 0)])),
]

write_points_to_shp(os.path.join(input_shapefiles_dir, 'assets_layer5_premises.shp'), setup_assets_layer5_premises, setup_assets_layer5_premises_schema)
write_points_to_shp(os.path.join(input_shapefiles_dir, 'links_layer5_premises.shp'), setup_links_layer5_premises, setup_links_layer5_premises_schema)
write_points_to_shp(os.path.join(input_shapefiles_dir, 'assets_layer4_distributions.shp'), setup_assets_layer4_distributions, setup_assets_layer4_distributions_schema)
write_points_to_shp(os.path.join(input_shapefiles_dir, 'links_layer4_distributions.shp'), setup_links_layer4_distributions, setup_links_layer4_distributions_schema)
write_points_to_shp(os.path.join(input_shapefiles_dir, 'assets_layer3_cabinets.shp'), setup_assets_layer3_cabinets, setup_assets_layer3_cabinets_schema)
write_points_to_shp(os.path.join(input_shapefiles_dir, 'links_layer3_cabinets.shp'), setup_links_layer3_cabinets, setup_links_layer3_cabinets_schema)
write_points_to_shp(os.path.join(input_shapefiles_dir, 'assets_layer2_exchanges.shp'), setup_assets_layer2_exchanges, setup_assets_layer2_exchanges_schema)

print('Done... Files are generated')