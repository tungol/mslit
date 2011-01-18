import math, os, os.path, subprocess, cmath
import numpy, scipy.optimize, pylab
import simplejson as json
from pyraf import iraf
import pyfits
import coords

####################################
## Some generic, useful functions ##
####################################

## Some Math ##

def cubic_solve(b0, b1, b2, b3):
	a = b2 / b3
	b = b1 / b3
	c = (b0) / b3
	m = 2 * (a ** 3) - 9 * a * b + 27 * c
	k = (a ** 2) - 3 * b
	n = (m ** 2) - 4 * (k ** 3)
	w1 = -.5 + .5 * math.sqrt(3) * 1j
	w2 = -.5 - .5 * math.sqrt(3) * 1j
	alpha = (.5 * (m + cmath.sqrt(n))) ** (1.0/3)
	beta = (.5 * (m - cmath.sqrt(n))) ** (1.0/3)
	solution1 = -(1.0/3) * (a + alpha + beta) 
	solution2 = -(1.0/3) * (a + w2 * alpha + w1 * beta) 
	solution3 = -(1.0/3) * (a + w1 * alpha + w2 * beta)
	return [solution1, solution2, solution3]

def avg(*args):
	"""Return the average of a list of values"""
	floatNums = [float(x) for x in args]
	remove_nan(floatNums)
	if len(floatNums) == 0:
		return float('NaN')
	return sum(floatNums) / len(floatNums)

def rms(*args):
	"""Return the root mean square of a list of values"""
	squares = [(float(x) ** 2) for x in args]
	return math.sqrt(avg(*squares))

def sigfigs_format(x, n):
	if n < 1:
		raise ValueError("number of significant digits must be >= 1")
	string = '%.*e' % (n-1, x)
	value, exponent = string.split('e')
	exponent = int(exponent)
	if exponent == 0:
		return value
	else:
		return '$%s \\times 10^{%s}$' % (value, exponent) 

def std(*args):
	"""Return the standard deviation of a list of values"""
	mean = avg(*args)
	deviations = [(float(x) - mean) for x in args]
	return rms(*deviations)

## Convenience functions ##

def average(items, values, test):
	for item in items[:]:
		if not test(item):
			items.remove(item)
	results = {}
	for value in values:
		tmp = [item.__dict__[value] for item in items]
		remove_nan(tmp)
		a = avg(*tmp)
		s = std(*tmp)
		results.update({value: [a,s]})
	return results

def fit(function, parameters, y, x=None):
	def f(params):
		i = 0
		for p in parameters:
			p.set(params[i])
			i += 1
		return y - function(x)
	
	if x is None:
		x = numpy.arange(y.shape[0])
	p = [param() for param in parameters]
	return scipy.optimize.leastsq(f,p)

class ParameterClass:
	def __init__(self, value):
		self.value = value
	
	def set(self, value):
		self.value = value
	
	def __call__(self):
		return self.value
	

def remove_nan(*lists):
	""" remove NaNs from one or more lists 
		if more than one, keep shape of all lists the same """
	for list in lists:
		count = 0
		for i, item in enumerate(list[:]):
			if numpy.isnan(item):
				for item in lists:
					del item[i - count]
				count += 1

def zerocount(i):
	"""Return the three digit representation of a number"""
	if i < 10:
		return '00%s' % i
	elif i < 100:
		return '0%s' % i
	else:
		return '%s' % i

###############################
## Functions to do with IRAF ##
###############################

## Wrappers for loading IRAF packages ##

def load_apextract():
	"""Load the apextract package"""
	iraf.noao(_doprint=0)
	iraf.twodspec(_doprint=0)
	iraf.apextract(_doprint=0)

def load_ccdred():
	"""Load the ccdred package"""
	iraf.noao(_doprint=0)
	iraf.imred(_doprint=0)
	iraf.ccdred(_doprint=0)

def load_imgeom():
	"""Load the imgeom package"""
	iraf.images(_doprint=0)
	iraf.imgeom(_doprint=0)

def load_kpnoslit():
	"""Load the kpnoslit package"""
	iraf.imred(_doprint=0)
	iraf.kpnoslit(_doprint=0)

def load_onedspec():
	"""Load the onedspec package"""
	iraf.noao(_doprint=0)
	iraf.onedspec(_doprint=0)

## Wrappers around IRAF functions ##

def apsum(input, output, section, **kwargs):
	load_apextract()
	set_aperture(input, section)
	kwargs.setdefault('format', 'onedspec')
	kwargs.setdefault('interactive', 'no')
	kwargs.setdefault('find', 'no')
	kwargs.setdefault('trace', 'no')
	kwargs.setdefault('fittrace', 'no')
	iraf.apsum.unlearn()
	iraf.apsum(input=input, output=output, **kwargs)

def calibrate(input, sens, output, **kwargs):
	load_kpnoslit()
	iraf.calibrate.unlearn()
	iraf.calibrate(input=input, output=output, sens=sens, **kwargs)

def ccdproc(images, **kwargs):
	load_ccdred()
	kwargs.setdefault('darkcor', 'no')
	kwargs.setdefault('fixpix', 'no')
	kwargs.setdefault('biassec', '[2049:2080,1:501]')
	kwargs.setdefault('trimsec', '[1:2048,1:501]')
	iraf.ccdproc.unlearn()
	iraf.ccdproc(images=images, **kwargs)

def combine(input, output, **kwargs):
	load_ccdred()
	iraf.combine.unlearn()
	iraf.combine(input=input, output=output, **kwargs)

def dispcor(input, output, **kwargs):
	load_onedspec()
	iraf.dispcor.unlearn()
	iraf.dispcor(input=input, output=output, **kwargs)

def flatcombine(input, **kwargs):
	load_ccdred()
	kwargs.setdefault('process', 'no')
	iraf.flatcombine.unlearn()
	iraf.flatcombine(input = input, **kwargs)

def fixpix(image, mask, **kwargs):
	iraf.fixpix.unlearn()
	iraf.fixpix(images = image, masks = mask, **kwargs)

def fix_image(image, mask):
	"""Apply a bad pixel mask to an image"""
	hedit(image, 'BPM', mask)
	fixpix(image, 'BPM', verbose='yes')

def hedit(images, fields, value, **kwargs):
	kwargs.setdefault('add', 'yes')
	kwargs.setdefault('verify', 'no')
	iraf.hedit.unlearn()
	iraf.hedit(images=images, fields=fields, value=value, **kwargs)

