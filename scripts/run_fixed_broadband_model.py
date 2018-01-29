from digital_comms.fixed_model.network_structure import ICTManager
import fiona
import os

from shapely.geometry import Point, LineString, mapping
import matplotlib.pyplot as plt

from networkx import drawing
from networkx import nx

from collections import OrderedDict

# from mpl_toolkits.basemap import Basemap as Basemap

# Config
input_shapefiles_dir = 'input_shapefiles'
output_shapefiles_dir = 'output_shapefiles'

# Helper functions
def write_points_to_shp(filename, data):
    sink_driver = 'ESRI Shapefile'
    sink_crs = {'no_defs': True, 'ellps': 'WGS84', 'datum': 'WGS84', 'proj': 'longlat'}

    setup_point_schema = {
        'geometry': 'Point',
        'properties': OrderedDict([('Name', 'str:254')])
    }
    
    with fiona.open(filename, 'w', driver=sink_driver, crs=sink_crs, schema=setup_point_schema) as sink:
        for node in data:
            sink.write({
                'geometry': mapping(node[1]),
                'properties': OrderedDict([('Name', node[0])])
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
                'geometry': mapping(link[2]),
                'properties': OrderedDict([('From', link[0]), ('To', link[1])])
            })

# Create shapefiles
setup_fixed_model_pcp = [
    ('cab_1', Point(-1.944580, 52.792175)),
    ('cab_2', Point(-0.395508, 52.485498)),
    ('cab_3', Point(-2.713623, 52.652437)),
    ('cab_4', Point( 0.417480, 51.147694)),
    ('cab_5', Point( 1.219482, 52.431944)),
    ('cab_6', Point(-1.900635, 51.223443)),
    ('cab_7', Point( 0.802002, 51.154586))
]

setup_fixed_model_exchanges = [
    ('EAARR', Point(-0.582275, 51.804581)),
    ('EABTM', Point( 0.527344, 51.845323))
]

setup_fixed_model_corenodes = [
    ('CoreNode', Point(0.3, 51.825323))
]

setup_fixed_model_links = [
    ('EAARR', 'cab_1', LineString([(-0.582275, 51.804581), (0, 52), (-1.944580, 52.792175)])),
    ('EAARR', 'cab_2', LineString([(-0.582275, 51.804581), (0, 52), (-0.395508, 52.485498)])),
    ('EAARR', 'cab_3', LineString([(-0.582275, 51.804581), (0, 52), (-2.713623, 52.652437)])),
    ('EAARR', 'cab_4', LineString([(-0.582275, 51.804581), (0, 52), ( 0.417480, 51.147694)])),
    ('EABTM', 'cab_5', LineString([( 0.527344, 51.845323), (0, 52), ( 1.219482, 52.431944)])),
    ('EABTM', 'cab_6', LineString([( 0.527344, 51.845323), (0, 52), (-1.900635, 51.223443)])),
    ('EABTM', 'cab_7', LineString([( 0.527344, 51.845323), (0, 52), ( 0.802002, 51.154586)])),
    ('CoreNode', 'EAARR', LineString([( 0.547344, 51.845323), (0, 51), ( 0.602002, 51.354586)])),
    ('CoreNode', 'EABTM', LineString([( 0.547344, 51.845323), (0, 51), ( 0.602002, 51.354586)]))
]

write_points_to_shp(os.path.join(input_shapefiles_dir, 'fixed_model_pcp.shp'), setup_fixed_model_pcp)
write_points_to_shp(os.path.join(input_shapefiles_dir, 'fixed_model_exchanges.shp'), setup_fixed_model_exchanges)
write_points_to_shp(os.path.join(input_shapefiles_dir, 'fixed_model_corenodes.shp'), setup_fixed_model_corenodes)
write_links_to_shp(os.path.join(input_shapefiles_dir, 'fixed_model_links.shp'), setup_fixed_model_links)

# Synthesize network
Manager = ICTManager(input_shapefiles_dir)

# Analyse network
print(nx.info(Manager._network))

nx.draw(Manager._network, with_labels=True, font_weight='bold')
plt.show()

# Analyse network (Plot on map)
# pos = {}
# for node in (list(Manager._network.nodes)):
#     pos[node] = m(Manager._network.node[node]['pos'].y, Manager._network.node[node]['pos'].x) 


# print(pos)

# m = Basemap(
#         projection='merc',
#         llcrnrlon=-20,
#         llcrnrlat=50,
#         urcrnrlon=10,
#         urcrnrlat=60,
#         lat_ts=0,
#         resolution='h',
#         suppress_ticks=True)


# nx.draw_networkx(Manager._network,pos,node_size=100,node_color='red')
# m.drawcountries()
# m.bluemarble()

# Write shapefile
Manager.save(output_shapefiles_dir)