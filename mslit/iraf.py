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

from __future__ import with_statement
import pyraf.iraf
import os
import os.path
from .data import get, get_object_spectra, get_group, get_sky_spectra, write
from .data import init_data, get_groups
from .misc import zerocount
from .sky import sky_subtract, generate_sky

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


## Higher level IRAF wrappers ##


def apsum_galaxy(name):
    """Create one dimensional spectra for a galaxy."""
    sections = get(name, 'sections')
    if not os.path.isdir('%s/sum' % name):
        os.mkdir('%s/sum' % name)
    for i, section in enumerate(sections):
        num = zerocount(i)
        apsum('%s/slice/%s' % (name, num),
              '%s/sum/%s.1d' % (name, num), section)
        apsum('%s/slice/%sc' % (name, num),
              '%s/sum/%sc.1d' % (name, num), section)
        namefix('%s/sum/%s.1d' % (name, num))
        namefix('%s/sum/%sc.1d' % (name, num))


def calibrate_galaxy(name):
    """Flux calibrate all object spectra in a galaxy."""
    group = get_group(name)
    if not os.path.isdir('%s/cal' % name):
        os.mkdir('%s/cal' % name)
    sens = '%s/sens' % group['star']
    spectra = get_object_spectra(name)
    for spectrum in spectra:
        num = zerocount(spectrum)
        calibrate('%s/sub/%s.1d' % (name, num), sens,
            '%s/cal/%s.1d' % (name, num))


def combine_sky_spectra(name):
    """Convert all sky spectra to the same scaling, then combine them."""
    sky_list = get_sky_spectra(name)
    sizes = get(name, 'sizes')
    scaled = []
    for spectra in sky_list:
        scale = sizes[spectra] # scale by the number of pixels arcoss
        num = zerocount(spectra)
        sarith('%s/disp/%s.1d' % (name, num), '/', scale,
            '%s/sky/%s.scaled' % (name, num))
        scaled.append('%s/sky/%s.scaled' % (name, num))
    if os.path.isfile('%s/sky.1d' % name):
        os.remove('%s/sky.1d' % name)
    scombine(list_convert(scaled), '%s/sky.1d' % name)


def dispcor_galaxy(name):
    """Apply dispersion correction to all spectra in a galaxy."""
    group = get_group(name)
    use = group['galaxy']
    if not os.path.isdir('%s/disp' % name):
        os.mkdir('%s/disp' % name)
    spectra = set(get_object_spectra(name) + get_sky_spectra(name))
    for spectrum in spectra:
        num = zerocount(spectrum)
        hedit('%s/sum/%s.1d' % (name, num), 'REFSPEC1',
            '%s/sum/%sc.1d' % (use, num))
        dispcor('%s/sum/%s.1d' % (name, num),
            '%s/disp/%s.1d' % (name, num))


def fix_galaxy(name):
    """Apply a bad pixel mask to all images in a galaxy."""
    group = get_group(name)
    imcopy('@lists/%s' % name, '%s/' % name)
    with open('lists/%s' % name) as f:
        items = ['%s/%s' % (name, item.strip()) for item in f.readlines()]
    strlist = list_convert(items)
    hedit(strlist, 'BPM', group['mask'])
    fixpix(strlist, 'BPM')


def imcopy_galaxy(name):
    """Create cropped images for all sections in a galaxy."""
    if not os.path.isdir('%s/slice' % name):
        os.mkdir('%s/slice' % name)
    sections = get(name, 'sections')
    for i, section in enumerate(sections):
        num = zerocount(i)
        imcopy('%s/rot/%s%s' % (name, num, section),
            '%s/slice/%s' % (name, num))
        imcopy('%s/rot/%sc%s' % (name, num, section),
            '%s/slice/%sc' % (name, num))


def init_galaxy(name):
    """Apply a bad pixel mask, then run ccdproc and combine."""
    group = get_group(name)
    if not os.path.isdir(name):
        os.mkdir(name)
    fix_galaxy(name)
    with open('lists/%s' % name) as f:
        items = ['%s/%s' % (name, item.strip()) for item in f.readlines()]
    ccdproc(list_convert(items), zero=group['zero'], flat=group['flat'])
    combine(list_convert(items), '%s/base' % name)


def rotate_galaxy(name):
    """Create a rotated image for every spectra in a galaxy."""
    group = get_group(name)
    if not os.path.isdir('%s/rot' % name):
        os.mkdir('%s/rot' % name)
    angles = get(name, 'angles')
    for i, angle in enumerate(angles):
        num = zerocount(i)
        rotate('%s/base' % name, '%s/rot/%s' % (name, num), angle)
        rotate('@lists/%s' % group['lamp'], '%s/rot/%sc' % (name, num), angle)


def setairmass_galaxy(name):
    """Set effective air mass for each object spectra in a galaxy."""
    spectra = get_object_spectra(name)
    for spectrum in spectra:
        num = zerocount(spectrum)
        setairmass('%s/sub/%s.1d' % (name, num))


def skies(name):
    """Create a combined sky spectrum, perform sky subtraction, and set
       airmass metadata """
    if not os.path.isdir('%s/sky' % name):
        os.mkdir('%s/sky' % name)
    combine_sky_spectra(name)
    if not os.path.isdir('%s/sub' % name):
        os.mkdir('%s/sub' % name)
    sky_subtract_galaxy(name)
    setairmass_galaxy(name)


def sky_subtract_galaxy(name):
    """Remove sky lines from each spectra in a galaxy, making a guess at an
       appropriate scaling level if none is stored already."""
    spectra = get_object_spectra(name)
    sky_levels = get(name, 'sky')
    for spectrum in spectra:
        sky_level = sky_levels[spectrum]
        if not sky_level:
            sky_level = sky_subtract(name, spectrum)
        generate_sky(name, spectrum, sky_level)
    write(name, 'sky', sky_levels)


def slice_galaxy(name):
    """Create one dimensional spectra for a galaxy."""
    init_data(name)
    rotate_galaxy(name)
    imcopy_galaxy(name)
    apsum_galaxy(name)
    # needed for next step
    try:
        os.makedirs('database/id%s/sum' % name)
    except OSError:
        pass


def zero_flats():
    """Combine the zeros and flats for a night, then apply a bad pixel mask."""
    groups = get_groups()
    done = []
    for group in groups:
        if group['zero'] not in done:
            done.append(group['zero'])
            zerocombine('@lists/%s' % group['zero'], output=group['zero'])
            hedit(group['zero'], 'BPM', group['mask'])
            fixpix(group['zero'], 'BPM')
        if group['flat'] not in done:
            done.append(group['flat'])
            flatcombine('@lists/%s' % group['flat'], output=group['flat'])
            hedit(group['flat'], 'BPM', group['mask'])
            fixpix(group['flat'], 'BPM')
