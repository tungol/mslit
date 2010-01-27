import math, os, os.path, scipy.optimize, subprocess
import simplejson as json
from pyraf import iraf
import pyfits

def avg(*args):
	floatNums = [float(x) for x in args]
	return sum(floatNums) / len(args)

def rms(*args):
	squares = [(float(x) ** 2) for x in args]
	return math.sqrt(avg(*squares))

def std(*args):
	mean = avg(*args)
	deviations = [(float(x) - mean) for x in args]
	return rms(*deviations)

def set_BASE(base):
	global BASE
	BASE = base

def load_ccdred():
	iraf.noao(_doprint=0)
	iraf.imred(_doprint=0)
	iraf.ccdred(_doprint=0)

def load_imgeom():
	iraf.images(_doprint=0)
	iraf.imgeom(_doprint=0)

def load_apextract():
	iraf.noao(_doprint=0)
	iraf.twodspec(_doprint=0)
	iraf.apextract(_doprint=0)

def load_onedspec():
	iraf.noao(_doprint=0)
	iraf.onedspec(_doprint=0)

def load_kpnoslit():
	iraf.imred(_doprint=0)
	iraf.kpnoslit(_doprint=0)

def load_astutil():
	iraf.astutil(_doprint=0)

def zerocombine(input, **kwargs):
	load_ccdred()
	iraf.zerocombine.unlearn()
	iraf.zerocombine(input = input, **kwargs)

def flatcombine(input, **kwargs):
	load_ccdred()
	kwargs.setdefault('process', 'no')
	iraf.flatcombine.unlearn()
	iraf.flatcombine(input = input, **kwargs)

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

def get_data(name):
	raw_data = get_raw_data(name)
	if 'data' not in raw_data:
		types = raw_data['types'][:]
		angles = get_angles(raw_data['coord'])
		sections, size = get_sections(raw_data['coord'])
		data = []
		for i, angle in enumerate(angles):
			data.append({'angle':angle, 'section':sections[i], 
				'size':size[i], 'type':types[i], 'number':i})
		write_data(name, data)
	else:
		data = raw_data['data']
	return data

def write_data(name, data):
	raw_data = get_raw_data(name)
	raw_data.update({'data':data})
	write_raw_data(name, raw_data)

def write_raw_data(name, raw_data):
	fn = os.path.join(BASE, 'input/%s.json' % name)
	data_file = open(fn, 'w')
	json.dump(raw_data, data_file)
	data_file.close()

def get_raw_data(name):
	fn = os.path.join(BASE, 'input/%s.json' % name)
	data_file = open(fn, 'r')
	raw_data = json.load(data_file)
	data_file.close()
	return raw_data

def set_value(name, value_name, value):
	raw_data = get_raw_data(name)
	raw_data.update({value_name: value})
	write_raw_data(name, raw_data)

def get_value(name, value_name):
	raw_data = get_raw_data(name)
	return raw_data[value_name]

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
		start = int(round(avg(start1, start2)))
		end = int(round(avg(end1, end2)))
		sections.append('[1:2048,%s:%s]' % (start, end))
		size.append(end - start)
	return sections, size

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

def rotate(input, output, angle, **kwargs):
	load_imgeom()
	iraf.rotate.unlearn()
	iraf.rotate(input=input, output=output, rotation=-angle, **kwargs)

def imcopy(input, output, **kwargs):
	iraf.imcopy.unlearn()
	iraf.imcopy(input=input, output=output, **kwargs)

def rotate_galaxy(name, comp):
	data = get_data(name)
	os.mkdir('%s/rot' % name)
	for i, item in enumerate(data):
		num = zerocount(i)
		rotate("%s/base" % name, '%s/rot/%s' % (name, num), item['angle'])
		rotate('@lists/%s' % comp, '%s/rot/%sc' % (name, num), item['angle'])

def imcopy_galaxy(name):
	data = get_data(name)
	os.mkdir('%s/slice' % name)
	for i, item in enumerate(data):
		num = zerocount(i)
		imcopy('%s/rot/%s%s' % (name, num, item['section']), '%s/slice/%s' % (name, num))
		imcopy('%s/rot/%sc%s' % (name, num, item['section']), '%s/slice/%sc' % (name, num))

def apsum_galaxy(name):
	data = get_data(name)
	os.mkdir('%s/sum' % name)
	for i, item in enumerate(data):
		num = zerocount(i)
		apsum('%s/slice/%s' % (name, num), '%s/sum/%s.1d' % (name, num), item['section'])
		apsum('%s/slice/%sc' % (name, num), '%s/sum/%sc.1d' % (name, num), item['section'])
		namefix('%s/sum/%s.1d' % (name, num))
		namefix('%s/sum/%sc.1d' % (name, num))

