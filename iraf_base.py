#!/usr/bin/env python
# encoding: utf-8

"""
iraf.py - contains wrappers around IRAF functions

In this file there are functions for loading specific IRAF packages,
wrappers around basic functions found in those packages, and some
miscelaneous functions that smooth over the interface to IRAF.

loaders: load_apextract, load_ccdred, load_imgeom, load_kpnoslit,
         load_onedspec
wrappers: apsum, calibrate, ccdproc, combine, dispcor, flatcombine, fixpix,
          hedit, imcopy, rotate, sarith, scombine, setairmass, zerocombine
misc: namefix, list_convert, set_aperture

All function wrappers can be passed arbitrary key values which will be
passed on to the corresponding IRAF function.
"""

import pyraf.iraf
import os
import os.path

## Wrappers for loading IRAF packages ##


def load_apextract():
    """Load the apextract package."""
    pyraf.iraf.noao(_doprint=0)
    pyraf.iraf.twodspec(_doprint=0)
    pyraf.iraf.apextract(_doprint=0)


def load_ccdred():
    """Load the ccdred package."""
    pyraf.iraf.noao(_doprint=0)
    pyraf.iraf.imred(_doprint=0)
    pyraf.iraf.ccdred(_doprint=0)


def load_imgeom():
    """Load the imgeom package."""
    pyraf.iraf.images(_doprint=0)
    pyraf.iraf.imgeom(_doprint=0)


def load_kpnoslit():
    """Load the kpnoslit package."""
    pyraf.iraf.imred(_doprint=0)
    pyraf.iraf.kpnoslit(_doprint=0)


def load_onedspec():
    """Load the onedspec package."""
    pyraf.iraf.noao(_doprint=0)
    pyraf.iraf.onedspec(_doprint=0)

## Wrappers around IRAF functions ##


def apsum(infiles, outfiles, section, **kwargs):
    """Call the apsum function from the apextract package, creating the
       apeture automatically and setting some defaults appropriately."""
    load_apextract()
    set_aperture(infiles, section)
    kwargs.setdefault('format', 'onedspec')
    kwargs.setdefault('interactive', 'no')
    kwargs.setdefault('find', 'no')
    kwargs.setdefault('trace', 'no')
    kwargs.setdefault('fittrace', 'no')
    pyraf.iraf.apsum.unlearn()
    pyraf.iraf.apsum(input=infiles, output=outfiles, **kwargs)


def calibrate(infiles, sens, outfiles, **kwargs):
    """Call the calibrate function from the kpnoslit package."""
    load_kpnoslit()
    pyraf.iraf.calibrate.unlearn()
    pyraf.iraf.calibrate(input=infiles, output=outfiles, sens=sens, **kwargs)


def ccdproc(images, **kwargs):
    """Call the ccdproc function from the ccdred package,
       with some defaults set appropriately."""
    load_ccdred()
    kwargs.setdefault('darkcor', 'no')
    kwargs.setdefault('fixpix', 'no')
    kwargs.setdefault('biassec', '[2049:2080,1:501]')
    kwargs.setdefault('trimsec', '[1:2048,1:501]')
    pyraf.iraf.ccdproc.unlearn()
    pyraf.iraf.ccdproc(images=images, **kwargs)


def combine(infiles, outfiles, **kwargs):
    """Call the combine function from the ccdred package."""
    load_ccdred()
    pyraf.iraf.combine.unlearn()
    pyraf.iraf.combine(input=infiles, output=outfiles, **kwargs)


def dispcor(infiles, outfiles, **kwargs):
    """Call the dispcor function from the onedspec package."""
    load_onedspec()
    pyraf.iraf.dispcor.unlearn()
    pyraf.iraf.dispcor(input=infiles, output=outfiles, **kwargs)


def flatcombine(infiles, **kwargs):
    """Call the flatcombine function from the ccdred package."""
    load_ccdred()
    kwargs.setdefault('process', 'no')
    pyraf.iraf.flatcombine.unlearn()
    pyraf.iraf.flatcombine(input=infiles, **kwargs)


def fixpix(image, mask, **kwargs):
    """Call the fixpix function from the core IRAF package."""
    pyraf.iraf.fixpix.unlearn()
    pyraf.iraf.fixpix(images=image, masks=mask, **kwargs)


