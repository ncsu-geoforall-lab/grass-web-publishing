# -*- coding: utf-8 -*-
"""
Created on Tue Nov 26 12:15:37 2013

@author: Vaclav Petras
"""

import os

import grass.script.core as gcore


def _setEnvironment(width, height, filename, transparent, driver='cairo'):
    os.environ['GRASS_WIDTH'] = str(width)
    os.environ['GRASS_HEIGHT'] = str(height)
    os.environ['GRASS_RENDER_IMMEDIATE'] = driver
    os.environ['GRASS_BACKGROUNDCOLOR'] = 'ffffff'
    os.environ['GRASS_TRUECOLOR'] = "TRUE"
    if transparent:
        os.environ['GRASS_TRANSPARENT'] = "TRUE"
    else:
        os.environ['GRASS_TRANSPARENT'] = "FALSE"
    os.environ['GRASS_PNGFILE'] = str(filename)


def _read2_command(*args, **kwargs):
    kwargs['stdout'] = gcore.PIPE
    kwargs['stderr'] = gcore.PIPE
    ps = gcore.start_command(*args, **kwargs)
    stdout, stderr = ps.communicate()
    return ps.returncode, stdout, stderr


def export_histogram(mapname, filename, width, height, style='bar'):
    # using png driver to be sure that it works for ms windows
    _setEnvironment(width, height, filename, transparent=True, driver='png')
    returncode, stdout, messages = _read2_command('d.histogram',
                                                  map=mapname, style=style)


def export_statistics(mapname, filename):
    gcore.run_command('r.univar', flags='e', map=mapname, output=filename)


def thumbnail_image(input_file, output_file):
    print input_file, output_file
    try:
        import Image
        image = Image.open(input_file)
        image.thumbnail((200, 200), Image.ANTIALIAS)
        image.save(output_file, 'PNG')
    except ImportError, error:
        gcore.warning(_("Cannot thumbnail image ({error})."
                        " Maybe you don't have PIL."
                        " Will output the same image.") % error)

def export_raster_as_geotiff(mapname, filename):
    gcore.run_command('r.out.tiff', input=mapname, output=filename)


def export_raster_packed(mapname, filename):
    gcore.run_command('r.pack', input=mapname, output=filename)
