#!/usr/bin/env python
# encoding: utf-8

import os
from argparse import ArgumentParser
from iraf_base import apsum, calibrate, ccdproc, combine, dispcor, flatcombine
from iraf_base import fixpix, hedit, imcopy, rotate, setairmass, zerocombine
from iraf_base import sarith, scombine
from iraf_base import list_convert, namefix
from misc import zerocount
from sky import generate_sky, sky_subtract
from data import init_data, get_groups, get_object_spectra, get, get_group
from data import get_sky_spectra, write

## Higher level IRAF wrappers ##


def apsum_galaxy(name):
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


def calibrate_galaxy(name, standard):
    """Calibrates all spectra in name with the standard specified"""
    if not os.path.isdir('%s/cal' % name):
        os.mkdir('%s/cal' % name)
    sens = '%s/sens' % standard
    spectra = get_object_spectra(name)
    for spectrum in spectra:
        num = zerocount(spectrum)
        calibrate('%s/sub/%s.1d' % (name, num), sens,
            '%s/cal/%s.1d' % (name, num))


def combine_sky_spectra(name):
    group = get_group(name)
    use = group['galaxy']
    sky_list = get_sky_spectra(name)
    sizes = get(name, 'sizes')
    flist = []
    for spectra in sky_list:
        scale = sizes[spectra]
        num = zerocount(spectra)
        sarith('%s/disp/%s.1d' % (use, num), '/', scale,
            '%s/sky/%s.scaled' % (name, num))
        flist.append('%s/sky/%s.scaled' % (name, num))
    scombine(list_convert(flist), '%s/sky.1d' % name)


def dispcor_galaxy(name, use=None):
    if not use:
        use = name
    if not os.path.isdir('%s/disp' % name):
        os.mkdir('%s/disp' % name)
    spectra = get_object_spectra(name) + get_sky_spectra(name)
    for spectrum in spectra:
        num = zerocount(spectrum)
        hedit('%s/sum/%s.1d' % (name, num), 'REFSPEC1',
            '%s/sum/%sc.1d' % (use, num))
        dispcor('%s/sum/%s.1d' % (name, num),
            '%s/disp/%s.1d' % (name, num))


def fix_galaxy(name, mask):
    imcopy('@lists/%s' % name, '%s/' % name)
    with open('lists/%s' % name) as f:
        items = ['%s/%s' % (name, item.strip()) for item in f.readlines()]
    strlist = list_convert(items)
    hedit(strlist, 'BPM', mask)
    fixpix(strlist, 'BPM', verbose='yes')


def imcopy_galaxy(name):
    if not os.path.isdir('%s/slice' % name):
        os.mkdir('%s/slice' % name)
    sections = get(name, 'sections')
    for i, section in enumerate(sections):
        num = zerocount(i)
        imcopy('%s/rot/%s%s' % (name, num, section),
            '%s/slice/%s' % (name, num))
        imcopy('%s/rot/%sc%s' % (name, num, section),
            '%s/slice/%sc' % (name, num))


def init_galaxy(name, mask, zero, flat):
    """Applies a bad pixel mask to all the images associated with name,
    then runs ccdproc and combine"""
    if not os.path.isdir(name):
        os.mkdir(name)
    fix_galaxy(name, mask)
    with open('lists/%s' % name) as f:
        items = ['%s/%s' % (name, item.strip()) for item in f.readlines()]
    ccdproc(list_convert(items), zero=zero, flat=flat)
    combine(list_convert(items), '%s/base' % name)


def rotate_galaxy(name, comp):
    if not os.path.isdir('%s/rot' % name):
        os.mkdir('%s/rot' % name)
    angles = get(name, 'angles')
    for i, angle in enumerate(angles):
        num = zerocount(i)
        rotate('%s/base' % name, '%s/rot/%s' % (name, num), angle)
        rotate('@lists/%s' % comp, '%s/rot/%sc' % (name, num), angle)


def setairmass_galaxy(name):
    spectra = get_object_spectra(name)
    for spectrum in spectra:
        num = zerocount(spectrum)
        setairmass('%s/sub/%s.1d' % (name, num))


def skies(name, lines):
    """Create a combined sky spectra, sky subtracts all object spectra,
    and sets airmass metadata"""
    if not os.path.isdir('%s/sky' % name):
        os.mkdir('%s/sky' % name)
    combine_sky_spectra(name)
    if not os.path.isdir('%s/sub' % name):
        os.mkdir('%s/sub' % name)
    sky_subtract_galaxy(name, lines)
    setairmass_galaxy(name)


def sky_subtract_galaxy(name, lines):
    spectra = get_object_spectra(name)
    sky_levels = get(name, 'sky')
    for spectrum in spectra:
        sky_level = sky_levels[spectrum]
        if not sky_level:
            sky_level = sky_subtract(name, spectrum, sky, lines)
        generate_sky(name, spectrum, sky_level)
    write(name, 'sky', sky_levels)


def slice_galaxy(name, comp):
    """Separates the individuals slices of a galaxy out,
    and creates one dimensional spectra"""
    init_data(name)
    rotate_galaxy(name, comp)
    imcopy_galaxy(name)
    apsum_galaxy(name)
    #needed for next step
    try:
        os.makedirs('database/id%s/sum' % name)
    except OSError:
        pass


def zero_flats(mask, zeros, flats):
    """This function combines the zeros and flats for a night,
    then applies the bad pixel mask specified."""
    for zero in zeros:
        zerocombine('@lists/%s' % zero, output='%s.fits' % zero)
        hedit(zero, 'BPM', mask)
        fixpix(zero, 'BPM', verbose='yes')
    for flat in flats:
        flatcombine('@lists/%s' % flat, output='%s.fits' % flat)
        hedit(flat, 'BPM', mask)
        fixpix(flat, 'BPM', verbose='yes')


## Top level functions ##

def init(groups):
    zeros = []
    flats = []
    for group in groups:
        if group['zero'] not in zeros:
            zeros.append(group['zero'])
        if group['flat'] not in flats:
            flats.append(group['flat'])
    # note: this takes the mask from the first group, will cause problems if
    # a single night needs more than one mask.
    zero_flats(groups[0]['mask'], zeros, flats)
    for group in groups:
        init_galaxy(group['galaxy'], group['mask'], group['zero'],
                    group['flat'])
        init_galaxy(group['star'], group['mask'], group['zero'], group['flat'])


def crop(groups):
    for group in groups:
        slice_galaxy(group['galaxy'], group['lamp'])
        slice_galaxy(group['star'], group['lamp'])


def disp(groups):
    for group in groups:
        dispcor_galaxy(group['galaxy'])
        dispcor_galaxy(group['star'], use=group['galaxy'])


def sky(groups):
    lines = [5893, 5578, 6301, 6365]
    for group in groups:
        skies(group['galaxy'], lines)
        skies(group['star'], lines)


def calibration(groups):
    for group in groups:
        calibrate_galaxy(group['galaxy'], group['star'])


## Program structure ##

def main(command, path):
    commands = {'init': init, 'slice': crop, 'disp': disp,
                'sky': sky, 'calibrate': calibration}
    os.chdir(path)
    groups = get_groups()
    commands[command](groups)


def parse_args():
    parser = ArgumentParser(description='')
    parser.add_argument('command')
    parser.add_argument('path')
    return vars(parser.parse_args())

if __name__ == '__main__':
    args = parse_args()
    main(args['command'], args['path'])
