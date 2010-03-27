import math, os, os.path, scipy.optimize, subprocess
import simplejson as json
from pyraf import iraf
import pyfits

####################################
## Some generic, useful functions ##
####################################

## Some Math ##

def avg(*args):
	"""Return the average of a list of values"""
	floatNums = [float(x) for x in args]
	return sum(floatNums) / len(args)

def rms(*args):
	"""Return the root mean square of a list of values"""
	squares = [(float(x) ** 2) for x in args]
	return math.sqrt(avg(*squares))

def std(*args):
	"""Return the standard deviation of a list of values"""
	mean = avg(*args)
	deviations = [(float(x) - mean) for x in args]
	return rms(*deviations)

## Convenience functions ##

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

def calibrate_galaxy(name, calibration, prefix=''):
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
	os.mkdir('%s/rot' % name)
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
	for item1, item2 in zip(list1, list2):
		start1 = item1['start']
		end1 = item1['end']
		start2 = item2['start']
		end2 = item2['end']
		start = avg(start1, start2)
		if math.modf(start)[0] < 0.25:
			start = int(math.floor(start))
		else:
			start = int(math.ceil(start))
		end = avg(end1, end2)
		if math.modf(end)[0] > 0.75:
			end = int(math.ceil(end))
		else:
			end = int(math.floor(end))
		sections.append('[1:2048,%s:%s]' % (start, end))
		size.append(end - start)
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
	i = int(number)
	num = zerocount(i)
	value = float(value)
	data = get_data(name)
	item = data[i]
	sky_level = item['sky_level']
	if op == '+':
		new_sky_level = sky_level + value
	elif op == '-':
		new_sky_level = sky_level - value
	data[i].update({'sky_level':new_sky_level})
	write_data(name, data)
	os.mkdir('%s/tmp' % name)
	regenerate_sky(name, i, data)
	subprocess.call(['rm', '-rf', '%s/tmp' % name])
