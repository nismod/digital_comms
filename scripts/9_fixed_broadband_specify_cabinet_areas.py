import fiona
import shapely.geometry as geometry
import pylab as pl
from descartes import PolygonPatch

import os
import configparser

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################
# setup file locations
#####################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'processed')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'processed')

with fiona.open("final_premises_with_all_attribute_data.shp") as input:
    meta = input.meta
    with fiona.open('cabinet_area.shp', 'w',**meta) as output:
        for feature in input:
             if feature['properties']['cabinet_id']
                 output.write(feature)







# #fiona, import points as shapefile
# shapefile = fiona.open(os.path.join(SYSTEM_INPUT_FIXED, 'final_premises_with_all_attribute_data.shp'))

# #?? obtain points ??
# points = [geometry.shape(point['geometry']) for point in shapefile]

# #identify x coordinates
# x = [p.coords.xy[0] for p in points]

# #identify y coordinates
# y = [p.coords.xy[1] for p in points]

# #plot coordinates
# pl.figure(figsize=(10,10))
# _ = pl.plot(x,y,'o', color='#f16824')

# #instantiate a MultiPoint
# point_collection = geometry.MultiPoint(list(points))

# #ask for the envelope of the MultiPoint collection
# point_collection.envelope

# #define function for plotting
# def plot_polygon(polygon):
#     fig = pl.figure(figsize=(10,10))
#     ax = fig.add_subplot(111)
#     margin = .3
#     x_min, y_min, x_max, y_max = polygon.bounds
#     ax.set_xlim([x_min-margin, x_max+margin])
#     ax.set_ylim([y_min-margin, y_max+margin])
#     patch = PolygonPatch(polygon, fc='#999999',
#                          ec='#000000', fill=True,
#                          zorder=-1)
#     ax.add_patch(patch)
#     return fig

# #specify plot based on outer envelope
# _ = plot_polygon(point_collection.envelope)
# _ = pl.plot(x,y,'o', color='#f16824')

# pl.show()

# #specify plot using convex_hull
# convex_hull_polygon = point_collection.convex_hull
# _ = plot_polygon(convex_hull_polygon)
# _ = pl.plot(x,y,'o', color='#f16824')

# pl.show()