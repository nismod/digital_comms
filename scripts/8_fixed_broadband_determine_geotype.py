from rtree import index
from collections import OrderedDict
import fiona
import os
import time
import configparser
import csv

CONFIG = configparser.ConfigParser()
CONFIG.read(os.path.join(os.path.dirname(__file__), 'script_config.ini'))
BASE_PATH = CONFIG['file_locations']['base_path']

#####################
# setup file locations
#####################

SYSTEM_INPUT_FIXED = os.path.join(BASE_PATH, 'processed')
SYSTEM_OUTPUT_FILENAME = os.path.join(BASE_PATH, 'processed')

# Initialize timer
start = time.time()

##################################
# load in postcode to cabinet data
##################################

start = time.time()

lut_pcb2cab = {}

with fiona.open(os.path.join(SYSTEM_INPUT_FIXED, 'final_premises_with_all_attribute_data.shp'), 'r') as source:

    # Read the postcode-to-cabinet-to-exchange lookup file into Rtree
    with open(os.path.join(SYSTEM_INPUT_FIXED, 'pcp_data.csv'), 'r') as f:
        reader = csv.reader(f)
        next(reader)

        i = 0
        cabinets = {}

        for row in reader:

            # Map and pre-process Csv data
            cabinets['postcode'] = row[2]
            cabinets['cabinet_id'] = row[3]

            # Add to Rtree and lookup table
            lut_pcb2cab[cabinets['postcode']] = cabinets['cabinet_id']

    # Write exchange polygons

    sink_schema = source.schema
    sink_schema['properties']['cabinet_id'] = 'str:30'
    sink_schema['properties']['cabinet_SRC'] = 'str:30'

    # Open output file
    sink = fiona.open(os.path.join(BASE_PATH, 'processed', 'final_premises_points_with_cabinet_id.shp'), 'w', crs=source.crs, driver=source.driver, schema=sink_schema)

    # Connect each postcode area to an exchange
    for premises in source:

        f = premises
        postcode = premises['properties']['postcode'].replace(" ", "")

        if postcode in lut_pcb2cab:

            # Postcode-to-cabinet-to-exchange association
            f['properties']['cabinet_id'] = lut_pcb2cab[postcode]
            f['properties']['cabinet_SRC'] = 'EXISTING CABINET DATA'

        else:

            # Find nearest exchange
            f['properties']['cabinet_id'] = 'NO CABINET'
            f['properties']['cabinet_SRC'] = 'NO CABINET'

        # Write to file
        sink.write(f)

    sink.close()

end = time.time()
print('Script completed in: ' + str(round((end - start), 2)) + ' seconds.')














# def read_cabinets():

#     pcp_data = []

#     with open(os.path.join(SYSTEM_INPUT_FIXED, 'pcp_data.csv'), 'r') as system_file:
#         reader = csv.reader(system_file)
#         next(reader)
#         for line in reader:
#             pcp_data.append({
#                 #'exchange_id': line[0],
#                 #'name': line[1],
#                 'postcode': line[2],
#                 'cabinet_id': line[3],
#                 #'exchange_only_flag': line[4]
#             })
#     return pcp_data

# print('read cabinets')
# cabinets = read_cabinets()
# for cab in cabinets:
#     print (cab)










