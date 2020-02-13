# -*- coding: utf-8 -*-
"""
Created on Thu Oct 31 22:00:39 2013

@author: Vaclav Petras <wenzeslaus gmail.com>
"""

import os
import sys
import tempfile

import grass.script as gs
import grass.script.setup as gsetup

from routleaflet.utils import (
    get_region, set_region, get_location_proj_string, reproject_region,
    Mapset)


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


def proj_to_wgs84(region):
    proj_in = '{east} {north}\n{west} {south}'.format(**region)
    proc = gs.start_command('m.proj', input='-', separator=' , ',
                            flags='od',
                            stdin=gs.PIPE, stdout=gs.PIPE, stderr=gs.PIPE)
    proc.stdin.write(gs.encode(proj_in))
    proc.stdin.close()
    proc.stdin = None
    proj_out, errors = proc.communicate()
    if proc.returncode:
        raise RuntimeError("m.proj error: %s" % errors)
    enws = gs.decode(proj_out).split(os.linesep)
    elon, nlat, unused = enws[0].split(' ')
    wlon, slat, unused = enws[1].split(' ')
    return {'east': elon, 'north': nlat,
            'west': wlon, 'south': slat}


def get_map_extent_for_location(map_name):
    info_out = gs.read_command('r.info', map=map_name, flags='g')
    info = gs.parse_key_val(info_out, sep='=')
    return proj_to_wgs84(info)


def raster_to_png(map_name, output_file,
                  compression=None, routpng_flags=None, backend=None):
    """Convert raster map ``map_name`` to PNG file named ``output_file``

    :param compression: PNG file compression (0-9)
    :param routpng_flags: flags for r.out.png (see r.out.png --help)
    :param backend: ``r.out.png`` or ``d.rast``

    ``backend`` can be set to ``r.out.png`` for export using this module
    or ``d.rast`` for rendering using this module. The flags are
    applied in both cases. Default is platform dependent and it is subject
    to change based on the most reliable option for each platform.
    """
    if not backend:
        if sys.platform.startswith('win'):
            backend = 'd.rast'
        else:
            backend = 'r.out.png'
    if backend == 'r.out.png':
        gs.run_command('r.out.png', input=map_name, output=output_file,
                       compression=compression, flags=routpng_flags)
    else:
        from routleaflet.outputs import set_rendering_environment
        region = get_region()
        if region['nsres'] > region['ewres']:
            # oversample in rows, do not loose columns
            width = region['cols']
            height = region['rows'] * (region['nsres'] / region['ewres'])
        else:
            # oversample in columns, do not loose rows
            width = region['cols'] * (region['ewres'] / region['nsres'])
            height = region['rows']
        if 't' in routpng_flags:
            transparent = True
        else:
            transparent = False
        set_rendering_environment(width=width, height=height,
                                  filename=output_file,
                                  transparent=True, driver='cairo',
                                  compression=compression)
        gs.run_command('d.rast', map=map_name)
        if 'w' in routpng_flags:
            # TODO: the r.out.png flag -w (world file) is ignored
            gs.warning(_("World file for PNG with its actual SRS"
                         " not generated with conversion (export)"
                         " backend <{}>").format(backend))


# TODO: support parallel calls, rewrite as class?