def imcopy(input, output, **kwargs):
	iraf.imcopy.unlearn()
	iraf.imcopy(input=input, output=output, **kwargs)

def rotate(input, output, angle, **kwargs):
	load_imgeom()
	iraf.rotate.unlearn()
	iraf.rotate(input=input, output=output, rotation=-angle, **kwargs)

def sarith(input1, op, input2, output, **kwargs):
	load_onedspec()
	iraf.sarith.unlearn()
	iraf.sarith(input1=input1, op=op, input2=input2, output=output, 
		**kwargs)

def scombine(input, output, **kwargs):
	load_onedspec()
	iraf.scombine.unlearn()
	iraf.scombine(input=input, output=output, **kwargs)

def setairmass(images, **kwargs):
	load_kpnoslit()
	iraf.setairmass.unlearn()
	iraf.setairmass(images=images, **kwargs)

def zerocombine(input, **kwargs):
	load_ccdred()
	iraf.zerocombine.unlearn()
	iraf.zerocombine(input = input, **kwargs)

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

def calibrate_galaxy(name, calibration):
	data = get_data(name)
	sens = '%s/sens' % calibration
	for i, item in enumerate(data):
		num = zerocount(i)
		calibrate('%s/sub/%s.1d' % (name, num), sens, 
			'%s/cal/%s.1d' % (name, num))

def dispcor_galaxy(name):
	data = get_data(name)
	for i, item in enumerate(data):
		num = zerocount(i)
		dispcor('%s/sum/%s.1d' % (name, num), 
			'%s/disp/%s.1d' % (name, num))

def fix_galaxy(name, mask):
	imcopy('@lists/%s' % name, '%s/@lists/%s' % (name, name))
	fix_image('%s/@lists/%s' % (name, name), mask)

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

def sky_subtract_galaxy(name, lines):
	data = get_data(name)
	sky = '%s/sky.1d' % name
	os.mkdir('%s/tmp' % name)
	for i, item in enumerate(data):
		if item['type'] == 'HIIREGION':
			if item.has_key('sky_level'):
				regenerate_sky(name, item)
			else:
				generate_sky(name, item, lines)
	write_data(name, data)
	subprocess.call(['rm', '-rf', '%s/tmp' % name])

## High level functions grouping together several options ##

def calibration(name, standard):
	"""Calibrates all spectra in name with the standard specified"""
	os.mkdir('%s/cal' % name)
	calibrate_galaxy(name, standard)

def disp_galaxy(name, use=None):
	"""Applies dispersion correction across all spectra in name"""
	os.mkdir('%s/disp' % name)
	hedit_galaxy(name, use=use)
	dispcor_galaxy(name)

def init_galaxy(name, mask, zero, flat):
	"""Applies a bad pixel mask to all the images associated with name, 
	then runs ccdproc and combine"""
	os.mkdir(name)
	fix_galaxy(name, mask)
	ccdproc('%s/@lists/%s' % (name, name), zero=zero, flat=flat)
	combine('%s/@lists/%s' % (name, name), '%s/base' % name)

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

def zero_flats(mask):
	"""This function combines the zeros and flats for a night,
	then applies the bad pixel mask specified."""
	zerocombine('@lists/zero')
	flatcombine('@lists/flat1', output = 'Flat1')
	flatcombine('@lists/flat2', output = 'Flat2')
	fix_image('Flat1', mask)
	fix_image('Flat2', mask)
	fix_image('Zero', mask)

## Functions to smooth over the interface to IRAF ##

def list_convert(list):
	"""Convert python lists to the strings that IRAF accepts as lists"""
	str = list.pop(0)
	for item in list:
		str += ', %s' % item
	return str

def namefix(name):
	"""Rename files to get rid of silly naming scheme of apsum"""
	os.rename('%s.0001.fits' % name, '%s.fits' % name)

def set_aperture(input, section):
	"""Create an aperture definition file for apsum"""
	(row, column) = section[1:-1].split(',')
	(left, right) = row.split(':')
	(down, up) = column.split(':')
	center = (float(up) - float(down) + 1) / 2.
	rup = center
	rdown = -center
	tmp = []
	tmp.append('begin\taperture %s 1 1024. %s\n' % (input, center))
	tmp.append('\timage\t%s\n' % input)
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
	file = open('./database/ap%s' % input.replace('/', '_'), 'w')
	file.writelines(tmp)

####################################################
## Functions for working with the metadata I have ##
####################################################

## Functions for low level reading, parsing, and writing ##

def get_raw_data(name):
	fn = 'input/%s.json' % name
	data_file = open(fn, 'r')
	raw_data = json.load(data_file)
	data_file.close()
	return raw_data

def write_raw_data(name, raw_data):
	fn = 'input/%s.json' % name
	data_file = open(fn, 'w')
	json.dump(raw_data, data_file)
	data_file.close()

def read_out_file(name):
	fn = 'input/%s.out' % name
	out_file = open(fn, 'r')
	raw_out = out_file.readlines()
	out_file.close()
	return raw_out

def get_pixel_sizes(name):
	fn = 'input/%s.pix' % name
	file = open(fn, 'r')
	raw = file.readlines()
	file.close()
	data = {}
	for line in raw:
		column, start, end = line.strip().split(',')
		data.update({column:{'start':start, 'end':end}})
	return data

## Functions for basic manipulation ##

def get_data(name):
	raw = get_raw_data(name)
	data = raw['data']
	return data

def init_data(name, use=None):
	if not use:
		use = name
	raw_out = read_out_file(use)
	data = parse_out_file(raw_out)
	pixel_sizes = get_pixel_sizes(use)
	real_start = float(data[0]['xlo'])
	real_end = float(data[-1]['xhi'])
	coord = get_coord(pixel_sizes, real_start, real_end, data)
	angles = get_angles(coord)
	sections, sizes = get_sections(coord)
	for i, angle in enumerate(angles):
		print i, sections[i]
		data[i].update({'angle':angle, 'section':sections[i], 
			'size':sizes[i]})
	write_data(name, data)

def set_obj(name, obj):
	data = get_data(name)
	for i, item in enumerate(data):
		if i != obj:
			if item['type'] == 'HIIREGION':
				item['type'] = 'NIGHTSKY'
	write_data(name, data)

def write_data(name, data):
	try:
		raw_data = get_raw_data(name)
	except (ValueError, IOError):
		raw_data = {}
	raw_data.update({'data':data})
	write_raw_data(name, raw_data)