def hedit(images, fields, value, **kwargs):
    """Add a field to a file's header using the hedit function."""
    kwargs.setdefault('add', 'yes')
    kwargs.setdefault('verify', 'no')
    pyraf.iraf.hedit.unlearn()
    pyraf.iraf.hedit(images=images, fields=fields, value=value, **kwargs)


def imcopy(infiles, outfiles, **kwargs):
    """Call the imcopy function from the core IRAF package."""
    pyraf.iraf.imcopy.unlearn()
    pyraf.iraf.imcopy(input=infiles, output=outfiles, **kwargs)


def rotate(infiles, outfiles, angle, **kwargs):
    """Call the rotate function from the imgeom package."""
    load_imgeom()
    pyraf.iraf.rotate.unlearn()
    pyraf.iraf.rotate(input=infiles, output=outfiles, rotation=-angle,
                      **kwargs)


def sarith(infile1, op, infile2, outfile, **kwargs):
    """Call the sarith function from the onedspec package."""
    load_onedspec()
    pyraf.iraf.sarith.unlearn()
    pyraf.iraf.sarith(input1=infile1, op=op, input2=infile2, output=outfile,
        **kwargs)


def scombine(infiles, outfiles, **kwargs):
    """Call the scombine function from the onedspec package."""
    load_onedspec()
    pyraf.iraf.scombine.unlearn()
    pyraf.iraf.scombine(input=infiles, output=outfiles, **kwargs)


def setairmass(images, **kwargs):
    """Call the setairmass function from the kpnoslit package."""
    load_kpnoslit()
    pyraf.iraf.setairmass.unlearn()
    pyraf.iraf.setairmass(images=images, **kwargs)


def zerocombine(infiles, **kwargs):
    """Call the zerocombine function from the ccdred package."""
    load_ccdred()
    pyraf.iraf.zerocombine.unlearn()
    pyraf.iraf.zerocombine(input=infiles, **kwargs)


## Miscelaneous ##

## Functions to smooth over the interface to IRAF ##


def namefix(name):
    """Rename files to get rid of the silly naming scheme that apsum uses."""
    os.rename('%s.0001.fits' % name, '%s.fits' % name)


def list_convert(pylist):
    """Convert python lists to the strings that IRAF accepts as lists."""
    stringlist = pylist[0]
    for item in pylist[1:]:
        stringlist += ', %s' % item
    return stringlist


def set_aperture(infile, section):
    """Create an aperture definition file for apsum to use."""
    # section is [left:right,down:up]
    column = section[1:-1].split(',')[1]
    (down, up) = column.split(':')
    center = (float(up) - float(down) + 1) / 2.
    rup = center
    rdown = -center
    tmp = []
    # details here obtained through reverse engineering of aperture files
    # generated by IRAF
    tmp.append('begin\taperture %s 1 1024. %s\n' % (infile, center))
    tmp.append('\timage\t%s\n' % infile)
    tmp.append('\taperture\t1\n')
    tmp.append('\tbeam\t1\n')
    tmp.append('\tcenter\t1024. %s\n' % center)
    tmp.append('\tlow\t-1023. %s\n' % rdown)
    tmp.append('\thigh\t1024. %s\n' % rup)
    tmp.append('\tbackground\n')
    tmp.append('\t\txmin -10.\n')
    tmp.append('\t\txmax 10.\n')
    tmp.append('\t\tfunction chebyshev\n')
    tmp.append('\t\torder 1\n')
    tmp.append('\t\tsample -10:-6,6:10\n')
    tmp.append('\t\tnaverage -3\n')
    tmp.append('\t\tniterate 0\n')
    tmp.append('\t\tlow_reject 3.\n')
    tmp.append('\t\thigh_reject 3.\n')
    tmp.append('\t\tgrow 0.\n')
    tmp.append('\taxis\t2\n')
    tmp.append('\tcurve\t5\n')
    tmp.append('\t\t2.\n')
    tmp.append('\t\t1.\n')
    tmp.append('\t\t1.\n')
    tmp.append('\t\t2048.\n')
    tmp.append('\t\t0.\n')
    tmp.append('\n')
    if not os.path.isdir('./database'):
        os.mkdir('./database')
    with open('./database/ap%s' % infile.replace('/', '_'), 'w') as f:
        f.writelines(tmp)