def namefix(name):
	os.rename('%s.0001.fits' % name, '%s.fits' % name)

def reidentify_galaxy(name, reference):
	data = get_data(name)
	for i, item in enumerate(data):
		num = zerocount(i)
		reidentify(reference, '%s/%sc.1d.0001' % (name, num))

def hedit_galaxy(name):
	data = get_data(name)
	for i, item in enumerate(data):
		num = zerocount(i)
		hedit('%s/sum/%s.1d' % (name, num), 'REFSPEC1', '%s/sum/%sc.1d' % (name, num))

def dispcor_galaxy(name):
	data = get_data(name)
	for i, item in enumerate(data):
		num = zerocount(i)
		dispcor('%s/sum/%s.1d' % (name, num), '%s/disp/%s.1d' % (name, num))

def sky_subtract(name, spectra, sky, lines):
	num = zerocount(spectra['number'])
	guess = guess_scaling(name, spectra, sky, lines)
	# fmin
	os.mkdir('%s/tmp/%s' % (name, num))
	xopt = scipy.optimize.fmin(get_std_sky, guess, args=(name, num, lines), xtol=0.001)
	return xopt
	# annealing
	#anneal_out = scipy.optimize.anneal(get_std_sky, guess, args=(name, num), lower=0, upper=20, T0=0.4)
	#return anneal_out[0]

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

def get_alt_std_sky(scale, name, num):
	scale = float(scale)
	sky = '%s/sky.1d' % name
	scaled_sky = '%s/tmp/%s/%s.sky' % (name, num, scale)
	in_fn = '%s/disp/%s.1d' % (name, num)
	out_fn = '%s/tmp/%s/%s.1d' % (name, num, scale)
	sarith(sky, '*', scale, scaled_sky)
	sarith(in_fn, '-', scaled_sky, out_fn)
	fits = pyfits.open('%s.fits' % out_fn)
	loc1 = get_wavelength_location(fits, 5600)
	loc2 = get_wavelength_location(fits, 7000)
	deviation = std(*fits[0].data[loc1:loc2])
	return deviation

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

def get_wavelength_location(hdulist, wavelength):
	headers = hdulist[0].header
	data = hdulist[0].data
	start = headers['CRVAL1']
	step = headers['CDELT1']
	tmp = wavelength - start
	number = round(tmp / step)
	return number

def find_line_peak(hdulist, wavelength, search):
	number = get_wavelength_location(hdulist, wavelength)
	data = hdulist[0].data
	search = range(int(number - search), int(number + search))
	list = [data[i] for i in search]
	peak = max(list)
	peak_num = search[list.index(peak)]
	return peak_num

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

def get_continuum(upcont_num, downcont_num, data, search=5):
	data = data.tolist()
	values = data[upcont_num:(upcont_num + 3)]
	values.extend(data[(downcont_num - 3):downcont_num])
	return rms(*values)

def regenerate_sky(name, i, data):
	num = zerocount(i)
	sky_level = data[i]['sky_level']
	in_sky = '%s/sky.1d' % name
	tmp_sky = '%s/tmp/%s.sky.1d' % (name, num)
	in_fn = '%s/disp/%s.1d' % (name, num)
	tmp_fn = '%s/tmp/%s.1d' % (name, num)
	sarith(in_sky, '*', sky_level, tmp_sky)
	sarith(in_fn, '-', tmp_sky, tmp_fn)
	out_fn = '%s/sub/%s.1d' % (name, num)
	out_sky = '%s/sky/%s.sky.1d' % (name, num)
	subprocess.call(['rm', '-f', '%s.fits' % out_fn])
	subprocess.call(['rm', '-f', '%s.fits' % out_sky])
	imcopy(tmp_sky, out_sky)
	imcopy(tmp_fn, out_fn)