## Functions for calculations ##

def get_angles(raw_data):
	columns = raw_data.keys()
	list1 = raw_data[columns[0]]
	list2 = raw_data[columns[1]]
	run = float(columns[0]) - float(columns[1])
	angles = []
	for item1, item2 in zip(list1, list2):		
		start1 = item1['start']
		end1 = item1['end']
		start2 = item2['start']
		end2 = item2['end']
		mid1 = avg(start1, end1)
		mid2 = avg(start2, end2)
		rise = mid1 - mid2
		slope = rise / run
		angles.append(math.degrees(math.atan(slope)))
	return angles

def get_coord(pixel_sizes, real_start, real_end, data):
	real_size = real_end - real_start
	coord = {}
	for column in pixel_sizes:
		def convert(real_value):
			real_value = float(real_value)
			pixel_start = float(pixel_sizes[column]['start'])
			pixel_end = float(pixel_sizes[column]['end'])
			pixel_size = pixel_end - pixel_start
			return (((real_value - real_start) * 
				(pixel_size / real_size)) + pixel_start)
		coord.update({column:[]})
		for item in data:
			start = convert(item['xlo'])
			end = convert(item['xhi'])
			coord[column].append({'start':start, 'end':end})
	return coord

def get_sections(raw_data):
	columns = raw_data.keys()
	list1 = raw_data[columns[0]]
	list2 = raw_data[columns[1]]
	sections = []
	size = []
	number = len(list1)
	for i, (item1, item2) in enumerate(zip(list1, list2)):
		start1 = item1['start']
		end1 = item1['end']
		start2 = item2['start']
		end2 = item2['end']
		start = avg(start1, start2)
		end = avg(end1, end2)
		start -= 1.5
		end += 1.5
		if math.modf(start)[0] < 0.70:
			start = int(math.floor(start))
		else:
			start = int(math.ceil(start))
		if math.modf(end)[0] > 0.30:
			end = int(math.ceil(end))
		else:
			end = int(math.floor(end))
		size.append(end - start)
		sections.append('[1:2048,%s:%s]' % (start, end))
	return sections, size

def parse_out_file(raw_out):
	data = []
	header = raw_out.pop(0)
	headers = header.split()
	for i, item in enumerate(headers[:]):
		headers.remove(item)
		if item[0] != '(':
			headers.insert(i, item.lower())
	raw_out.pop(0)
	for i, item in enumerate(raw_out):
		values = item.split()
		item_dict = dict(zip(headers, values))
		item_dict.update({'number':i})
		item_dict.update({'type':item_dict['name']})
		data.append(item_dict)
	return data

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
	data = hdulist[0].data
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

def modify_sky(night, name, number, op, value):
	location = os.path.expanduser('~/iraf/work/%s' % night)
	os.chdir(location)
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


########################################################
## Functions related to processing and output results ##
########################################################

## Useful classes ##

class MeasurementClass:
	def __init__(self, line):
		def conv(str):
			if str == "INDEF":
				str = "NaN"
			return float(str)
		
		if line != '':
			list = line.split()
			self.center = conv(list.pop(0))
			self.cont = conv(list.pop(0))
			self.flux = conv(list.pop(0))
			self.eqw = conv(list.pop(0))
			self.core = conv(list.pop(0))
			self.gfwhm = conv(list.pop(0))
			self.lfwhm = conv(list.pop(0))
	
	def __repr__(self):
		return str(self.flux)
	
	def calculate(self):
		values = ['center', 'cont', 'flux', 'eqw', 'core', 'gfwhm', 'lfwhm']
		for value in values:
			tmp = [x.__dict__[value] for x in self.source]
			self.__dict__[value] = avg(*tmp)
			self.__dict__['%srms' % value] = rms(*tmp)
	

class SpectrumClass:
	def __init__(self, id):
		self.id = id
		try:
			self.number = int(id)
		except:
			pass
		self.measurements = []
	
	def __getattr__(self, name):
		# for all internals not otherwise defined, act like the name
		if name[0:2] == '__':
			return eval('self.id.%s' % name)
		# if 'data' is present, lookup in there too
		elif 'data' in self.__dict__:
			if name in self.data:
				return self.data[name]
		raise AttributeError
	
	def add_measurement(self, line):
		""" add a measurement from splot log files """
		self.measurements.append(MeasurementClass(line))
	
	def add_measurement2(self, name, flux):
		""" add a measurement with known name and flux """
		measurement = MeasurementClass('')
		self.measurements.append(measurement)
		measurement.flux = flux
		measurement.name = name
	
	def calculate(self):
		""" run every item in self.computed and save them as the key """
		for key, value in self.computed.items():
			try:
				self.__dict__[key] = self.call(value)
			except (ZeroDivisionError, AttributeError):
				self.__dict__[key] = float('NaN')
	
	def calculate_OH(self, disambig=True):
		""" Calculate metalicity of the spectrum """
		try:
			r23 = self.r23
		except:
			r23 = self.calculate_r23()
		# uses conversion given by nagao 2006
		b0 = 1.2299 - math.log10(r23)
		b1 = -4.1926
		b2 = 1.0246
		b3 = -6.3169 * 10 ** -2
		# solving the equation 
		solutions = cubic_solve(b0, b1, b2, b3)
		for i, item in enumerate(solutions):
			if item.imag == 0.0:
				solutions[i] = item.real
			else:
				solutions[i] = float('NaN')
		if disambig:
			branch = self.OIII2 / self.OII
			if branch < 2:
				return solutions[2]
			else:
				return solutions[1]
		else:
			return solutions[2]
	
	def calculate_r23(self):
		""" calculate and return the value of R_23 """
		r2 = self.OII / self.hbeta
		r3 = (self.OIII1 + self.OIII2) / self.hbeta
		r23 = r2 + r3
		return r23
	
	def calculate_radial_distance(self):
		""" Calculate the galctocentric radius of the region """
		position = coords.Position('%s %s' % (self.ra, self.dec))
		theta = self.center.angsep(position)
		# radial distance in kiloparsecs
		return self.distance * math.tan(math.radians(theta.degrees()))
	
	def calculate_SFR(self):
		"""halpha SFR calibration given by Kennicutt 1998"""
		d = self.distance * 3.0857 * (10 ** 21)
		flux = self.halpha
		luminosity = flux * 4 * math.pi * (d ** 2)
		return luminosity * 7.9 * (10 ** -42)
	
	def call(self, method, *args, **kwargs):
		""" call a class method given the name of the method as a string """
		return self.__class__.__dict__[method](self, *args, **kwargs)
	
	def collate_lines(self, lines):
		self.lines = {}
		for name, loc in lines.items():
			self.lines.update({name: MeasurementClass('')})
			self.lines[name].name = name
			self.lines[name].loc = loc
			sources = []
			for measurement in self.measurements:
				if measurement.name == name:
					sources.append(measurement)
			self.lines[name].source = sources
		for name, line in self.lines.items():
			line.calculate()
			self.__dict__[name] = line.flux
	
	def correct_extinction(self):
		def k(l):
			# for use in the calzetti method
			# convert to micrometers from angstrom		
			l = l / 10000.
			if 0.63 <= l <= 1.0:
				return ((1.86 / l ** 2) - (0.48 / l ** 3) - 
					(0.1 / l) + 1.73)
			elif 0.12 <= l < 0.63:
				return (2.656 * (-2.156 + (1.509 / l) - 
					(0.198 / l ** 2) + (0.011 / l ** 3)) + 4.88)
			else:
				raise ValueError
		
