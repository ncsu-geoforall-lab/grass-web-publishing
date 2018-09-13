# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 19:28:54 2013

@author: Vaclav Petras <wenzeslaus gmail.com>
"""


import os
import copy


from grass.script import core as gcore


def get_region():
    """Returns current computational region as dictionary.

    Uses standardized key names. Outputs only 2D region values which are usable
    for conversion to another location.
    """
    gregion_out = gcore.read_command('g.region', flags='pg')
    region = gcore.parse_key_val(gregion_out, sep='=')
    return {'east': float(region['e']), 'north': float(region['n']),
            'west': float(region['w']), 'south': float(region['s']),
            'rows': int(region['rows']), 'cols': int(region['cols']),
            'nsres': float(region['nsres']),
            'ewres': float(region['ewres'])}


def set_region(region):
    region = copy.copy(region)
    print region
    region['n'] = region['north']
    region['s'] = region['south']
    region['e'] = region['east']
    region['w'] = region['west']
    del region['north']
    del region['south']
    del region['east']
    del region['west']
    if gcore.run_command('g.region', **region):
        raise RuntimeError("Cannot set region.")


def get_location_proj_string():
    out = gcore.read_command('g.proj', flags='jf')
    return out.strip()


def reproject_region(region, from_proj, to_proj):
    region = copy.copy(region)
    print "to reproject:", region
    proj_input = '{east} {north}\n{west} {south}'.format(**region)
    print proj_input
    proc = gcore.start_command('m.proj', input='-', separator=' , ',
                               proj_in=from_proj, proj_out=to_proj,
                               stdin=gcore.PIPE,
                               stdout=gcore.PIPE, stderr=gcore.PIPE)
    proc.stdin.write(proj_input)
    proc.stdin.close()
    proc.stdin = None
    proj_output, stderr = proc.communicate()
    if proc.returncode:
        print from_proj, to_proj, proj_input
        raise RuntimeError("reprojecting region: m.proj error: " + stderr)
    enws = proj_output.split(os.linesep)
    print proj_output
    print enws
    elon, nlat, unused = enws[0].split(' ')
    wlon, slat, unused = enws[1].split(' ')
    region['east'] = elon
    region['north'] = nlat
    region['west'] = wlon
    region['south'] = slat
    return region


def read_env_file(filename):
    keyval = {}
    with open(filename, 'r') as file:
        for line in file:
            # TODO: to generalize, add error handling
            key, value = line.split(':', 1)
            keyval[key.strip()] = value.strip()
    return keyval


def write_env_file(keyval, filename):
    # if this is interrupted, file may be broken
    # (see C implementation (which is not as general as this one))
    # theoretically, this could be solved by generalized g.gisenv
    with open(filename, 'w') as file:
        for key, value in keyval.items():
            file.write("%s: %s\n" % (key, value))


def set_current_mapset(dbase, location, mapset, gisrc=None, env=None):
    """Sets the current mapset in the ``gisrc`` file.

    If ``gisrc`` is not provided, environment variable ``GISRC`` is
    used. The ``env`` parameter can be used to override the system
    (global) environment.
    """
    if not gisrc:
        if env:
            gisrc = env['GISRC']
        else:
            gisrc = os.environ['GISRC']
    gisenv = read_env_file(gisrc)
    gisenv['GISDBASE'] = dbase
    gisenv['LOCATION_NAME'] = location
    gisenv['MAPSET'] = mapset
    write_env_file(gisenv, gisrc)
