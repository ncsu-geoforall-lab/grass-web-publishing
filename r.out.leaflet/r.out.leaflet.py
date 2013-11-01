#!/usr/bin/env python
#
############################################################################
#
# MODULE:       r.out.leaflet
# AUTHOR(S):    Vaclav Petras
# PURPOSE:      Outputs raster maps prepared for a Leaflet web map
#
# COPYRIGHT:    (C) 2013 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################


#%module
#% description: Outputs raster maps prepared for a Leaflet web map
#% keywords: raster
#% keywords: export
#% keywords: visualization
#% keywords: web
#%end
#%option G_OPT_R_INPUT
#% key: raster
#% label: Name(s) of input raster map(s)
#% description: Either this or strds option must be used to specify the input.
#% multiple: yes
#% required: no
#% guisection: Input
#%end
#%option G_OPT_STRDS_INPUT
#% key: strds
#% label: Name of the input space time raster dataset
#% description: Either this or raster option must be used to specify the input.
#% required: no
#% guisection: Input
#%end
#%option G_OPT_T_WHERE
#% required: no
#% guisection: Input
#%end
#%option G_OPT_M_DIR
#% key: output
#% label: Output directory
#% description: Directory must exists and should be empty but this is not checked by the script. Some parts may fail is the files will be in the directory. Overwrite is not implemented yet.
#% guisection: Output
#%end
#%option
#% key: epsg
#% type: integer
#% label: EPSG projection code
#% description: EPSG code of the projection which will be used for projecting raster map. Leaflet by default uses Spherical Mercator (EPSG:3857).
#% required: no
#% options: 1-100000
#% answer: 3857
#%end
#%option
#% key: opacity
#% type: integer
#% label: Layer opacity
#% description: Either one value or the same number of values as number of input maps is required. Use 0 for fully transparent image and 1 for fully opaque image.
#% required: no
#% multiple: yes
#% options: 0-1
#% answer: 1
#%end
#%option
#% key: compression
#% type: integer
#% label: Compression level of PNG file
#% description: (0 = none, 1 = fastest, 9 = best)
#% required: no
#% answer: 6
#% options: 0-9
#%end
#%flag
#% key: n
#% label: Do not make NULL cells transparent
#% description: When map is overlay NULL cells should be transparent. However, note that r.out.png does not make NULL cells transparent by default.
#%end
#%flag
#% key: w
#% description: Output world file
#%end

"""
Created on Fri Oct  4 17:17:49 2013

@author: Vaclav Petras <wenzeslaus gmail.com>
"""

import os
import sys

from grass.script import core as gcore
from grass.pygrass.modules import Module


def map_extent_to_js_leaflet_list(extent):
    """extent dictionary with latitudes and longitudes extent (east, north, west, south)"""
    return "[[{south}, {east}], [{north}, {west}]]".format(**extent)


def get_map_extent_for_file(file_name):
    wgs84_file = open(file_name, 'r')
    enws = wgs84_file.readlines()
    elon, nlat = enws[0].strip().split(' ')
    wlon, slat = enws[1].strip().split(' ')
    return {'east': elon, 'north': nlat,
            'west': wlon, 'south': slat}


