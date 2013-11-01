# -*- coding: utf-8 -*-
"""
Created on Thu Oct 31 22:00:39 2013

@author: Vaclav Petras <wenzeslaus gmail.com>
"""

import os
import tempfile

from grass.script import core as gcore
from grass.script import setup as gsetup
from grass.pygrass.modules import Module
from grass.pygrass.gis import Mapset, Location


def map_extent_to_js_leaflet_list(extent):
    """extent dictionary with latitudes and longitudes extent
    (east, north, west, south)
    """
    return "[[{south}, {east}], [{north}, {west}]]".format(**extent)


def map_extent_to_file_content(extent):
    """extent dictionary with latitudes and longitudes extent
    (east, north, west, south)
    """
    return "{east} {north}\n{west} {south}".format(**extent)


def get_map_extent_for_file(file_name):
    wgs84_file = open(file_name, 'r')
    enws = wgs84_file.readlines()
    elon, nlat = enws[0].strip().split(' ')
    wlon, slat = enws[1].strip().split(' ')
    return {'east': elon, 'north': nlat,
            'west': wlon, 'south': slat}


# TODO: support parallel calls, rewrite as class?
def get_map_extent_for_location(map_name):
    info_out = gcore.read_command('r.info', map=map_name, flags='g')
    info = gcore.parse_key_val(info_out, sep='=')
    proj_in = '{east} {north}\n{west} {south}'.format(**info)
    print proj_in
    proc = gcore.start_command('m.proj', input='-', separator=' , ',
                               flags='od', stdin=gcore.PIPE, stdout=gcore.PIPE)
    proc.stdin.write(proj_in)
    proc.stdin.close()
    proc.stdin = None
    proj_out = proc.communicate()[0]
    enws = proj_out.split(os.linesep)
    elon, nlat, unused = enws[0].split(' ')
    wlon, slat, unused = enws[1].split(' ')
    print enws
    return {'east': elon, 'north': nlat,
            'west': wlon, 'south': slat}

    #mproj = Module('m.proj')
    #mproj.inputs.stdin = proj_in
    #mproj(flags='o', input='-', stdin_=subprocess.PIPE,
    #      stdout_=subprocess.PIPE)
    #print mproj.outputs.stdout


def export_png_in_projection(src_mapset_name, map_name, output_file,
                             epsg_code,
                             routpng_flags, compression, wgs84_file):
    # TODO: change only location and not gisdbase?
    # we rely on the tmp dir having enough space for our map
    tgt_gisdbase = tempfile.mkdtemp()
    # this is not needed if we use mkdtemp but why not
    tgt_location = 'r.out.png.proj_location_%s' % epsg_code
    # because we are using PERMANENT we don't have to create mapset explicitly
    tgt_mapset_name = 'PERMANENT'

    src_mapset = Mapset(src_mapset_name)

    # get source (old) and set target (new) GISRC enviromental variable
    src_gisrc = os.environ['GISRC']
    tgt_gisrc = gsetup.write_gisrc(tgt_gisdbase,
                                   tgt_location, tgt_mapset_name)
    os.environ['GISRC'] = tgt_gisrc
    # these lines looks good but anyway when developing the module
    # switching location seemed fragile and on some errors (while running
    # unfinished module) location was switched in the command line

    try:
        # the function itself is not safe for other (backgroud) processes
        # (e.g. GUI), however we already switched GISRC for us
        # and child processes, so we don't influece others
        gcore.create_location(dbase=tgt_gisdbase,
                              location=tgt_location,
                              epsg=epsg_code,
                              datum=None,
                              datum_trans=None)

        # Mapset object cannot be created if the real mapset does not exists
        tgt_mapset = Mapset(gisdbase=tgt_gisdbase, location=tgt_location,
                            mapset=tgt_mapset_name)
        # set the current mapset in the library
        # we actually don't need to switch when only calling modules
        # (right GISRC is enough for them)
        tgt_mapset.current()

        # map import
        # respect comp region of the src location would be nice
        # (using g.region in src location and m.proj)
        # respect MASK of the src location would be hard
        # and null values are usually enough

        # find out map extent to import everything
        # combining pygrass also with classic API because of some problems
        # however, rewriting to pygrass should be possible
        rproj_out = gcore.read_command('r.proj', input=map_name,
                                       dbase=src_mapset.gisdbase,
                                       location=src_mapset.location,
                                       mapset=src_mapset.name,
                                       output=map_name, flags='g')
        a = gcore.parse_key_val(rproj_out, sep='=', vsep=' ')
        gcore.run_command('g.region', **a)
        # map import
        r_proj = Module('r.proj')
        r_proj(input=map_name, dbase=src_mapset.gisdbase,
               location=src_mapset.location, mapset=src_mapset.name,
               output=map_name)

        # actual work here
        r_out_png = Module('r.out.png')
        r_out_png(input=map_name, output=output_file, compression=compression,
                  flags=routpng_flags)

        if wgs84_file:
            data_file = open(wgs84_file, 'w')
            data_file.write(
                map_extent_to_file_content(
                    get_map_extent_for_location(map_name))
                + '\n')

    finally:
        # juts in case we need to do something in the old location
        os.environ['GISRC'] = src_gisrc
        # set current in library
        src_mapset.current()

        # delete the whole gisdbase
        # delete file by file to ensure that we are deleting only our things
        # exception will be raised when removing non-empty directory
        tgt_location_path = Location(gisdbase=tgt_gisdbase,
                                     location=tgt_location).path()
        tgt_mapset.delete()
        os.rmdir(tgt_location_path)
        # dir created by tempfile.mkdtemp() needs to be romved manually
        os.rmdir(tgt_gisdbase)
        # we have to remove file created by tempfile.mkstemp function
        # in write_gisrc function
        os.remove(tgt_gisrc)
