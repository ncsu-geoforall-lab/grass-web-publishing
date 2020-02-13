# -*- coding: utf-8 -*-
"""
Created on Fri Nov 29 19:28:54 2013

@author: Vaclav Petras <wenzeslaus gmail.com>
"""


import os
import copy
import shutil

import grass.script as gs


def get_region():
    """Returns current computational region as dictionary.

    Adds long key names.
    """
    region = gs.region()
    region['east'] = region['e']
    region['west'] = region['w']
    region['north'] = region['n']
    region['south'] = region['s']
    return region


def set_region(region):
    """Sets the current computational region from a dictionary.

    Accepts long key names and removes key from ``grass.script.region()``
    which are not useful for setting the region.
    """
    region = copy.copy(region)
    if 'north' in region:
        # just assuming all
        region['n'] = region['north']
        region['s'] = region['south']
        region['e'] = region['east']
        region['w'] = region['west']
    for key in ['north', 'south', 'east', 'west',
                'zone', 'projection', 'cells']:
        del region[key]
    gs.run_command('g.region', **region)


def get_location_proj_string():
    out = gs.read_command('g.proj', flags='jf')
    return out.strip()


# TODO: this does not take care of resolution (it's just extent)
def reproject_region(region, from_proj, to_proj):
    region = region.copy()
    proj_input = '{east} {north}\n{west} {south}'.format(**region)
    proc = gs.start_command('m.proj', input='-', separator=' , ',
                            proj_in=from_proj, proj_out=to_proj,
                            stdin=gs.PIPE, stdout=gs.PIPE, stderr=gs.PIPE)
    proc.stdin.write(gs.encode(proj_input))
    proc.stdin.close()
    proc.stdin = None
    proj_output, stderr = proc.communicate()
    if proc.returncode:
        raise RuntimeError("reprojecting region: m.proj error: " + stderr)
    enws = gs.decode(proj_output).split(os.linesep)
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


def get_current_mapset(gisrc=None, env=None):
    """Gets the current mapset in the ``gisrc`` file.

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
    return gisenv['GISDBASE'], gisenv['LOCATION_NAME'], gisenv['MAPSET']


# TODO: similar class in GRASS lib/init/grass.py (MapsetSettings)
class Mapset(object):
    """Holds GRASS GIS Database directory, Location name and Mapset name

    Provides few convenient functions.

    It can represent mapset which does not exist, so it can be used for
    mapset manipulation. Only when ``use_current=True`` is used, mapset
    needs to be set in the session (rc file) at the time of object
    creation.

    If ``gisrc`` is not provided, environment variable ``GISRC`` is
    used. The ``env`` parameter can be used to override the system
    (global) environment.
    """
    def __init__(self, database=None, location=None, name=None,
                 use_current=False, gisrc=None, env=None):
        if database and not location:
            raise ValueError(_("If database path is provided, location"
                               " name needs to be provided as well"))
        if location and not name:
            raise ValueError(_("If location name is provided, mapset"
                               " name needs to be provided as well"))
        # current values if requested
        # the source of session information is determined in the function
        if use_current:
            current_database, current_location, current_mapset = \
                get_current_mapset(gisrc=gisrc, env=env)
        # save potential sources of session information for later
        # (to be used in function if appropriate and not overridden)
        self._gisrc = gisrc
        self._env = env
        # use the parameter, or current if requested, or raise error
        if database:
            self.database = database
        else:
            if use_current:
                self.database = current_database
            else:
                raise ValueError(_("Database path cannot be determined"))
        if location:
            self.location = location
        else:
            if use_current:
                self.location = current_location
            else:
                raise ValueError(_("Location name cannot be determined"))
        if name:
            self.name = name
        else:
            if use_current:
                self.name = current_mapset
            else:
                raise ValueError(_("Mapset name cannot be determined"))

    @property
    def mapset_path(self):
        return os.path.join(self.database, self.location, self.name)

    @property
    def location_path(self):
        return os.path.join(self.database, self.location)

    def set_as_current(self, gisrc=None, env=None):
        """Set the this mapset as the current mapset

        If ``gisrc`` is not provided, environment variable ``GISRC`` is
        used. The ``env`` parameter can be used to override the system
        (global) environment.
        """
        # use the saved potential sources of session information
        # when not overridden by one of the parameters
        if not gisrc and not env:
            gisrc = self._gisrc
            env = self._env
        # the source of session information is determined in the function
        set_current_mapset(self.database, self.location, self.name,
                           gisrc=gisrc, env=env)

    def delete(self):
        """Delete the mapset"""
        # TODO: if this would be a general function, we would have to
        # create a policy on what can be deleted, only current should
        # be for writing, but it does not make sense to delete current
        # so maybe any mapset can be deleted with this API
        shutil.rmtree(self.mapset_path)

    # TODO: a simple check, better checks now e.g. in lib/init/grass.py
    def exists(self):
        return os.path.exists(self.mapset_path)