#		using the method described here: 
#  <http://www.astro.umd.edu/~chris/publications/html_papers/aat/node13.html>
		R_intr = 2.76
		a = 2.21
		R_obv = self.halpha / self.hbeta
		if numpy.isnan(R_obv):
			self.corrected = False
			self.id = self.id + '*'
			return
		self.extinction = a * math.log10(R_obv / R_intr)
#		Now using the Calzetti method:
		for line in self.lines.values():
			line.obv_flux = line.flux
			line.flux = line.obv_flux / (10 ** 
				(-0.4 * self.extinction * k(line.loc)))
			self.__dict__[line.name] =  line.flux
		self.corrected = True
	
	def id_lines(self, lines):
		for measurement in self.measurements:
			tmp = {}
			for name in lines:
				tmp.update({(abs(measurement.center - 
					lines[name])): name})
			name = tmp[min(tmp.keys())]
			measurement.name = name
	

class GalaxyClass:
	def __init__(self, id):
		self.id = id
		self.spectradict = {}
		self.lines = {'OII': 3727, 'hgamma': 4341, 'hbeta': 4861, 
			'OIII1': 4959, 'OIII2': 5007, 'NII1': 6548, 
			'halpha': 6563, 'NII2': 6583, 'SII1': 6717, 
			'SII2': 6731, 'OIII3': 4363}
		self.lookup = {
			'OII': '[O II]$\lambda3727$', 
			'hgamma': 'H$\gamma$', 
			'hbeta': 'H$\\beta$',
			'OIII1': '[O III]$\lambda4959$', 
			'OIII2': '[O III]$\lambda5007$',
			'NII1': '[N II]$\lambda6548$', 
			'halpha': 'H$\\alpha$', 
			'NII2': '[N II]$\lambda6583$', 
			'SII1': '[S II]$\lambda6717$', 
			'SII2': '[S II]$\lambda6731$', 
			'OIII3': '[O III]$\lambda4363$',
			'OH': '$12 + \log{\\textnormal{O/H}}$',
			'SFR': 'SFR(M$_\odot$ / year)',
			'rdistance': 'Radial Distance (kpc)',
			'extinction': 'E(B - V)',
			'r23': '$R_{23}$'
		}
		self.computed = {
			'r23': 'calculate_r23', 
			'SFR': 'calculate_SFR', 
			'rdistance': 'calculate_radial_distance', 
			'OH': 'calculate_OH'
		}
	
	def __getattr__(self, name):
		if name == 'spectra':
			spectra = self.spectradict.values()
			spectra.sort()
			return spectra
		elif name == '__repr__':
			return self.id.__repr__
		else:
			raise AttributeError
	
	def add_log(self, fn):
		def is_spectra_head(line):
			if line[:3] in ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
				'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'):
				return True
			else:
				return False
		
		def is_labels(line):
			labelstr = "    center      cont      flux       eqw"
			labelstr = labelstr + "      core     gfwhm     lfwhm\n"
			if line == labelstr:
				return True
			return False
		
		def get_num(line):
			start = line.find('[') + 1
			stop = start + 3
			return line[start:stop]
		
		file = open('%s/measurements/%s.log' % (self.id, fn))
		raw = file.readlines()
		file.close()
		for line in raw:
			if is_spectra_head(line):
				num = get_num(line)
				if not num in self.spectradict:
					self.spectradict.update(
						{num: SpectrumClass(num)})
			elif is_labels(line):
				pass
			elif line.strip() != '':
				self.spectradict[num].add_measurement(line)
	
	def add_logs(self):
			logs = os.listdir('%s/measurements/' % self.id)
			for log in logs:
				if log[-4:] == '.log':
					self.add_log(log[:-4])
	
	def add_spectra(self, num, spectra):
		self.spectradict.update({num: spectra})
	
	def calculate(self):
		data = get_data(self.id)
		center = coords.Position(self.center)
		for spectrum in self.spectra:
			sdata = data[spectrum.number]
			sdata.update({'distance': self.distance, 'center': center})
			spectrum.data = sdata
			spectrum.computed = self.computed
			spectrum.calculate()
	
	def collate_lines(self):
		for spectrum in self.spectra:
			spectrum.collate_lines(self.lines)
	
	def correct_extinction(self):
		for spectrum in self.spectra:
			spectrum.correct_extinction()
	
	def fit_OH(self):
		# inital guess: flat and solar metallicity
		slope = ParameterClass(0)
		intercept = ParameterClass(8.6)
		def function(x):
			return (intercept() + slope() * x)
		
		x = [s.rdistance for s in self.spectra]
		y = [s.OH for s in self.spectra]
		remove_nan(x, y)
		x = numpy.array(x)
		y = numpy.array(y)
		x = x / self.r25
		lsqout = fit(function, [slope, intercept], y, x)
		self.fit = lsqout
		self.grad = lsqout[0][0]
		self.metal = lsqout[0][1] + lsqout[0][0] * 0.4
		return lsqout
	
	def get_fit_slope(self):
		return self.grad
	
	def get_metallicity(self):
		return self.metal
	
	def id_lines(self):
		lines = self.lines.copy()
		for item in lines:
			lines.update({item: (lines[item] * (self.redshift + 1))})
		for spectrum in self.spectra:
			spectrum.id_lines(lines)
	
	def output_graphs(self):
		graph_metalicity(self)
		graph_SFR(self)
		graph_SFR_metals(self)
	
	def output_tables(self):
		spectra = self.spectra
		for i, spectrum in enumerate(spectra):
			spectrum.printnumber = i + 1
		make_flux_table(self)
		make_data_table(self)
	
	def run(self):
		self.add_logs()
		self.id_lines()
		self.collate_lines()
		self.correct_extinction()
		self.calculate()
		self.regions = len(self.spectra)
	

