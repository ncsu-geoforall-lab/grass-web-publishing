# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 12:15:37 2013

@author: Vaclav Petras
"""

import os

import grass.script as gs


def set_rendering_environment(width, height, filename, transparent,
                              backgroud_color='ffffff', driver='cairo',
                              compression=None, env=None):
    # if parameter not provided (but allow for empty dictionary)
    if env is None:
        env = os.environ
    env['GRASS_RENDER_WIDTH'] = str(width)
    env['GRASS_RENDER_HEIGHT'] = str(height)
    env['GRASS_RENDER_IMMEDIATE'] = driver
    env['GRASS_RENDER_BACKGROUNDCOLOR'] = backgroud_color
    env['GRASS_RENDER_TRUECOLOR'] = "TRUE"
    if transparent:
        env['GRASS_RENDER_TRANSPARENT'] = "TRUE"
    else:
        env['GRASS_RENDER_TRANSPARENT'] = "FALSE"
    if compression:
        env['GRASS_RENDER_FILE_COMPRESSION'] = str(compression)
    env['GRASS_RENDER_FILE'] = str(filename)


def export_legend(mapname, filename, width, height):
    # using png driver but need to set bg color if we want transparency
    # otherwise png driver will set pixels to ffffff and PIL will
    # not crop the legend
    set_rendering_environment(width, height, filename, transparent=True,
                              backgroud_color='000000',
                              driver='png')
    gs.run_command('d.legend', raster=mapname)
    try:
        from PIL import Image
        image = Image.open(filename)
        imageBox = image.getbbox()
        cropped_image = image.crop(imageBox)
        cropped_image.save(filename, 'PNG')
    except ImportError as error:
        gs.warning(_("Cannot crop legend image ({error})."
                     " Maybe you don't have PIL."
                     " Uncropped legend image will be used.") % error)


def export_histogram(mapname, filename, width, height, style='bar'):
    # using png driver to be sure that it works for ms windows
    set_rendering_environment(width, height, filename, transparent=True,
                              driver='png')
    gs.run_command('d.histogram', map=mapname, style=style)


def export_info(mapname, filename):
    output = gs.read_command('r.info', map=mapname)
    with open(filename, 'w') as output_file:
        output_file.write(output)


def export_statistics(mapname, filename):
    gs.run_command('r.univar', flags='e', map=mapname, output=filename)


def thumbnail_image(input_file, output_file):
    try:
        import Image
        image = Image.open(input_file)
        image.thumbnail((200, 200), Image.ANTIALIAS)
        image.save(output_file, 'PNG')
    except ImportError as error:
        gs.warning(_("Cannot thumbnail image ({error})."
                     " Maybe you don't have PIL.") % error)


def export_raster_as_geotiff(mapname, filename):
    gs.run_command('r.out.tiff', input=mapname, output=filename)


def export_raster_packed(mapname, filename):
    gs.run_command('r.pack', input=mapname, output=filename)
