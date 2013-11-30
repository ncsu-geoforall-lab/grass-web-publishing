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
    return {'east': region['e'], 'north': region['n'],
            'west': region['w'], 'south': region['s'],
            'rows': region['rows'], 'cols': region['cols']}


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