## Functions for reading in tables of data ##

def get_galaxies(fn, keys):
	gfile = open('../other_data/%s' % fn, 'r')
	raw = gfile.readlines()
	gfile.close()
	galaxies = []
	current = None
	number = None
	for line in raw:
		line = line.strip()
		if line == '':
			pass
		elif line[0] == '*':
			id = line[1:]
			name = 'NGC ' + id
			current = GalaxyClass(id)
			current.name = name
			number = 0
			galaxies.append(current)
			current.distance = keys[id]['distance']
			current.r25 = keys[id]['r_0']
			current.type = keys[id]['type']
			current.bar = keys[id]['bar']
			current.ring = keys[id]['ring']
			current.env = keys[id]['env']
		else:
			(r, hbeta, OII, OIII) =  line.split('\t')
			r = float(r)
			hbeta = float(hbeta)
			OII = float(OII)
			OIII = float(OIII)
			r_23 = OII + OIII
			OII = hbeta * OII
			OIII = hbeta * OIII
			r = current.r25 * r
			spectrum = SpectrumClass(str(number))
			current.add_spectra(number, spectrum)
			spectrum.add_measurement2('hbeta', hbeta)
			spectrum.add_measurement2('OII', OII)
			spectrum.add_measurement2('OIII1', OIII)
			spectrum.distance = current.distance
			spectrum.rdistance = r
			spectrum.r23 = r_23
			spectrum.OH = spectrum.calculate_OH(disambig=False)
			number += 1
	return galaxies

def get_other():
	files = os.listdir('../other_data/')
	for fn in files:
		if fn[-4:] != '.txt':
			files.remove(fn)
	keyfile = files.pop(0)
	keys = parse_keyfile(keyfile)
	others = []
	for item in files:
		galaxies = get_galaxies(item, keys)
		for galaxy in galaxies:
			others.append(galaxy)
	for galaxy in others:
		galaxy.regions = len(galaxy.spectra)
	return others

def parse_keyfile(fn):
	keyfile = open('../other_data/%s' % fn, 'r')
	raw = keyfile.readlines()
	keyfile.close()
	keys = {}
	for line in raw:
		if line[0:3] == 'ngc':
			pass
		else:
			line = line.strip()
			(ngc, distance, r_0, htype, bar, ring, env) = line.split('\t')
			# convert distance to kpc from Mpc for consistency
			distance = float(distance) * 1000
			# convert r_0 from arcminutes to kpc
			r_0 = distance * math.tan(math.radians(float(r_0) * 60))
			keys.update({ngc:{
			'distance': distance, 
			'r_0': r_0,
			'type': htype,
			'bar': bar,
			'ring': ring,
			'env': env
		}})
	return keys

## Functions for graphing ##

def compare_basic(galaxies, other):
	graph_number = get_graph_number()
	pylab.figure(figsize=(5,5), num=graph_number)
	pylab.xlabel('$R/R_{25}$')
	pylab.ylabel('$12 + \log{\\textnormal{O/H}}$')
	#overplot solar metalicity
	t = numpy.arange(0, 2, .1)
	solardata = 8.69 + t * 0
	pylab.plot(t, solardata, 'k--')
	pylab.text(1.505, 8.665, '$Z_\odot$')
	# plot the other data as black diamonds
	for galaxy in other:
		spectra = galaxy.spectra
		OH = [s.OH for s in spectra]
		r = [s.rdistance for s in spectra]
		remove_nan(OH, r)
		OH = numpy.array(OH)
		r = numpy.array(r)
		r = r / galaxy.r25
		pylab.plot(r, OH, 'wd')
	#plot my galaxies
	data = []
	for galaxy in galaxies:
		spectra = galaxy.spectra
		OH = [s.OH for s in spectra]
		r = [s.rdistance for s in spectra]
		remove_nan(OH, r)
		OH = numpy.array(OH)
		r = numpy.array(r)
		r = r / galaxy.r25
		data.append((r, OH))
	pylab.plot(data[0][0], data[0][1], 'r^')
	pylab.plot(data[1][0], data[1][1], 'co')
	pylab.axis((0, 1.5, 8.0, 9.7))
	pylab.savefig('tables/basic_comparison.eps', format='eps')

def compare_type(galaxies, other):
	graph_number = get_graph_number()
	pylab.figure(figsize=(5,5), num=graph_number)
	pylab.xlabel('$R/R_{25}$')
	pylab.ylabel('$12 + \log{\\textnormal{O/H}}$')
	#overplot solar metalicity
	t = numpy.arange(0, 2, .1)
	solardata = 8.69 + t * 0
	pylab.plot(t, solardata, 'k--')
	pylab.text(1.505, 8.665, '$Z_\odot$')
	# plot the other data
	for galaxy in other:
		spectra = galaxy.spectra
		OH = [s.OH for s in spectra]
		r = [s.rdistance for s in spectra]
		remove_nan(OH, r)
		OH = numpy.array(OH)
		r = numpy.array(r)
		r = r / galaxy.r25
		if galaxy.type in ('Sa', 'Sab'):
			pylab.plot(r, OH, 'y^')
		elif galaxy.type in ('Sb', 'Sbc'):
			pylab.plot(r, OH, 'rd')
		elif galaxy.type in ('Sc', 'Scd'):
			pylab.plot(r, OH, 'mp')
		elif galaxy.type in ('Sd', 'Irr'):
			pylab.plot(r, OH, 'bD')
	#plot my galaxies
	for galaxy in galaxies:
		spectra = galaxy.spectra
		OH = [s.OH for s in spectra]
		r = [s.rdistance for s in spectra]
		remove_nan(OH, r)
		OH = numpy.array(OH)
		r = numpy.array(r)
		r = r / galaxy.r25
		if galaxy.type in ('Sa', 'Sab'):
			pylab.plot(r, OH, 'y^')
		elif galaxy.type in ('Sb', 'Sbc'):
			pylab.plot(r, OH, 'rd')
		elif galaxy.type in ('Sc', 'Scd'):
			pylab.plot(r, OH, 'mp')
		elif galaxy.type in ('Sd', 'Irr'):
			pylab.plot(r, OH, 'bD')
	pylab.axis((0, 1.5, 8.0, 9.7))
	pylab.savefig('tables/type_comparison.eps', format='eps')

