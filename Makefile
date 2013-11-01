MODULE_TOPDIR =../..

PGM = r.out.leaflet

SUBDIRS = \
          r.out.leaflet \
          r.out.png.proj \
          routleaflet

include $(MODULE_TOPDIR)/include/Make/Dir.make

default: parsubdirs htmldir

install: installsubdirs