def sky_subtract_galaxy(name, lines):
	data = get_data(name)
	sky = '%s/sky.1d' % name
	os.mkdir('%s/tmp' % name)
	for i, item in enumerate(data):
		if item.has_key('sky_level'):
			regenerate_sky(name, i, data)
		else:
			num = zerocount(i)
			xopt = float(sky_subtract(name, item, sky, lines))
			print "\tSolution for %s: %s" % (num, xopt)
			print "\tSolution divided by width: %s" % (xopt / item['size'])
			tmp_fn = '%s/tmp/%s/%s.1d' % (name, num, xopt)
			tmp_sky = '%s/tmp/%s/%s.sky.1d' % (name, num, xopt)
			out_fn = '%s/sub/%s.1d' % (name, num)
			out_sky  = '%s/sky/%s.sky.1d' % (name, num)
			imcopy(tmp_fn, out_fn)
			imcopy(tmp_sky, out_sky)	
			data[i].update({'sky_level':xopt})
	write_data(name, data)
	subprocess.call(['rm', '-rf', '%s/tmp' % name])

def print_size(name, list=''):
	data = get_data(name)
	if list == '':
		list = range(len(data))
	for i in list:
		print i, data[i]['size']

def scale_spectra(input, scale, output):
	sarith(input, '/', scale, output)

def combine_sky_spectra(name, scale=False, **kwargs):
	data = get_data(name)
	list = []
	for i, item in enumerate(data):
		if item['type'] == 'NIGHTSKY':
			list.append(i)
	if scale == True:
		flist = []
		for spectra in list:
			scale = data[spectra]['size']
			num = zerocount(spectra)
			sarith('%s/disp/%s.1d' % (name, num), '/', scale, 
				'%s/sky/%s.scaled' % (name, num))
			flist.append('%s/sky/%s.scaled' % (name, num))
	else:
		flist = []
		for spectra in list:
			num = zerocount(spectra)
			flist.append('%s/disp/%s.1d' % (name, num))
	scombine(list_convert(flist), '%s/sky.1d' % name, **kwargs)

def list_convert(list):
	str = list.pop(0)
	for item in list:
		str += ', %s' % item
	return str

def setairmass_galaxy(name):
	data = get_data(name)
	for i, item in enumerate(data):
		num = zerocount(i)
		setairmass('%s/sub/%s.1d' % (name, num))

def calibrate_galaxy(name, calibration, prefix=''):
	data = get_data(name)
	sens = '%s/sens' % calibration
	for i, item in enumerate(data):
		num = zerocount(i)
		calibrate('%s/sub/%s.1d' % (name, num), '%s/cal/%s.1d' % (name, num))

def zerocount(i):
	if i < 10:
		return "00%s" % i
	elif i < 100:
		return '0%s' % i
	else:
		return '%s' % i

def fix_image(image, mask):
	hedit(image, 'BPM', mask)
	fixpix(image, 'BPM', verbose="yes")

def fix_galaxy(name, mask):
	imcopy('@lists/%s' % name, '%s/@lists/%s' % (name, name))
	fix_image('%s/@lists/%s' % (name, name), mask)
	
def setairmass(images, **kwargs):
	load_kpnoslit()
	iraf.setairmass.unlearn()
	iraf.setairmass(images=images, **kwargs)

def fixpix(image, mask, **kwargs):
	iraf.fixpix.unlearn()
	iraf.fixpix(images = image, masks = mask, **kwargs)

def calibrate(input, sens, output, **kwargs):
	load_kpnoslit()
	iraf.calibrate.unlearn()
	iraf.calibrate(input=input, output=output, sens=sens, **kwargs)

def dispcor(input, output, **kwargs):
	load_onedspec()
	iraf.dispcor.unlearn()
	iraf.dispcor(input=input, output=output, **kwargs)

def scombine(input, output, **kwargs):
	load_onedspec()
	iraf.scombine.unlearn()
	iraf.scombine(input=input, output=output, **kwargs)

def hedit(images, fields, value, **kwargs):
	kwargs.setdefault('add', 'yes')
	kwargs.setdefault('verify', 'no')
	iraf.hedit.unlearn()
	iraf.hedit(images=images, fields=fields, value=value, **kwargs)
	
def reidentify(reference, images, **kwargs):
	load_onedspec()
	kwargs.setdefault('verbose', 'yes')
	kwargs.setdefault('interactive', 'no')
	kwargs.setdefault('shift', 'INDEF')
	kwargs.setdefault('search', 'INDEF')
	iraf.reidentify.unlearn()
	iraf.reidentify(reference=reference, images=images, **kwargs)

def set_aperture(input, section):
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

def sarith(input1, op, input2, output, **kwargs):
	load_onedspec()
	iraf.sarith.unlearn()
	iraf.sarith(input1=input1, op=op, input2=input2, output=output, 
		**kwargs)

def setairmass(name, **kwargs):
	load_astutil()
	iraf.setairmass.unlearn()
	iraf.setairmass(images=name, **kwargs)
