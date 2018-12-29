import configparser
import os, sys

from grass_session import Session
from grass.script import core as gcore

def load_raster_files(list_of_tiles, output_dir, x_transmitter, y_transmitter):

    gis_path = os.path.join(output_dir, 'gisdb')

    transmitter_coords = str(x_transmitter) + ',' + str(y_transmitter)  

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with Session(gisdb=gis_path, location="location", create_opts="EPSG:27700"):
        
        print(gcore.parse_command("g.gisenv", flags="s"))
        
        for tile in list_of_tiles:
            base, ext = os.path.splitext(os.path.split(tile)[1])
            tile_name = "tile_%s" % base
            gcore.run_command('r.import', input=tile, output=tile_name, overwrite=True)
        
        rast_list = gcore.read_command('g.list', type='rast', pattern="tile_*", separator="comma").strip()
         
        gcore.run_command('r.external.out', flags="r")

        gcore.run_command('r.patch', input=rast_list, output="all_tiles", overwrite=True)
        gcore.run_command('r.viewshed',flags='b',input="all_tiles", output="viewshed", coordinates=transmitter_coords, overwrite=True)
        gcore.run_command('r.external.out', flags="r")

    return print('files loaded')


def generate_viewshed(x_transmitter, y_transmitter, output_dir, filename, tile_path):
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    gis_path = os.path.join(output_dir, 'gisdb')

    output_filename = '{}-viewshed.tif'.format(filename)

    transmitter_coords = str(x_transmitter) + ',' + str(y_transmitter)

    with Session(gisdb=gis_path, location="location", create_opts="EPSG:27700"):
    
        print(gcore.parse_command("g.gisenv", flags="s"))
        gcore.run_command('r.external', input=tile_path, output=filename, overwrite=True)
        gcore.run_command('r.external.out', directory=output_dir, format="GTiff")
        gcore.run_command('g.region', raster=filename)
        gcore.run_command('r.viewshed',flags='b',input=filename,output=output_filename,coordinates=transmitter_coords,overwrite=True)
        gcore.run_command('r.external.out', flags="r")