def main():
    options, flags = gcore.parser()

    # it does not check if pngs and other files exists,
    # maybe it could check the any/all file(s) dir

    if options['raster'] and options['strds']:
        gcore.fatal(_("Options raster and strds cannot be specified together."
                      " Please decide for one of them."))
    if options['raster'] and options['where']:
        gcore.fatal(_("Option where cannot be combined with the option raster."
                      " Please don't set where option or use strds option"
                      " instead of raster option."))
    if options['raster']:
        if ',' in options['raster']:
            maps = options['raster'].split(',') #TODO: skip empty parts
        else:
            maps = [options['raster']]
    elif options['strds']:
        # import and init only when needed
        # init is called anyway when the generated form is used
        import grass.temporal as tgis

        strds = options['strds']
        where = options['where']

        # make sure the temporal database exists
        tgis.init()

        # create the space time raster object
        ds = tgis.open_old_space_time_dataset(strds, 'strds')
        # check if the dataset is in the temporal database
        if not ds.is_in_db():
            gcore.fatal(_("Space time dataset <%s> not found") % strds)

        # we need a database interface
        dbiface = tgis.SQLDatabaseInterfaceConnection()
        dbiface.connect()

        # the query
        rows = ds.get_registered_maps(columns='id', where=where)
        if not rows:
            gcore.fatal(_("Cannot get any maps for spatio-temporal raster"
                          " dataset <%s>."
                          " Dataset is empty or you temporal WHERE"
                          " condition filtered all maps out."
                          " Please, specify another dataset,"
                          " put maps into this dataset"
                          " or correct your WHERE condition.") % strds)
        maps = [row['id'] for row in rows]
    else:
        gcore.fatal(_("Either raster or strds option must be specified."
                      " Please specify one of them."))
    # get the number of maps for later use
    num_maps = len(maps)

    out_dir = options['output']
    if not os.path.exists(out_dir):
        # TODO: maybe we could create the last dir on specified path?
        gcore.fatal(_("Output path <%s> does not exists."
                      " You need to create the (empty) output directory"
                      " yourself before running this module.") % out_dir)
    epsg = int(options['epsg'])

    if ',' in options['opacity']:
        opacities = [float(opacity)
                     for opacity in options['opacity'].split(',')]
        if len(opacities) != num_maps:
            gcore.fatal(_("Number of opacities <{no}> does not match number"
                          " of maps <{nm}>.").format(no=len(opacities),
                                                     nm=num_maps))
    else:
        opacities = [float(options['opacity'])] * num_maps

    # r.out.png options
    compression = int(options['compression'])
    # flag w is passed to r.out.png.proj
    # our flag n is inversion of r.out.png.proj's t flag
    # (transparent NULLs are better for overlay)
    # we always need the l flag (ll .wgs84 file)
    routpngproj_flags = 'l'
    if not flags['n']:
        routpngproj_flags += 't'
    if flags['w']:
        routpngproj_flags += 'w'

    # hard coded file names
    data_file_name = 'data_file.csv'
    js_data_file_name = 'data_file.js'

    data_file = open(os.path.join(out_dir, data_file_name), 'w')
    js_data_file = open(os.path.join(out_dir, js_data_file_name), 'w')
    js_data_file.write('/* This file was generated by r.out.leaflet GRASS GIS'
                       ' module. */\n\n')
    js_data_file.write('var layerInfos = [\n')

    for i, map_name in enumerate(maps):
        routpng = Module('r.out.png.proj')
        if '@' in map_name:
            pure_map_name = map_name.split('@')[0]
        else:
            pure_map_name = map_name
        image_file_name = pure_map_name + '.png'
        image_file_path = os.path.join(out_dir, image_file_name)
        routpng(input=map_name,
                output=image_file_path,
                epsg=epsg,
                compression=compression,
                flags=routpngproj_flags)

        data_file.write(pure_map_name + ',' + image_file_name + '\n')

        # it doesn't matter in which location we are, it just uses the current
        # location, not tested for LL loc, assuming that to be nop.
        map_extent = get_map_extent_for_file(image_file_path + '.wgs84')
        bounds = map_extent_to_js_leaflet_list(map_extent)

        # http://www.w3schools.com/js/js_objects.asp
        js_data_file.write("""   {{title: "{title}", file: "{file_}","""
                           """ bounds: {bounds}, opacity: {opacity}}}\n"""
                           .format(title=pure_map_name,
                                   file_=image_file_name,
                                   bounds=bounds,
                                   opacity=opacities[i]))
        # do not write after the last item
        if i < num_maps - 1:
            js_data_file.write(',')
    js_data_file.write('];\n')
    data_file.close()


if __name__ == '__main__':
    sys.exit(main())