def compare_bar(galaxies, other):
	graph_number = get_graph_number()
	pylab.figure(figsize=(5,5), num=graph_number)
	pylab.xlabel('$R/R_{25}$')
	pylab.ylabel('$12 + \log{\\textnormal{O/H}}$')
	#overplot solar metalicity
	t = numpy.arange(0, 2, .1)
	solardata = 8.69 + t * 0
	pylab.plot(t, solardata, 'k--')
	pylab.text(1.505, 8.665, '$Z_\odot$')
	# plot the other data
	for galaxy in other:
		spectra = galaxy.spectra
		OH = [s.OH for s in spectra]
		r = [s.rdistance for s in spectra]
		remove_nan(OH, r)
		OH = numpy.array(OH)
		r = numpy.array(r)
		r = r / galaxy.r25
		if galaxy.bar == 'A':
			pylab.plot(r, OH, 'y^')
		elif galaxy.bar == 'AB':
			pylab.plot(r, OH, 'rd')
		elif galaxy.bar == 'B':
			pylab.plot(r, OH, 'mp')
	#plot my galaxies
	for galaxy in galaxies:
		spectra = galaxy.spectra
		OH = [s.OH for s in spectra]
		r = [s.rdistance for s in spectra]
		remove_nan(OH, r)
		OH = numpy.array(OH)
		r = numpy.array(r)
		r = r / galaxy.r25
		if galaxy.bar == 'A':
			pylab.plot(r, OH, 'y^')
		elif galaxy.bar == 'AB':
			pylab.plot(r, OH, 'rd')
		elif galaxy.bar == 'B':
			pylab.plot(r, OH, 'mp')
	pylab.axis((0, 1.5, 8.0, 9.7))
	pylab.savefig('tables/bar_comparison.eps', format='eps')

def compare_ring(galaxies, other):
	graph_number = get_graph_number()
	pylab.figure(figsize=(5,5), num=graph_number)
	pylab.xlabel('$R/R_{25}$')
	pylab.ylabel('$12 + \log{\\textnormal{O/H}}$')
	#overplot solar metalicity
	t = numpy.arange(0, 2, .1)
	solardata = 8.69 + t * 0
	pylab.plot(t, solardata, 'k--')
	pylab.text(1.505, 8.665, '$Z_\odot$')
	# plot the other data
	for galaxy in other:
		spectra = galaxy.spectra
		OH = [s.OH for s in spectra]
		r = [s.rdistance for s in spectra]
		remove_nan(OH, r)
		OH = numpy.array(OH)
		r = numpy.array(r)
		r = r / galaxy.r25
		if galaxy.ring == 's':
			pylab.plot(r, OH, 'y^')
		elif galaxy.ring == 'rs':
			pylab.plot(r, OH, 'rd')
		elif galaxy.ring == 'r':
			pylab.plot(r, OH, 'mp')
	#plot my galaxies
	for galaxy in galaxies:
		spectra = galaxy.spectra
		OH = [s.OH for s in spectra]
		r = [s.rdistance for s in spectra]
		remove_nan(OH, r)
		OH = numpy.array(OH)
		r = numpy.array(r)
		r = r / galaxy.r25
		if galaxy.ring == 's':
			pylab.plot(r, OH, 'y^')
		elif galaxy.ring == 'rs':
			pylab.plot(r, OH, 'rd')
		elif galaxy.ring == 'r':
			pylab.plot(r, OH, 'mp')
	pylab.axis((0, 1.5, 8.0, 9.7))
	pylab.savefig('tables/ring_comparison.eps', format='eps')

def compare_env(galaxies, other):
	graph_number = get_graph_number()
	pylab.figure(figsize=(5,5), num=graph_number)
	pylab.xlabel('$R/R_{25}$')
	pylab.ylabel('$12 + \log{\\textnormal{O/H}}$')
	#overplot solar metalicity
	t = numpy.arange(0, 2, .1)
	solardata = 8.69 + t * 0
	pylab.plot(t, solardata, 'k--')
	pylab.text(1.505, 8.665, '$Z_\odot$')
	# plot the other data
	for galaxy in other:
		spectra = galaxy.spectra
		OH = [s.OH for s in spectra]
		r = [s.rdistance for s in spectra]
		remove_nan(OH, r)
		OH = numpy.array(OH)
		r = numpy.array(r)
		r = r / galaxy.r25
		if galaxy.env == 'isolated':
			pylab.plot(r, OH, 'y^')
		elif galaxy.env == 'group':
			pylab.plot(r, OH, 'rd')
		elif galaxy.env == 'pair':
			pylab.plot(r, OH, 'mp')
	#plot my galaxies
	for galaxy in galaxies:
		spectra = galaxy.spectra
		OH = [s.OH for s in spectra]
		r = [s.rdistance for s in spectra]
		remove_nan(OH, r)
		OH = numpy.array(OH)
		r = numpy.array(r)
		r = r / galaxy.r25
		if galaxy.env == 'isolated':
			pylab.plot(r, OH, 'y^')
		elif galaxy.env == 'group':
			pylab.plot(r, OH, 'rd')
		elif galaxy.env == 'pair':
			pylab.plot(r, OH, 'mp')
	pylab.axis((0, 1.5, 8.0, 9.7))
	pylab.savefig('tables/env_comparison.eps', format='eps')

def get_graph_number():
	global graph_number
	try:
		graph_number += 1
	except NameError:
		graph_number = 0
	return graph_number	

def graph_metalicity(galaxy):
	graph_number = get_graph_number()
	spectra = galaxy.spectra
	OH = [s.OH for s in spectra]
	r = [s.rdistance for s in spectra]
	remove_nan(OH, r)
	OH = numpy.array(OH)
	r = numpy.array(r)
	r = r / galaxy.r25
	pylab.figure(figsize=(5,5), num=graph_number)
	pylab.xlabel('$R/R_{25}$')
	pylab.ylabel('$12 + \log{\\textnormal{O/H}}$')
	#plot the data
	pylab.plot(r, OH, 'co')
	#overplot the fitted function
	t = numpy.arange(0, 2, .1)
	fit = galaxy.fit[0]
	fitdata = fit[1] + t * fit[0]
	pylab.plot(t, fitdata, 'k-')
	#overplot solar metalicity
	solardata = 8.69 + t * 0
	pylab.plot(t, solardata, 'k--')
	v = (0, 1.5, 8.0, 9.7)
	pylab.axis(v)
	# label solar metalicity
	pylab.text(1.505, 8.665, '$Z_\odot$')
	pylab.savefig('tables/%s_metals.eps' % galaxy.id, format='eps')

