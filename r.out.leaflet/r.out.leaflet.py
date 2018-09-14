#!/usr/bin/env python
#
############################################################################
#
# MODULE:       r.out.leaflet
# AUTHOR(S):    Vaclav Petras
# PURPOSE:      Outputs raster maps prepared for a Leaflet web map
#
# COPYRIGHT:    (C) 2013-2018 by Vaclav Petras and the GRASS Development Team
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
#% description: Directory must exists and should be empty but this is not checked by the script. Some parts may fail if the files will be in the directory. Overwrite is not implemented yet.
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
#% key: info
#% type: string
#% label: Additional information to be exported
#% description: Specifies which information about maps should be exported
#% required: no
#% multiple: yes
#% options: legend, histogram, pie-histogram, info, statistics, thumbnail, geotiff, packed-map
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
#% label: Use map extent instead of current region
#% description: Instead of current region, each map extent will be used for export map and additional information. This can be advantage for map extents, zooming to map layers and exported images but it can be confusing when comparing map histograms or map staticstics.
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

import grass.script as gs


gs.set_path(modulename='r.out.leaflet', dirname='routleaflet',
            path=os.path.join(os.path.dirname(__file__), '..'))


from routleaflet.pngproj import (
    get_map_extent_for_file, map_extent_to_js_leaflet_list,
    export_png_in_projection)
import routleaflet.outputs as loutputs


def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)


def escape_endlines(text):
    return text.replace('\n', '\\n')


def escape_quotes(text):
    return text.replace('"', '\\"')


def escape_backslashes(text):
    return text.replace('\\', '\\\\')


def generate_infos(map_name, projected_png_file, output_directory,
                   required_infos, attributes):
    histogram_width = 500
    histogram_height = 500

    if 'legend' in required_infos:
        file_name = map_name + '.png'
        file_path = os.path.join(output_directory, 'legends',
                                 file_name)
        ensure_dir(file_path)
        # let's use histogram size
        loutputs.export_legend(map_name, file_path,
                               width=histogram_width,
                               height=histogram_height)
        attributes.append(('legend', file_name))

    if 'histogram' in required_infos:
        file_name = map_name + '.png'
        file_path = os.path.join(output_directory, 'histograms',
                                 file_name)
        ensure_dir(file_path)
        loutputs.export_histogram(map_name, file_path,
                                  width=histogram_width,
                                  height=histogram_height)
        attributes.append(('histogram', file_name))

    if 'pie-histogram' in required_infos:
        file_name = map_name + '.png'
        file_path = os.path.join(output_directory, 'pie-histograms',
                                 file_name)
        ensure_dir(file_path)
        loutputs.export_histogram(map_name, file_path,
                                  width=histogram_width,
                                  height=histogram_height,
                                  style='pie')
        attributes.append(('piehistogram', file_name))

    if 'info' in required_infos:
        file_name = map_name + '.txt'
        file_path = os.path.join(output_directory, 'infos',
                                 file_name)
        ensure_dir(file_path)
        loutputs.export_info(map_name, file_path)
        attributes.append(('infofile', file_name))
        with open(file_path, 'r') as data_file:
            content = data_file.read()
            attributes.append(('info', content))

    if 'statistics' in required_infos:
        file_name = map_name + '.txt'
        file_path = os.path.join(output_directory, 'statistics',
                                 file_name)
        ensure_dir(file_path)
        loutputs.export_statistics(map_name, file_path)
        attributes.append(('statisticsfile', file_name))
        with open(file_path, 'r') as data_file:
            content = data_file.read()
            attributes.append(('statistics', content))

    if 'thumbnail' in required_infos:
        file_name = map_name + '.png'
        file_path = os.path.join(output_directory, 'thumbnails',
                                 file_name)
        ensure_dir(file_path)
        loutputs.thumbnail_image(projected_png_file, file_path)
        attributes.append(('thumbnail', file_name))

    if 'geotiff' in required_infos:
        file_name = map_name + '.tif'  # r.out.tiff always uses this extension
        file_path = os.path.join(output_directory, 'geotiffs',
                                 file_name)
        ensure_dir(file_path)
        loutputs.export_raster_as_geotiff(map_name, file_path)
        attributes.append(('geotiff', file_name))

    if 'packed-map' in required_infos:
        file_name = map_name + '.pack'
        file_path = os.path.join(output_directory, 'packed-maps',
                                 file_name)
        ensure_dir(file_path)
        loutputs.export_raster_packed(map_name, file_path)
        attributes.append(('packedmap', file_name))


