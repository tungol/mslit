import math, os
import simplejson as json
from pyraf import iraf

def avg(*args):
	floatNums = [float(x) for x in args]
	return sum(floatNums) / len(args)

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
		for i in range(len(angles)):
			data.append({'angle':angles[i], 'section':sections[i], 
				'size':size[i], 'type':types[i]})
		write_data(name, data)
	else:
		data = raw_data['data']
	return data

def write_data(name, data):
	raw_data = get_raw_data(name)
	raw_data.update['data':data]
	write_raw_data(name, raw_data)

def write_raw_data(name, raw_data):
	fn = '../input/%s.json' % name
	data_file = open(fn, 'w')
	json.dump(data_file, raw_data)
	data_file.close()

def get_raw_data(name):
	fn = '../input/%s.json' % name
	data_file = open(fn, 'r')
	raw_data = json.load(data_file)
	file.close()
	return raw_data

def set_value(name, value_name, value):
	raw_data = get_raw_data(name)
	raw_data['data'].update({value_name: value})
	write_raw_data(name, raw_data)

def get_sections(raw_data):
	columns = raw_data.keys()
	list1 = raw_data[columns[0]]
	list2 = raw_data[columns[1]]
	sections = []
	size = []
	for i in range(len(list1)):
		start1 = list1[i]['start']
		end1 = list1[i]['end']
		start2 = list2[i]['start']
		end2 = list2[i]['end']
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
	for i in range(len(list1)):		
		start1 = list1[i]['start']
		end1 = list1[i]['end']
		start2 = list2[i]['start']
		end2 = list2[i]['end']
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

def imcopy(input, output, section, **kwargs):
	iraf.imcopy.unlearn()
	tmp = input + section
	iraf.imcopy(input=tmp, output=output, **kwargs)

def rotate_galaxy(name, comp):
	data = get_data(name)
	os.chdir(name)
	comp = '../' + comp
	for i in range(len(data)):
		si = zerocount(i)
		rotate("base", 'r%s' % si, data[i]['angle'])
		rotate(comp, 'r%sc' % si, data[i]['angle'])
	os.chdir('..')

def imcopy_galaxy(name):
	data = get_data(name)
	os.chdir(name)
	for i in range(len(data)):
		si = zerocount(i)
		imcopy('r%s' % si, 's%s' % si, data[i]['section'])
		imcopy('r%sc' % si, 's%sc' % si, data[i]['section'])
	os.chdir('..')

def apsum_galaxy(name):
	data = get_data(name)
	os.chdir(name)
	for i in range(len(data)):
		si = zerocount(i)
		apsum('s%s' % si, '%s.1d' % si, data[i]['section'])
		apsum('s%sc' % si, '%sc.1d' % si, data[i]['section'])
	os.chdir('..')

def reidentify_galaxy(name, reference):
	data = get_data(name)
	os.chdir(name)
	for i in range(len(data)):
		si = zerocount(i)
		reidentify(reference, '%sc.1d.0001' % si)
	os.chdir('..')

def hedit_galaxy(name):
	data = get_data(name)
	os.chdir(name)
	for i in range(len(data)):
		si = zerocount(i)
		hedit('%s.1d.0001' % si, 'REFSPEC1', '%sc.1d.0001' % si)
	os.chdir('..')

def dispcor_galaxy(name):
	data = get_data(name)
	os.chdir(name)
	for i in range(len(data)):
		si = zerocount(i)
		dispcor('%s.1d.0001' % si, 'd%s.1d' % si)
	os.chdir('..')

def sky_subtract_galaxy(name, sky, prefix='', scale=False):
	data = get_data(name)
	os.chdir(name)
	if scale == True:
		for i in range(len(data)):
			si = zerocount(i)
			scaled_sky = '%ssky.1d.%s' % (prefix, si)
			sarith(sky, '*', data[i]['size'], scaled_sky)
			sarith('d%s.1d' % si, '-', scaled_sky, '%sds%s.1d' % (prefix, si))
	else:
		for i in range(len(data)):
			si = zerocount(i)
			sarith('d%s.1d' % si, '-', sky, 
				'%sds%s.1d' % (prefix, si))
	os.chdir('..')

def print_size(name, list=''):
	data = get_data(name)
	if list == '':
		list = range(len(data))
	for i in list:
		print i, data[i]['size']

def scale_spectra(input, scale, output):
	sarith(input, '/', scale, output)

def combine_sky_spectra(name, out='sky.1d', scale=False, **kwargs):
	data = get_data(name)
	os.chdir(name)
	list = []
	for i, item in enumerate(data):
		if item['type'] == 'NIGHTSKY':
			list.append(i)
	if scale == True:
		flist = []
		for spectra in list:
			scale = data[spectra]['size']
			i = zerocount(spectra)
			sarith('d%s.1d' % i, '/', scale, 
				'd%s.1d.scaled' % i)
			flist.append('d%s.1d.scaled' % i)
	else:
		flist = []
		for spectra in list:
			flist.append('d%s.1d' % i)
	scombine(list_convert(flist), out, **kwargs)
	os.chdir('..')

def list_convert(list):
	str = list.pop(0)
	for item in list:
		str += ', %s' % item
	return str

def calibrate_galaxy(name, sens, prefix=''):
	data = get_data(name)
	os.chdir(name)
	for i in range(len(data)):
		si = zerocount(i)
		calibrate('%sds%s.1d' % (prefix, si), sens, '%sdsc%s.1d' % (prefix, si))
	os.chdir('..')

def zerocount(i):
	if i < 10:
		return "00%s" % i
	elif i < 100:
		return '0%s' % i
	else:
		return '%s' % i

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
