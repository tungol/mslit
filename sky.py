import os
import subprocess
import pyfits
import scipy.optimize
from misc import rms, std, avg, zerocount
from iraf import sarith, imcopy, scombine, list_convert
from data import get_sizes, get_types

##########################################
## Functions related to sky subtraction ##
##########################################

## Functions for manipulating the fits data at a low level ##


def find_line_peak(hdulist, wavelength, search):
    number = get_wavelength_location(hdulist, wavelength)
    data = hdulist[0].data
    search = range(int(number - search), int(number + search))
    list = [data[i] for i in search]
    peak = max(list)
    peak_num = search[list.index(peak)]
    return peak_num


def get_continuum(upcont_num, downcont_num, data):
    data = data.tolist()
    values = data[upcont_num:(upcont_num + 3)]
    values.extend(data[(downcont_num - 3):downcont_num])
    return rms(*values)


def get_peak_cont(hdulist, wavelength, search):
    data = hdulist[0].data
    peak_num = find_line_peak(hdulist, wavelength, search)
    peak = data[peak_num]
    upcont_num = peak_num
    while True:
        if data[upcont_num] >= data[upcont_num + 1]:
            upcont_num += 1
        else:
            break
    downcont_num = peak_num
    while True:
        if data[downcont_num] >= data[downcont_num - 1]:
            downcont_num -= 1
        else:
            break
    cont = get_continuum(upcont_num, downcont_num, data)
    return peak, cont


def get_wavelength_location(hdulist, wavelength):
    headers = hdulist[0].header
    start = headers['CRVAL1']
    step = headers['CDELT1']
    tmp = wavelength - start
    number = round(tmp / step)
    return number

## Functions for solving for the proper level of sky subtraction ##


def get_std_sky(scale, name, num, lines):
    scale = float(scale)
    sky = '%s/sky.1d' % name
    scaled_sky = '%s/tmp/%s/%s.sky.1d' % (name, num, scale)
    in_fn = '%s/disp/%s.1d' % (name, num)
    out_fn = '%s/tmp/%s/%s.1d' % (name, num, scale)
    sarith(sky, '*', scale, scaled_sky)
    sarith(in_fn, '-', scaled_sky, out_fn)
    outfits = pyfits.open('%s.fits' % out_fn)
    infits = pyfits.open('%s.fits' % in_fn)
    locations = []
    for line in lines:
        locations.append(find_line_peak(infits, line, 5))
    deviations = []
    for item in locations:
        values = outfits[0].data[(item - 50):(item + 50)]
        deviations.append(std(*values))
    return avg(*deviations)


def guess_scaling(name, spectrum, sky, lines):
    name = '%s/disp/%s.1d.fits' % (name, zerocount(spectrum))
    skyname = '%s.fits' % sky
    spectrafits = pyfits.open(name)
    skyfits = pyfits.open(skyname)
    scalings = []
    for line in lines:
        spec_peak, spec_cont = get_peak_cont(spectrafits, line, 5)
        sky_peak, sky_cont = get_peak_cont(skyfits, line, 5)
        scale = ((spec_peak - spec_cont) / (sky_peak - sky_cont))
        scalings.append(scale)
    return avg(*scalings)


## Functions wrapping the solvers and providing output ##


def generate_sky(name, spectrum, lines):
    num = zerocount(spectrum)
    sky = '%s/sky.1d' % name
    xopt = float(sky_subtract(name, spectrum, sky, lines))
    tmp_fn = '%s/tmp/%s/%s.1d' % (name, num, xopt)
    tmp_sky = '%s/tmp/%s/%s.sky.1d' % (name, num, xopt)
    out_fn = '%s/sub/%s.1d' % (name, num)
    out_sky = '%s/sky/%s.sky.1d' % (name, num)
    imcopy(tmp_fn, out_fn)
    imcopy(tmp_sky, out_sky)
    return xopt


def regenerate_sky(name, spectrum, sky_level):
    num = zerocount(spectrum)
    in_fn = '%s/disp/%s.1d' % (name, num)
    in_sky = '%s/sky.1d' % name
    tmp_fn = '%s/tmp/%s.1d' % (name, num)
    tmp_sky = '%s/tmp/%s.sky.1d' % (name, num)
    sarith(in_sky, '*', sky_level, tmp_sky)
    sarith(in_fn, '-', tmp_sky, tmp_fn)
    out_fn = '%s/sub/%s.1d' % (name, num)
    out_sky = '%s/sky/%s.sky.1d' % (name, num)
    subprocess.call(['rm', '-f', '%s.fits' % out_fn])
    subprocess.call(['rm', '-f', '%s.fits' % out_sky])
    imcopy(tmp_sky, out_sky)
    imcopy(tmp_fn, out_fn)


def sky_subtract(name, spectrum, sky, lines):
    num = zerocount(spectrum)
    guess = guess_scaling(name, spectrum, sky, lines)
    # fmin
    os.mkdir('%s/tmp/%s' % (name, num))
    xopt = scipy.optimize.fmin(get_std_sky, guess,
        args=(name, num, lines), xtol=0.001)
    return xopt


## Other functions relating to sky subtraction ##


def get_sky_list(name, star_num):
    sky_types = ['NIGHTSKY']
    items = get_types(name)
    if star_num:
        items.pop(star_num)
        sky_types.append('HIIREGION')
    sky_list = [i for i, x in enumerate(items) if x in sky_types]
    return sky_list


def combine_sky_spectra(name, use=None, star_num=None):
    if not use:
        use = name
    sky_list = get_sky_list(name, star_num)
    sizes = get_sizes(name)
    flist = []
    for spectra in sky_list:
        scale = sizes[spectra]['size']
        num = zerocount(spectra)
        sarith('%s/disp/%s.1d' % (use, num), '/', scale,
            '%s/sky/%s.scaled' % (name, num))
        flist.append('%s/sky/%s.scaled' % (name, num))
    scombine(list_convert(flist), '%s/sky.1d' % name)