def main():
    options, flags = gs.parser()

    # it does not check if pngs and other files exists,
    # maybe it could check the any/all file(s) dir

    if options['raster'] and options['strds']:
        gs.fatal(_("Options raster and strds cannot be specified together."
                   " Please decide for one of them."))
    if options['raster'] and options['where']:
        gs.fatal(_("Option where cannot be combined with the option raster."
                   " Please don't set where option or use strds option"
                   " instead of raster option."))
    if options['raster']:
        if ',' in options['raster']:
            maps = options['raster'].split(',')  # TODO: skip empty parts
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
            gs.fatal(_("Space time dataset <%s> not found") % strds)

        # we need a database interface
        dbiface = tgis.SQLDatabaseInterfaceConnection()
        dbiface.connect()

        # the query
        rows = ds.get_registered_maps(columns='id', where=where,
                                      order='start_time')
        if not rows:
            gs.fatal(_("Cannot get any maps for spatio-temporal raster"
                       " dataset <%s>."
                       " Dataset is empty or you temporal WHERE"
                       " condition filtered all maps out."
                       " Please, specify another dataset,"
                       " put maps into this dataset"
                       " or correct your WHERE condition.") % strds)
        maps = [row['id'] for row in rows]
    else:
        gs.fatal(_("Either raster or strds option must be specified."
                   " Please specify one of them."))
    # get the number of maps for later use
    num_maps = len(maps)

    out_dir = options['output']
    if not os.path.exists(out_dir):
        # TODO: maybe we could create the last dir on specified path?
        gs.fatal(_("Output path <%s> does not exists."
                   " You need to create the (empty) output directory"
                   " yourself before running this module.") % out_dir)
    epsg = int(options['epsg'])

    if ',' in options['opacity']:
        opacities = [float(opacity)
                     for opacity in options['opacity'].split(',')]
        if len(opacities) != num_maps:
            gs.fatal(_("Number of opacities <{no}> does not match number"
                       " of maps <{nm}>.").format(no=len(opacities),
                                                  nm=num_maps))
    else:
        opacities = [float(options['opacity'])] * num_maps

    if ',' in options['info']:
        infos = options['info'].split(',')
    else:
        infos = [options['info']]

    if 'geotiff' in infos and not gs.find_program('r.out.tiff', '--help'):
        gs.fatal(_("Install r.out.tiff add-on module to export GeoTIFF"))

    # r.out.png options
    compression = int(options['compression'])
    # flag w is passed to r.out.png.proj
    # our flag n is inversion of r.out.png.proj's t flag
    # (transparent NULLs are better for overlay)
    # we always need the l flag (ll .wgs84 file)
    routpng_flags = ''
    if not flags['n']:
        routpng_flags += 't'
    if flags['w']:
        routpng_flags += 'w'
    # r.out.png.proj l flag for LL .wgs84 file is now function parameter
    # and is specified bellow

    if flags['m']:
        use_region = False
        # we will use map extent
        gs.use_temp_region()
    else:
        use_region = True

    # hard coded file names
    data_file_name = 'data_file.csv'
    js_data_file_name = 'data_file.js'

    data_file = open(os.path.join(out_dir, data_file_name), 'w')
    js_data_file = open(os.path.join(out_dir, js_data_file_name), 'w')
    js_data_file.write('/* This file was generated by r.out.leaflet GRASS GIS'
                       ' module. */\n\n')
    js_data_file.write('var layerInfos = [\n')

    for i, map_name in enumerate(maps):
        if not use_region:
            gs.run_command('g.region', rast=map_name)
        if '@' in map_name:
            pure_map_name = map_name.split('@')[0]
        else:
            pure_map_name = map_name
        # TODO: mixing current and map's mapset at this point
        if '@' in map_name:
            map_name, src_mapset_name = map_name.split('@')
        else:
            # TODO: maybe mapset is mandatory for those out of current mapset?
            src_mapset_name = gs.gisenv()['MAPSET']
        image_file_name = pure_map_name + '.png'
        image_file_path = os.path.join(out_dir, image_file_name)
        # TODO: skip writing to file and extract the information from
        # function, or use object if function is so large
        wgs84_file = image_file_path + '.wgs84'
        export_png_in_projection(map_name=map_name,
                                 src_mapset_name=src_mapset_name,
                                 output_file=image_file_path,
                                 epsg_code=epsg,
                                 compression=compression,
                                 routpng_flags=routpng_flags,
                                 wgs84_file=wgs84_file,
                                 use_region=True)

        data_file.write(pure_map_name + ',' + image_file_name + '\n')

        # it doesn't matter in which location we are, it just uses the current
        # location, not tested for LL loc, assuming that to be nop.
        map_extent = get_map_extent_for_file(wgs84_file)
        bounds = map_extent_to_js_leaflet_list(map_extent)

        extra_attributes = []

        generate_infos(map_name=map_name,
                       projected_png_file=image_file_path,
                       required_infos=infos,
                       output_directory=out_dir,
                       attributes=extra_attributes)
        # http://www.w3schools.com/js/js_objects.asp
        js_data_file.write("""   {{title: "{title}", file: "{file_}","""
                           """ bounds: {bounds}, opacity: {opacity}"""
                           .format(title=pure_map_name,
                                   file_=image_file_name,
                                   bounds=bounds,
                                   opacity=opacities[i]))
        if extra_attributes:
            extra_js_attributes = [pair[0] + ': "' +
                                   escape_quotes(
                                       escape_endlines(
                                           escape_backslashes(
                                               pair[1]
                                           ))) + '"'
                                   for pair in extra_attributes]
            js_data_file.write(', ' + ', '.join(extra_js_attributes))
        js_data_file.write("""}\n""")
        # do not write after the last item
        if i < num_maps - 1:
            js_data_file.write(',')
    js_data_file.write('];\n')
    data_file.close()


if __name__ == '__main__':
    sys.exit(main())
