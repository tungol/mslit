import os, subprocess
import pyfits, scipy
from generic import rms, std, avg, zerocount
from data import get_data, write_data
from iraf import sarith, imcopy, scombine
from iraf import list_convert

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

def get_continuum(upcont_num, downcont_num, data, search=5):
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

def guess_scaling(name, spectra, sky, lines):
    number = spectra['number']
    name = '%s/disp/%s.1d.fits' % (name, zerocount(number))
    skyname = '%s.fits' % sky
    spectrafits = pyfits.open(name)
    skyfits = pyfits.open(skyname)
    scalings = []
    for line in lines:
        spec_peak, spec_cont = get_peak_cont(spectrafits, line, 5)
        sky_peak, sky_cont = get_peak_cont(skyfits, line,   5)
        scale = ((spec_peak - spec_cont) / (sky_peak - sky_cont))
        scalings.append(scale)
    return avg(*scalings)

## Functions wrapping the solvers and providing output ##

def generate_sky(name, item, lines):
    num = zerocount(item['number'])
    sky = '%s/sky.1d' % name
    xopt = float(sky_subtract(name, item, sky, lines))
    print '\tSolution for %s: %s' % (num, xopt)
    print '\tSolution divided by width: %s' % (xopt / item['size'])
    tmp_fn = '%s/tmp/%s/%s.1d' % (name, num, xopt)
    tmp_sky = '%s/tmp/%s/%s.sky.1d' % (name, num, xopt)
    out_fn = '%s/sub/%s.1d' % (name, num)
    out_sky  = '%s/sky/%s.sky.1d' % (name, num)
    imcopy(tmp_fn, out_fn)
    imcopy(tmp_sky, out_sky)    
    item.update({'sky_level':xopt})

def regenerate_sky(name, item):
    num = zerocount(item['number'])
    sky_level = item['sky_level']
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

def sky_subtract(name, spectra, sky, lines):
    num = zerocount(spectra['number'])
    guess = guess_scaling(name, spectra, sky, lines)
    # fmin
    os.mkdir('%s/tmp/%s' % (name, num))
    xopt = scipy.optimize.fmin(get_std_sky, guess, 
        args=(name, num, lines), xtol=0.001)
    return xopt

## Other functions relating to sky subtraction ##

def combine_sky_spectra(name, use=None, **kwargs):
    if not use:
        use = name
    data = get_data(use)
    list = []
    for i, item in enumerate(data):
        if item['type'] == 'NIGHTSKY':
            list.append(i)
    flist = []
    for spectra in list:
        scale = data[spectra]['size']
        num = zerocount(spectra)
        sarith('%s/disp/%s.1d' % (use, num), '/', scale, 
            '%s/sky/%s.scaled' % (name, num))
        flist.append('%s/sky/%s.scaled' % (name, num))
    scombine(list_convert(flist), '%s/sky.1d' % name, **kwargs)

def modify_sky(path, name, number, op, value):
    os.chdir(path)
    number = int(number)
    value = float(value)
    data = get_data(name)
    item = data[number]
    sky_level = item['sky_level']
    if op == '+':
        new_sky_level = sky_level + value
    elif op == '-':
        new_sky_level = sky_level - value
    item.update({'sky_level':new_sky_level})
    write_data(name, data)
    os.mkdir('%s/tmp' % name)
    regenerate_sky(name, item)
    subprocess.call(['rm', '-rf', '%s/tmp' % name])

