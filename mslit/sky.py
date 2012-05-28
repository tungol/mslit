#!/usr/bin/env python
# encoding: utf-8

"""
Functions related to sky subtraction.

high level iraf wrappers: combine_sky_spectra, setairmass_galaxy, skies
                          sky_subtract_galaxy
low level FITS functions: find_line_peak, find_lines, get_continuum,
                          get_peak_cont, get_wavelength_location
functions for solving: get_std_sky, guess_scaling, try_sky
high level functions: generate_sky, modify_sky, sky_subtract
"""

import os
import subprocess
import pyfits
import scipy.optimize
from .data import get, get_object_spectra, get_sky_spectra, write
from .iraf_low import sarith, scombine, setairmass
from .misc import avg, base, list_convert, rms, std, zerocount


# define some atmospheric spectral lines
LINES = [5893, 5578, 6301, 6365]


## High level IRAF wrappers ##

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


## Functions for manipulating the fits data at a low level ##


def find_line_peak(data, location, search):
    """Find the local maximum near a given location. The third option control
       how far on either side of the expected wavelength location to
       consider."""
    search = range(int(location - search), int(location + search))
    values = [data[i] for i in search]
    peak_num = search[values.index(max(values))]
    return peak_num


def find_lines(name, num):
    """Find the locations of a number of sky lines in a FITS file."""
    fn = '%s/disp/%s.1d.fits' % (name, num)
    hdulist = pyfits.open(fn)
    data = hdulist[0].data
    header = hdulist[0].header
    locations = []
    for line in LINES:
        line_loc = get_wavelength_location(header, line)
        locations.append(find_line_peak(data, line_loc, 5))
    return locations


def get_continuum(location, data):
    """Return the root means square of the continuum values around a
       location."""
    upcont_num = base(location, data, 1)
    downcont_num = base(location, data, -1)
    data = data.tolist()
    values = data[upcont_num:(upcont_num + 3)]
    values.extend(data[(downcont_num - 3):downcont_num])
    return rms(*values)


def get_peak_cont(hdulist, wavelength, search):
    """Return the maximum value near a given wavelength; also the local
       continuum level."""
    data = hdulist[0].data
    header = hdulist[0].header
    wavelength_location = get_wavelength_location(header, wavelength)
    peak_location = find_line_peak(data, wavelength_location, search)
    peak = data[peak_location]
    cont = get_continuum(peak_location, data)
    return peak, cont


def get_wavelength_location(headers, wavelength):
    """Find the location of a given wavelength withing a FITS file."""
    start = headers['CRVAL1']
    step = headers['CDELT1']
    distance = wavelength - start
    number = round(distance / step)
    return number


## Functions for solving for the proper level of sky subtraction ##


def get_std_sky(scale, name, num):
    """Attempt a sky subtraction at a given scaling, and return a metric of
       how good that scaling is.

       A proper sky subraction should result in a basically smooth continuum
       left, so this function looks at the standard deviaton of the spectrum
       around spectral lines known to be atmospheric. These values are
       averaged and return, lower numbers are better."""
    scale = float(scale)
    try_sky(scale, name, num)
    locations = find_lines(name, num)
    fn = '%s/tmp/%s/%s.1d.fits' % (name, num, scale)
    hdulist_out = pyfits.open(fn)
    deviations = []
    for item in locations:
        values = hdulist_out[0].data[(item - 50):(item + 50)]
        deviations.append(std(*values))
    return avg(*deviations)


def guess_scaling(name, spectrum):
    """Make a guess at an appropriate scaling factor for sky subtraction.

       For each atmospheric spectral line given, find the difference
       between the peak and the continuum levels in both the sky spectrum
       and the object spectrum. The ratio of these is the scaling factor.
       Average the ratios from each line and return this value."""
    spectra = '%s/disp/%s.1d.fits' % (name, zerocount(spectrum))
    skyname = '%s/sky.1d.fits' % name
    spectrafits = pyfits.open(spectra)
    skyfits = pyfits.open(skyname)
    scalings = []
    for line in LINES:
        spec_peak, spec_cont = get_peak_cont(spectrafits, line, 5)
        sky_peak, sky_cont = get_peak_cont(skyfits, line, 5)
        scale = ((spec_peak - spec_cont) / (sky_peak - sky_cont))
        scalings.append(scale)
    return avg(*scalings)


def try_sky(scale, name, num):
    """Preform a sky subtraction at a given scaling, saving the result to a
       temporary location."""
    sky = '%s/sky.1d' % name
    scaled_sky = '%s/tmp/%s/%s.sky.1d' % (name, num, scale)
    in_fn = '%s/disp/%s.1d' % (name, num)
    out_fn = '%s/tmp/%s/%s.1d' % (name, num, scale)
    if not (os.path.isfile('%s.fits' % scaled_sky) or
            os.path.isfile('%s.fits' % out_fn)):
        sarith(sky, '*', scale, scaled_sky)
        sarith(in_fn, '-', scaled_sky, out_fn)


## Functions wrapping the solvers and providing output ##


def generate_sky(name, spectrum, sky_level):
    """Use sarith to perform sky subtraction at a given scaling level."""
    num = zerocount(spectrum)
    in_fn = '%s/disp/%s.1d' % (name, num)
    in_sky = '%s/sky.1d' % name
    out_fn = '%s/sub/%s.1d' % (name, num)
    out_sky = '%s/sky/%s.sky.1d' % (name, num)
    subprocess.call(['rm', '-f', '%s.fits' % out_fn])
    subprocess.call(['rm', '-f', '%s.fits' % out_sky])
    sarith(in_sky, '*', sky_level, out_sky)
    sarith(in_fn, '-', out_sky, out_fn)


def modify_sky(path, name, number, op, value):
    """Change the level of sky subtraction for a region by an increment."""
    os.chdir(path)
    sky_levels = get(name, 'sky')
    sky_level = sky_levels[number]
    if op == '+':
        new_sky_level = sky_level + value
    elif op == '-':
        new_sky_level = sky_level - value
    sky_levels[number] = new_sky_level
    write(name, 'sky', sky_levels)
    generate_sky(name, number, new_sky_level)

def sky_subtract(name, spectrum):
    """Optimize the get_std_sky function to determine the best level of sky
       subtraction. Return the value found."""
    num = zerocount(spectrum)
    guess = guess_scaling(name, spectrum)
    os.mkdir('%s/tmp' % name)
    os.mkdir('%s/tmp/%s' % (name, num))
    xopt = scipy.optimize.fmin(get_std_sky, guess,
        args=(name, num), xtol=0.001)
    subprocess.call(['rm', '-rf', '%s/tmp' % name])
    return float(xopt)
