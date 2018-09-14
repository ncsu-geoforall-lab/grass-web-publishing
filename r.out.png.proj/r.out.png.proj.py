#!/usr/bin/env python
#
############################################################################
#
# MODULE:       r.out.png.proj
# AUTHOR(S):    Vaclav Petras
# PURPOSE:      Outputs a raster map as an PNG image in specified location
#
# COPYRIGHT:    (C) 2013-2018 by Vaclav Petras and the GRASS Development Team
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
#% key: m
#% description: Use map extent instead of current region
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

import grass.script as gs
from grass.script.utils import set_path


set_path(modulename='r.out.png.proj', dirname='routleaflet',
         path=os.path.join(os.path.dirname(__file__), '..'))


from routleaflet.pngproj import export_png_in_projection


def main():
    options, flags = gs.parser()

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

    if flags['m']:
        use_region = False
    else:
        use_region = True

    # TODO: mixing current and map's mapset at this point
    # or perhaps not an issue if parser adds mapset automatically (?)
    if '@' in map_name:
        map_name, src_mapset_name = map_name.split('@')
    else:
        src_mapset_name = gs.gisenv()['MAPSET']

    export_png_in_projection(map_name=map_name,
                             src_mapset_name=src_mapset_name,
                             output_file=output_file,
                             epsg_code=epsg_code,
                             compression=compression,
                             routpng_flags=routpng_flags,
                             wgs84_file=wgs84_file,
                             use_region=use_region)


if __name__ == '__main__':
    sys.exit(main())