# geotype_data = [
#     OrderedDict([('geotype', 'Inner London'), ('exchanges', 86), ('ave_lines', 16812),
#                 ('cabinets', 2892), ('ave_lines_per_cabinet', 500), ('dist_points', 172118),
#                 ('ave_lines_per_dist_point', 8.4), ('ave_line_length', 1240)]),
#     OrderedDict([('geotype', '>500 pop'), ('exchanges', 204), ('ave_lines', 15512),
#                 ('cabinets', 6329), ('ave_lines_per_cabinet', 500), ('dist_points', 376721),
#                 ('ave_lines_per_dist_point', 8.4), ('ave_line_length', 1780)]),
#     OrderedDict([('geotype', '>200k pop'), ('exchanges', 180), ('ave_lines', 15527),
#                 ('cabinets', 5590), ('ave_lines_per_cabinet', 500), ('dist_points', 332713),
#                 ('ave_lines_per_dist_point', 8.4), ('ave_line_length', 1800)]),
#     OrderedDict([('geotype', '>20k lines (a)'), ('exchanges', 167), ('ave_lines', 17089),
#                 ('cabinets', 6008), ('ave_lines_per_cabinet', 475), ('dist_points', 365886),
#                 ('ave_lines_per_dist_point', 7.8), ('ave_line_length', 1500)]),
#     OrderedDict([('geotype', '>20k lines (b)'), ('exchanges', 167), ('ave_lines', 10449),
#                 ('cabinets', 4362), ('ave_lines_per_cabinet', 400), ('dist_points', 223708),
#                 ('ave_lines_per_dist_point', 7.8), ('ave_line_length', 4.83)]),
#     OrderedDict([('geotype', '>10k lines (a)'), ('exchanges', 406), ('ave_lines', 10728),
#                 ('cabinets', 9679), ('ave_lines_per_cabinet', 450), ('dist_points', 604925),
#                 ('ave_lines_per_dist_point', 7.2), ('ave_line_length', 1400)]),
#     OrderedDict([('geotype', '>10k lines (b)'), ('exchanges', 406), ('ave_lines', 3826),
#                 ('cabinets', 4142), ('ave_lines_per_cabinet', 375), ('dist_points', 215740),
#                 ('ave_lines_per_dist_point', 7.2), ('ave_line_length', 4000)]),
#     OrderedDict([('geotype', '>3k lines (a)'), ('exchanges', 1003), ('ave_lines', 2751),
#                 ('cabinets', 13455), ('ave_lines_per_cabinet', 205), ('dist_points', 493569),
#                 ('ave_lines_per_dist_point', 5.6), ('ave_line_length', 730)]),
#     OrderedDict([('geotype', '>3k lines (b)'), ('exchanges', 1003), ('ave_lines', 3181),
#                 ('cabinets', 22227), ('ave_lines_per_cabinet', 144), ('dist_points', 570745),
#                 ('ave_lines_per_dist_point', 5.6), ('ave_line_length', 4830)]),
#     OrderedDict([('geotype', '>1k lines (a)'), ('exchanges', 1230), ('ave_lines', 897),
#                 ('cabinets', 5974), ('ave_lines_per_cabinet', 185), ('dist_points', 246555),
#                 ('ave_lines_per_dist_point', 4.5), ('ave_line_length', 620)]),
#     OrderedDict([('geotype', '>1k lines (b)'), ('exchanges', 1230), ('ave_lines', 935),
#                 ('cabinets', 9343), ('ave_lines_per_cabinet', 123), ('dist_points', 257043),
#                 ('ave_lines_per_dist_point', 4.5), ('ave_line_length', 4090)]),
#     OrderedDict([('geotype', '<1k lines (a)'), ('exchanges', 2302), ('ave_lines', 190),
#                 ('cabinets', 0), ('ave_lines_per_cabinet', 0), ('dist_points', 130706),
#                 ('ave_lines_per_dist_point', 3.4), ('ave_line_length', 520)]),
#     OrderedDict([('geotype', '<1k lines (b)'), ('exchanges', 2302), ('ave_lines', 305),
#                 ('cabinets', 0), ('ave_lines_per_cabinet', 0), ('dist_points', 209571),
#                 ('ave_lines_per_dist_point', 3.4), ('ave_line_length', 4260)]),
#                 ]






# #####################
# # find representative points from postcode polygons
# #####################

# with fiona.open(os.path.join(SYSTEM_INPUT_FIXED, 'cb.shp'), 'r') as source:
#     # preserve the schema of the original shapefile, including the crs
#     meta = source.meta
#     meta['schema']['geometry'] = 'Point'
#     # Write exchange polygons
#     with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, 'postcode_polygon_centroids.shp'), 'w', **meta) as sink:

#         for f in source:

#             centroid = shape(f['geometry']).representative_point()

#             f['geometry'] = mapping(centroid)

#             sink.write(f)

# #####################
# # spatial join of polygon attributes to all points within that polygon
# #####################

# with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, "exchange_boundary_polygons_dissolved.shp"), "r") as n:

#     with fiona.open(os.path.join(SYSTEM_OUTPUT_FILENAME, "pcd_shapes_no_verticals.shp"), "r") as s:

#         # create a schema for the attributes
#         outSchema =  deepcopy(s.schema)
#         outSchema['properties'].update(n.schema['properties'])

#         with fiona.open (os.path.join(SYSTEM_OUTPUT_FILENAME, "postcode_points_with_exchange_area_id.shp"), "w", s.driver, outSchema, s.crs) as output:

#             for postcode in s:
#                 for exchange in n:
#                     # check if point is in polygon and set attribute
#                     if shape(postcode['geometry']).within(shape(exchange['geometry'])):
#                         postcode['properties']['EX_ID'] = exchange['properties']['EX_ID']
#                     # write out
#                         output.write({
#                             'properties': postcode['properties'],
#                             'geometry': postcode['geometry']
#                         })

end = time.time()
print('Script completed in: ' + str(round((end - start), 2)) + ' seconds.')



# if __name__ == "__main__":

#     print('read cabinets')
#     premises = read_cabinets()
