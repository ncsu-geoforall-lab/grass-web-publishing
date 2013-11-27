#!/usr/bin/env python
#
############################################################################
#
# MODULE:       r.out.png.proj
# AUTHOR(S):    Vaclav Petras
# PURPOSE:      Outputs a raster map as an PNG image in specified location
#
# COPYRIGHT:    (C) 2013 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################


#%module
#% description: Outputs a raster map as an PNG image in specified location
#% keywords: raster
#% keywords: export
#% keywords: PNG
#% keywords: projection
#%end
#%option G_OPT_R_INPUT
#%end
#%option G_OPT_F_OUTPUT
#%end
#%option
#% key: epsg
#% type: integer
#% label: EPSG projection code
#% description: EPSG code of the projection which will be used for projecting raster map, e.g. '3857' for Spherical Mercator.
#% required: yes
#% options: 1-100000
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
#% key: t
#% description: Make NULL cells transparent
#%end
#%flag
#% key: w
#% description: Output world file
#%end
#%flag
#% key: l
#% description: Output LL WGS84 file
#%end

"""
Created on Fri Oct  4 17:17:49 2013

@author: Vaclav Petras <wenzeslaus gmail.com>
"""

import os
import sys

from grass.script import core as gcore

# TODO: put this to grass.utils
def add_pythonlib_to_path(name):
    libpath = None
    # this is specified by Makefile
    if os.path.isdir(os.path.join(os.getenv('GISBASE'), 'etc', name)):
        libpath = os.path.join(os.getenv('GISBASE'), 'etc', name)
    elif os.getenv('GRASS_ADDON_BASE') and \
            os.path.isdir(os.path.join(os.getenv('GRASS_ADDON_BASE'), 'etc',
                                       name)):
        libpath = os.path.join(os.getenv('GRASS_ADDON_BASE'), 'etc', name)
    # this is the directory name
    elif os.path.join(os.path.dirname(__file__), '..', name):
        libpath = os.path.join(os.path.dirname(__file__), '..')
    # maybe this should be removed because it is useless
    elif os.path.isdir(os.path.join('..', name)):
        libpath = os.path.join('..', name)
    else:
        gcore.fatal(_("Python library '%s' not found. Probably it was not"
                      "intalled correctly.") % name)

    sys.path.append(libpath)

add_pythonlib_to_path('routleaflet')

# maybe this would be the same without try-except
# TODO: ask about the best practice on ML
# the reason for the except with long message is actually debugging of
# the previous setting of the path, considering the fact that it will be never
# 100% sure, the try-except has the reason
try:
    from routleaflet.pngproj import export_png_in_projection
except ImportError, error:
    gcore.fatal(_("Cannot import from routleaflet: ") + str(error)
                + _("\nThe search path (sys.path) is: ") + str(sys.path))

def main():
    options, flags = gcore.parser()

    # main options
    map_name = options['input']
    output_file = options['output']
    # TODO: other options of g.proj are not supported
    epsg_code = int(options['epsg'])
    # r.out.png options
    compression = int(options['compression'])
    # both flags (tw) passed to r.out.png
    routpng_flags = ''
    if flags['t']:
        routpng_flags += 't'
    if flags['w']:
        routpng_flags += 'w'
    if flags['l']:
        wgs84_file = output_file + '.wgs84'
    else:
        wgs84_file = None

    if '@' in map_name:
        map_name, src_mapset_name = map_name.split('@')
    else:
        # TODO: maybe mapset is mandatory for those out of current mapset?
        src_mapset_name = ''

    export_png_in_projection(map_name=map_name,
                             src_mapset_name=src_mapset_name,
                             output_file=output_file,
                             epsg_code=epsg_code,
                             compression=compression,
                             routpng_flags=routpng_flags,
                             wgs84_file=wgs84_file)

if __name__ == '__main__':
    sys.exit(main())