def export_png_in_projection(src_mapset_name, map_name, output_file,
                             epsg_code,
                             routpng_flags, compression, wgs84_file,
                             use_region=True):
    """

    :param use_region: use computation region and not map extent
    """
    if use_region:
        src_region = get_region()
        src_proj_string = get_location_proj_string()

    # TODO: change only location and not gisdbase?
    # we rely on the tmp dir having enough space for our map
    tgt_gisdbase = tempfile.mkdtemp()
    # this is not needed if we use mkdtemp but why not
    tgt_location = 'r.out.png.proj_location_%s' % epsg_code
    # because we are using PERMANENT we don't have to create mapset explicitly
    tgt_mapset_name = 'PERMANENT'

    src_mapset = Mapset(name=src_mapset_name, use_current=True)
    assert src_mapset.exists()

    # get source (old) and set target (new) GISRC enviromental variable
    # TODO: set environ only for child processes could be enough and it would
    # enable (?) parallel runs
    src_gisrc = os.environ['GISRC']
    tgt_gisrc = gsetup.write_gisrc(tgt_gisdbase,
                                   tgt_location, tgt_mapset_name)
    os.environ['GISRC'] = tgt_gisrc
    # we do this only after we obtained region, so it was applied
    # and we don't need it in the temporary (tgt) mapset
    if os.environ.get('WIND_OVERRIDE'):
        old_temp_region = os.environ['WIND_OVERRIDE']
        del os.environ['WIND_OVERRIDE']
    else:
        old_temp_region = None

    tgt_mapset = Mapset(tgt_gisdbase, tgt_location, tgt_mapset_name)

    try:
        # the function itself is not safe for other (backgroud) processes
        # (e.g. GUI), however we already switched GISRC for us
        # and child processes, so we don't influece others
        gs.create_location(dbase=tgt_gisdbase,
                           location=tgt_location,
                           epsg=epsg_code,
                           datum=None,
                           datum_trans=None)
        assert tgt_mapset.exists()

        # we need to make the mapset change in the current GISRC (tgt)
        # note that the C library for this process still holds the
        # path to the old GISRC file (src)
        tgt_mapset.set_as_current(gisrc=tgt_gisrc)

        # setting region
        if use_region:
            # respecting computation region of the src location
            # by previous use g.region in src location
            # and m.proj and g.region now
            # respecting MASK of the src location would be hard
            # null values in map are usually enough
            tgt_proj_string = get_location_proj_string()
            tgt_region = reproject_region(src_region,
                                          from_proj=src_proj_string,
                                          to_proj=tgt_proj_string)
            # uses g.region thus and sets region only for child processes
            # which is enough now
            # TODO: unlike the other branch, this keeps the current
            # resolution which is not correct
            set_region(tgt_region)
        else:
            # find out map extent to import everything
            # using only classic API because of some problems with pygrass
            # on ms windows
            rproj_out = gs.read_command('r.proj', input=map_name,
                                        dbase=src_mapset.database,
                                        location=src_mapset.location,
                                        mapset=src_mapset.name,
                                        output=map_name, flags='g')
            a = gs.parse_key_val(rproj_out, sep='=', vsep=' ')
            gs.run_command('g.region', **a)

        # map import
        gs.message("Reprojecting...")
        gs.run_command('r.proj', input=map_name, dbase=src_mapset.database,
                       location=src_mapset.location, mapset=src_mapset.name,
                       output=map_name, quiet=True)

        # actual export
        gs.message("Rendering...")
        raster_to_png(map_name, output_file, compression=compression,
                      routpng_flags=routpng_flags)

        # outputting file with WGS84 coordinates
        if wgs84_file:
            gs.verbose("Projecting coordinates to LL WGS 84...")
            with open(wgs84_file, 'w') as data_file:
                if use_region:
                    # map which is smaller than region is imported in its own
                    # small extent, but we export image in region, so we need
                    # bounds to be for region, not map
                    # hopefully this is consistent with r.out.png behavior
                    data_file.write(
                        map_extent_to_file_content(
                            proj_to_wgs84(get_region())) + '\n')
                else:
                    # use map to get extent
                    # the result is actually the same as using map
                    # if region is the same as map (use_region == False)
                    data_file.write(
                        map_extent_to_file_content(
                            get_map_extent_for_location(map_name)) +
                        '\n')

    finally:
        # juts in case we need to do something in the old location
        # our callers probably do
        os.environ['GISRC'] = src_gisrc
        if old_temp_region:
            os.environ['WIND_OVERRIDE'] = old_temp_region
        # set current in library
        src_mapset.set_as_current(gisrc=src_gisrc)

        # delete the whole gisdbase
        # delete file by file to ensure that we are deleting only our things
        # exception will be raised when removing non-empty directory
        tgt_mapset.delete()
        os.rmdir(tgt_mapset.location_path)
        # dir created by tempfile.mkdtemp() needs to be romved manually
        os.rmdir(tgt_gisdbase)
        # we have to remove file created by tempfile.mkstemp function
        # in write_gisrc function
        os.remove(tgt_gisrc)
