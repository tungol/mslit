#!/usr/bin/env python
# encoding: utf-8

"""
High level wrappers around IRAF functions.

wrappers: apsum_galaxy, calibrate_galaxy, dispcor_galaxy, fix_galaxy
          imcopy_galaxy, init_galaxy, rotate_galaxy, setairmass_galaxy
          slice_galaxy, zero_flats
"""

import os
import os.path
from .data import get, get_group, get_groups, get_object_spectra
from .data import get_sky_spectra, init_data
from .iraf_low import apsum, calibrate, dispcor, hedit, imcopy, fixpix, ccdproc
from .iraf_low import rotate, combine, zerocombine, flatcombine
from .misc import list_convert, namefix, zerocount


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
