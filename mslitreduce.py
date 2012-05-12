#!/usr/bin/env python
# encoding: utf-8

import os, subprocess
from argparse import ArgumentParser
from iraf import ccdproc, combine, zerocombine, flatcombine, fixpix
from iraf import apsum, dispcor, imcopy, hedit, rotate, setairmass
from iraf import list_convert
from sky import combine_sky_spectra, generate_sky, regenerate_sky
from data import init_data, set_obj, get_groups, get_data, write_data
from generic import zerocount


## Functions to smooth over the interface to IRAF ##

def namefix(name):
    """Rename files to get rid of silly naming scheme of apsum"""
    os.rename('%s.0001.fits' % name, '%s.fits' % name)

def fix_image(image, mask):
    """Apply a bad pixel mask to an image"""
    hedit(image, 'BPM', mask)
    fixpix(image, 'BPM', verbose='yes')


## Functions that wrap IRAF functions, applied across many items at once ##

def apsum_galaxy(name):
    data = get_data(name)
    os.mkdir('%s/sum' % name)
    for i, item in enumerate(data):
        num = zerocount(i)
        apsum('%s/slice/%s' % (name, num), 
            '%s/sum/%s.1d' % (name, num), item['section'])
        apsum('%s/slice/%sc' % (name, num), 
            '%s/sum/%sc.1d' % (name, num), item['section'])
        namefix('%s/sum/%s.1d' % (name, num))
        namefix('%s/sum/%sc.1d' % (name, num))

def calibrate_galaxy(name, standard):
    """Calibrates all spectra in name with the standard specified"""
    os.mkdir('%s/cal' % name)
    data = get_data(name)
    sens = '%s/sens' % standard
    for i, item in enumerate(data):
        num = zerocount(i)
        calibrate('%s/sub/%s.1d' % (name, num), sens, 
            '%s/cal/%s.1d' % (name, num))

def dispcor_galaxy(name, use=None):
    os.mkdir('%s/disp' % name)
    hedit_galaxy(name, use=use)
    data = get_data(name)
    for i, item in enumerate(data):
        num = zerocount(i)
        dispcor('%s/sum/%s.1d' % (name, num), 
            '%s/disp/%s.1d' % (name, num))

def fix_galaxy(name, mask):
    imcopy('@lists/%s' % name, '%s/' % name)
    with open('lists/%s' % name) as f:
        items = ['%s/%s' % (name, item) for item in f.readlines()]
    fix_image(list_convert(items), mask)

def hedit_galaxy(name, use=None):
    data = get_data(name)
    if not use:
        use = name
    for i, item in enumerate(data):
        num = zerocount(i)
        hedit('%s/sum/%s.1d' % (name, num), 'REFSPEC1', 
            '%s/sum/%sc.1d' % (use, num))

def imcopy_galaxy(name):
    data = get_data(name)
    os.mkdir('%s/slice' % name)
    for i, item in enumerate(data):
        num = zerocount(i)
        imcopy('%s/rot/%s%s' % (name, num, item['section']), 
            '%s/slice/%s' % (name, num))
        imcopy('%s/rot/%sc%s' % (name, num, item['section']), 
            '%s/slice/%sc' % (name, num))

def init_galaxy(name, mask, zero, flat):
    """Applies a bad pixel mask to all the images associated with name, 
    then runs ccdproc and combine"""
    try:
        os.mkdir(name)
    except OSError:
        pass
    fix_galaxy(name, mask)
    with open('lists/%s' % name) as f:
        items = ['%s/%s' % (name, item) for item in f.readlines()]
    ccdproc(list_convert(items), zero=zero, flat=flat)
    combine(list_convert(items), '%s/base' % name)

def rotate_galaxy(name, comp):
    data = get_data(name)
    try:
        os.mkdir('%s/rot' % name)
    except:
        pass
    for i, item in enumerate(data):
        num = zerocount(i)
        rotate('%s/base' % name, '%s/rot/%s' % (name, num), 
            item['angle'])
        rotate('@lists/%s' % comp, '%s/rot/%sc' % (name, num), 
            item['angle'])

def setairmass_galaxy(name):
    data = get_data(name)
    for i, item in enumerate(data):
        num = zerocount(i)
        if item['type'] == 'HIIREGION':
            setairmass('%s/sub/%s.1d' % (name, num))

def skies(name, lines, use=None, obj=None):
    """Create a combined sky spectra, sky subtracts all object spectra, 
    and sets airmass metadata"""
    if obj:
        set_obj(name, obj)
    os.mkdir('%s/sky' % name)
    combine_sky_spectra(name, use=use)
    os.mkdir('%s/sub' % name)
    sky_subtract_galaxy(name, lines)
    setairmass_galaxy(name)

def sky_subtract_galaxy(name, lines):
    data = get_data(name)
    os.mkdir('%s/tmp' % name)
    for i, item in enumerate(data):
        if item['type'] == 'HIIREGION':
            if item.has_key('sky_level'):
                regenerate_sky(name, item)
            else:
                generate_sky(name, item, lines)
    write_data(name, data)
    subprocess.call(['rm', '-rf', '%s/tmp' % name])

def slice_galaxy(name, comp, use=None):
    """Separates the individuals slices of a galaxy out, 
    and creates one dimensional spectra"""
    init_data(name, use=use)
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
        zerocombine('@lists/%s' % zero, output = '%s.fits' % zero)
        fix_image(zero, mask)
    for flat in flats:
        flatcombine('@lists/%s' % flat, output = '%s.fits' % flat)
        fix_image(flat, mask)


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
        init_galaxy(group['galaxy'], group['mask'], group['zero'], group['flat'])
        init_galaxy(group['star'], group['mask'], group['zero'], group['flat'])

def slice(groups):
    for group in groups:
        slice_galaxy(group['galaxy'], group['lamp'])
        slice_galaxy(group['star'], group['lamp'], use=group['galaxy'])

def disp(groups):
    for group in groups:
        dispcor_galaxy(group['galaxy'])
        dispcor_galaxy(group['star'], use=group['galaxy'])

def sky(groups):
    lines = [5893, 5578, 6301, 6365]
    for group in groups:
        skies(group['galaxy'], lines)
        skies(group['star'], lines, obj=group['star_num'])

def calibrate(groups):
    for group in groups:
        calibrate_galaxy(group['galaxy'], group['star'])


## Program structure ##

def main(command, path):
    groups = get_groups(path)
    commands = {'init': init, 'slice': slice, 'disp': disp,
                'sky': sky, 'calibrate': calibrate}
    os.chdir(path)
    commands[command](groups)

def parse_args():
    parser = ArgumentParser(description='')
    parser.add_argument('command')
    parser.add_argument('path')
    return vars(parser.parse_args())

if __name__ == '__main__':
    args = parse_args()
    main(args['command'], args['path'])