def graph_SFR(galaxy):
	graph_number = get_graph_number()
	spectra = galaxy.spectra
	#remove uncorrected values
	for spectrum in spectra[:]:
		if spectrum.id[-1] == '*':
			spectra.remove(spectrum)
	SFR = [s.SFR for s in spectra]
	r = [s.rdistance for s in spectra]
	remove_nan(SFR, r)
	SFR = numpy.array(SFR)
	r = numpy.array(r)
	r = r / galaxy.r25
	pylab.figure(figsize=(5,5), num=graph_number)
	pylab.xlabel('$R/R_{25}$')
	pylab.ylabel('$SFR (M_\odot/\\textnormal{year})$')
	#plot the data
	pylab.plot(r, SFR, 'co')
	v = pylab.axis()
	v = (0, 1.5, v[2], v[3])
	pylab.axis(v)
	pylab.savefig('tables/%s_sfr.eps' % galaxy.id, format='eps')

def graph_SFR_metals(galaxy):
	graph_number = get_graph_number()
	pylab.figure(figsize=(5,5), num=graph_number)
	pylab.xlabel('SFR(M$_\odot$ / year)')
	pylab.ylabel('$12 + \log{\\textnormal{O/H}}$')
	spectra = galaxy.spectra
	#remove uncorrected values
	for spectrum in spectra[:]:
		if spectrum.id[-1] == '*':
			spectra.remove(spectrum)
	OH = [s.OH for s in spectra]
	SFR = [s.SFR for s in spectra]
	remove_nan(OH, SFR)
	pylab.plot(SFR, OH, 'co')
	v = pylab.axis()
	v = (0, v[1], 8.0, 9.7)
	t = numpy.arange(0, v[1]*1.5, v[1]*0.05)
	#overplot solar metalicity
	solardata = 8.69 + t * 0
	pylab.plot(t, solardata, 'k--')
	pylab.text(v[1] * 1.01, 8.665, '$Z_\odot$')
	pylab.axis((v[0], v[1], 8.0, 9.7))
	pylab.savefig('tables/%s_sfr-metal.eps' % galaxy.id, format='eps')

## Functions for outputting latex tables ##

def compare_type_table(galaxies, other):
	keys = ['grad', 'metal']
	lookup = {
		'grad': 'Gradient (dex/R$_{25}$)', 
		'metal': 'Metalicity at 0.4R$_{25}$',
	}
	for item in other:
		galaxies.append(item)
	group1 = average(galaxies[:], keys, lambda g: g.type in ('Sa', 'Sab'))
	group2 = average(galaxies[:], keys, lambda g: g.type in ('Sb', 'Sbc'))
	group3 = average(galaxies[:], keys, lambda g: g.type in ('Sc', 'Scd'))
	group4 = average(galaxies[:], keys, lambda g: g.type in ('Sd', 'Irr'))
	string = ''
	string += 'Hubble Type '
	for value in keys:
		string += '& %s & Standard Deviation ' % lookup[value]
	string += '\\\\\n'
	string += '\\midrule\n'
	string += ' Sa and Sab '
	for value in keys:
		string += '& %s ' % sigfigs_format(group1[value][0], 2)
		string += '& %s ' % sigfigs_format(group1[value][1], 2)
	string += '\\\\\n'
	string += ' Sb and Sbc '
	for value in keys:
		string += '& %s ' % sigfigs_format(group2[value][0], 2)
		string += '& %s ' % sigfigs_format(group3[value][1], 2)
	string += '\\\\\n'
	string += ' Sc and Scd '
	for value in keys:
		string += '& %s ' % sigfigs_format(group3[value][0], 2)
		string += '& %s ' % sigfigs_format(group3[value][1], 2)
	string += '\\\\\n'
	string += ' Sd '
	for value in keys:
		string += '& %s ' % sigfigs_format(group4[value][0], 2)
		string += '& %s ' % sigfigs_format(group4[value][1], 2)
	string += '\\\\\n'
	fn = 'tables/type_comparison.tex'
	file = open(fn, 'w')
	file.write(string)
	file.close()

def compare_bar_table(galaxies, other):
	keys = ['grad', 'metal']
	lookup = {
		'grad': 'Gradient (dex/R$_{25}$)', 
		'metal': 'Metalicity at 0.4R$_{25}$',
	}
	for item in other:
		galaxies.append(item)
	group1 = average(galaxies[:], keys, lambda g: g.bar == 'A')
	group2 = average(galaxies[:], keys, lambda g: g.bar == 'AB')
	group3 = average(galaxies[:], keys, lambda g: g.bar == 'B')
	string = ''
	string += ' Bar '
	for value in keys:
		string += '& %s & Standard Deviation ' % lookup[value]
	string += '\\\\\n'
	string += '\\midrule\n'
	string += ' No Bar '
	for value in keys:
		string += '& %s ' % sigfigs_format(group1[value][0], 2)
		string += '& %s ' % sigfigs_format(group1[value][1], 2)
	string += '\\\\\n'
	string += ' Weakly Barred '
	for value in keys:
		string += '& %s ' % sigfigs_format(group2[value][0], 2)
		string += '& %s ' % sigfigs_format(group3[value][1], 2)
	string += '\\\\\n'
	string += ' Strongly Barred '
	for value in keys:
		string += '& %s ' % sigfigs_format(group3[value][0], 2)
		string += '& %s ' % sigfigs_format(group3[value][1], 2)
	string += '\\\\\n'
	fn = 'tables/bar_comparison.tex'
	file = open(fn, 'w')
	file.write(string)
	file.close()

