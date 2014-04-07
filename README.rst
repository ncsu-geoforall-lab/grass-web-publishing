GRASS module r.out.leaflet and related tools
============================================

GRASS module r.out.leaflet, r.out.png.proj and other tools related to
the export of GRASS data to the form which can be used by a Leaflet
web page, i.e. easily imported used from JavaScript code.


TODO
----

* work for computational region as well as for map extent
* document Python functions
* create manual pages
* describe output structure
* generate manuals and publish them using GitHub pages
* better error handling (return codes of modules should be checked)
* solve the overwrite behavior (according to directory structure)
* use map titles for large maps (perhaps in separate module)
* apply region extent only to maps same or bigger than region (use map extent for small maps)
* apply map resolution when computational region's is too fine for map (may cause problems for Leaflet)
* separate option of resolution (must be same for ns ew)
* crop thumbnail?
* export (and import/external?) of QGIS project file including the data files (GeoTIFF, ...)
* extract functions for switching the location (consider usage of ``with`` statement)


Authors
-------

Vaclav Petras, wenzeslaus gmail com, NCSU OSGeoREL


License
-------

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

If you not have received a copy of the GNU General Public License
along with this program, see http://www.gnu.org/licenses/.

