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
	kwargs.setdefault('fixpix', 'no')
	kwargs.setdefault('darkcor', 'no')
	kwargs.setdefault('biassec', '[2049:2080,1:501]')
	kwargs.setdefault('trimsec', '[1:2048,1:501]')
	iraf.ccdproc.unlearn()
	iraf.ccdproc(images=images, **kwargs)

def combine(input, output, **kwargs):
	load_ccdred()
	iraf.combine.unlearn()
	iraf.combine(input=input, output=output, **kwargs)

def coodproc(cood_fn):
	cood_file = open(cood_fn, 'r')
	cood = json.load(cood_file)
	cood_file.close()
	angles = get_angles(cood)
	sections = get_sections(cood)
	tmp = []
	for i in range(len(angles)):
		tmp.append({'angle':angles[i], 'section':sections[i]})
	return tmp

def get_sections(cood):
	columns = cood.keys()
	list1 = cood[columns[0]]
	list2 = cood[columns[1]]
	sections = []
	for i in range(len(list1)):
		start1 = list1[i]['start']
		end1 = list1[i]['end']
		start2 = list2[i]['start']
		end2 = list2[i]['end']
		start = int(round(avg(start1, start2)))
		end = int(round(avg(end1, end2)))
		sections.append('[1:2048,%s:%s]' % (start, end))
	return sections

def get_angles(cood):
	columns = cood.keys()
	list1 = cood[columns[0]]
	list2 = cood[columns[1]]
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
	cood_data = coodproc('input/%s_cood.json' % name)
	os.chdir(name)
	comp = '../' + comp
	for i in range(len(cood_data)):
		if i < 10:
			si = "00%s" % i
		elif i < 100:
			si = '0%s' % i
		else:
			si = '%s' % i
		rotate("base", 'r%s' % si, cood_data[i]['angle'])
		rotate(comp, 'r%sc' % si, cood_data[i]['angle'])
	os.chdir('..')

def imcopy_galaxy(name):
	cood_data = coodproc('input/%s_cood.json' % name)
	os.chdir(name)
	for i in range(len(cood_data)):
		if i < 10:
			si = "00%s" % i
		elif i < 100:
			si = '0%s' % i
		else:
			si = '%s' % i
		imcopy('r%s' % si, 's%s' % si, cood_data[i]['section'])
		imcopy('r%sc' % si, 's%sc' % si, cood_data[i]['section'])
	os.chdir('..')

def apsum_galaxy(name):
	cood_data = coodproc('input/%s_cood.json' % name)
	os.chdir(name)
	for i in range(len(cood_data)):
		if i < 10:
			si = "00%s" % i
		elif i < 100:
			si = '0%s' % i
		else:
			si = '%s' % i
		apsum('s%s' % si, '%s.1d' % si, cood_data[i]['section'])
		apsum('s%sc' % si, '%sc.1d' % si, cood_data[i]['section'])
	os.chdir('..')

def reidentify_galaxy(name, reference):
	cood_data = coodproc('input/%s_cood.json' % name)
	os.chdir(name)
	for i in range(len(cood_data)):
		if i < 10:
			si = "00%s" % i
		elif i < 100:
			si = '0%s' % i
		else:
			si = '%s' % i
		reidentify(reference, '%sc.1d.0001' % si)
	os.chdir('..')

def hedit_galaxy(name):
	cood_data = coodproc('input/%s_cood.json' % name)
	os.chdir(name)
	for i in range(len(cood_data)):
		if i < 10:
			si = "00%s" % i
		elif i < 100:
			si = '0%s' % i
		else:
			si = '%s' % i
		hedit('%s.1d.0001' % si, 'REFSPEC1', '%sc.1d.0001' % si)
	os.chdir('..')

def dispcor_galaxy(name):
	cood_data = coodproc('input/%s_cood.json' % name)
	os.chdir(name)
	for i in range(len(cood_data)):
		if i < 10:
			si = "00%s" % i
		elif i < 100:
			si = '0%s' % i
		else:
			si = '%s' % i
		dispcor('%s.1d.0001' % si, 'd%s.1d.0001' % si)
	os.chdir('..')

def sarith_galaxy(name, sky):
	cood_data = coodproc('input/%s_cood.json' % name)
	os.chdir(name)
	for i in range(len(cood_data)):
		si = zerocount(i)
		sarith('d%s.1d.0001' % si, '-', sky, 'ds%s.1d.0001' % si)

def calibrate_galaxy(name, sens):
	cood_data = coodproc('input/%s_cood.json' % name)
	os.chdir(name)
	for i in range(len(cood_data)):
		si = zerocount(i)
		calibrate('ds%s.1d.0001' % si, sens, 'dsc%s.1d.0001' % si)

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