def compare_ring_table(galaxies, other):
	keys = ['grad', 'metal']
	lookup = {
		'grad': 'Gradient (dex/R$_{25}$)', 
		'metal': 'Metalicity at 0.4R$_{25}$',
	}
	for item in other:
		galaxies.append(item)
	group1 = average(galaxies[:], keys, lambda g: g.ring == 's')
	group2 = average(galaxies[:], keys, lambda g: g.ring == 'rs')
	group3 = average(galaxies[:], keys, lambda g: g.ring == 'r')
	string = ''
	string += ' Ring '
	for value in keys:
		string += '& %s & Standard Deviation ' % lookup[value]
	string += '\\\\\n'
	string += '\\midrule\n'
	string += ' S-Shaped '
	for value in keys:
		string += '& %s ' % sigfigs_format(group1[value][0], 2)
		string += '& %s ' % sigfigs_format(group1[value][1], 2)
	string += '\\\\\n'
	string += ' Intermediate Type '
	for value in keys:
		string += '& %s ' % sigfigs_format(group2[value][0], 2)
		string += '& %s ' % sigfigs_format(group3[value][1], 2)
	string += '\\\\\n'
	string += ' Ringed '
	for value in keys:
		string += '& %s ' % sigfigs_format(group3[value][0], 2)
		string += '& %s ' % sigfigs_format(group3[value][1], 2)
	string += '\\\\\n'
	fn = 'tables/ring_comparison.tex'
	file = open(fn, 'w')
	file.write(string)
	file.close()

def compare_env_table(galaxies, other):
	keys = ['grad', 'metal']
	lookup = {
		'grad': 'Gradient (dex/R$_{25}$)', 
		'metal': 'Metalicity at 0.4R$_{25}$',
	}
	for item in other:
		galaxies.append(item)
	group1 = average(galaxies[:], keys, lambda g: g.env == 'isolated')
	group2 = average(galaxies[:], keys, lambda g: g.env == 'group')
	group3 = average(galaxies[:], keys, lambda g: g.env == 'pair')
	string = ''
	string += ' Environment '
	for value in keys:
		string += '& %s & Standard Deviation ' % lookup[value]
	string += '\\\\\n'
	string += '\\midrule\n'
	string += ' Isolated '
	for value in keys:
		string += '& %s ' % sigfigs_format(group1[value][0], 2)
		string += '& %s ' % sigfigs_format(group1[value][1], 2)
	string += '\\\\\n'
	string += ' Group '
	for value in keys:
		string += '& %s ' % sigfigs_format(group2[value][0], 2)
		string += '& %s ' % sigfigs_format(group3[value][1], 2)
	string += '\\\\\n'
	string += ' Pair '
	for value in keys:
		string += '& %s ' % sigfigs_format(group3[value][0], 2)
		string += '& %s ' % sigfigs_format(group3[value][1], 2)
	string += '\\\\\n'
	fn = 'tables/env_comparison.tex'
	file = open(fn, 'w')
	file.write(string)
	file.close()

def make_comparison_table(galaxies, other):
	keys = ['grad', 'metal', 'type', 'bar', 'ring', 'env', 'regions']
	lookup = {
		'grad': 'Gradient (dex/R$_{25}$)', 
		'metal': 'Metalicity at 0.4R$_{25}$',
		'type': 'Hubble Type',
		'bar': 'Bar',
		'ring': 'Ring',
		'env': 'Environment',
		'regions': 'Number of Regions'
	}
	string = ''
	string += '\\begin{tabular}{ *{%s}{c}}\n' % (len(keys) + 1)
	string += '\\toprule\n'
	string += ' Name '
	for item in keys:
		string += '& %s ' % lookup[item]
	string += '\\\\\n'
	string += '\\midrule\n'
	for item in galaxies:
		string += ' %s ' % item.name
		for key in keys:
			value = item.__dict__[key]
			if type(value) == str:
				string += '& %s ' % value
			else:
				if numpy.isnan(value):
					value = '. . .'
				elif key == 'regions':
					value = str(value)
				else:
					value = sigfigs_format(value, 3)
				string += '& %s ' % value
		string += '\\\\\n'
	string += '\\midrule\n'
	for item in other:
		string += ' %s ' % item.name
		for key in keys:
			value = item.__dict__[key]
			if type(value) == str:
				string += '& %s ' % value
			else:
				if numpy.isnan(value):
					value = '. . .'
				elif key == 'regions':
					value = str(value)
				else:
					value = sigfigs_format(value, 3)
				string += '& %s ' % value
		string += '\\\\\n'
	string += '\\bottomrule\n'
	string += '\\end{tabular}\n'
	fn = 'tables/comparison.tex'
	file = open(fn, 'w')
	file.write(string)
	file.close()

def make_data_table(galaxy):
	spectra = galaxy.spectra
	values = ['rdistance', 'OH', 'SFR']
	string = ''
	string += '\\begin{tabular}{ *{4}{c}}\n'
	string += '\\toprule\n'
	string += ' Number '
	for item in values:
		string += '& %s ' % galaxy.lookup[item]
	string += '\\\\\n'
	string += '\\midrule\n'
	for spectrum in spectra:
		if spectrum.corrected == True:
			string += ' %s ' % spectrum.printnumber
		else:
			string += ' ~%s$^a$' % spectrum.printnumber
		for item in values:
			value = spectrum.__dict__[item]
			if numpy.isnan(value):
				value = '. . .'
			else:
				value = sigfigs_format(value, 2)
			string += '& %s ' % value
		string += '\\\\\n'
	string += '\\bottomrule\n'
	string += '\\end{tabular}\n'
	fn = 'tables/%s.tex' % galaxy.id
	file = open(fn, 'w')
	file.write(string)
	file.close()

def make_flux_table(galaxy):
	spectra = galaxy.spectra
	lines = galaxy.lines.keys()
	lines.sort()
	for item in lines[:]:
		unused = True
		for s in spectra:
			if not numpy.isnan(s.__dict__[item]):
				unused = False
				break
		if unused == True:
			lines.remove(item)
	string = ''
	string += '\\begin{tabular}{ *{%s}{c}}\n' % (len(lines) + 1)
	string += '\\toprule\n'
	string += ' Number '
	for item in lines:
		string += '& %s ' % galaxy.lookup[item]
	string += '\\\\\n'
	string += '\\midrule\n'
	for spectrum in spectra:
		if spectrum.corrected == True:
			string += ' %s ' % spectrum.printnumber
		else:
			string += ' ~%s$^a$' % spectrum.printnumber
		for line in lines:
			value = spectrum.__dict__[line]
			if numpy.isnan(value):
				value = '. . .'
			else:
				value = sigfigs_format(value, 2)
			string += '& %s ' % value
		string += '\\\\\n'
	string += '\\bottomrule\n'
	string += '\\end{tabular}\n'
	fn = 'tables/%sflux.tex' % galaxy.id
	file = open(fn, 'w')		
	file.write(string)
	file.close()
