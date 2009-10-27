import math
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

def slice_galaxy(name, comp):
	cood_data = coodproc('input/%s_cood.json' % name)
	for i in range(len(cood_data)):
		rotate("%s/base" % name, '%s/r%s' % (name, i),
			cood_data[i]['angle'])
		rotate(comp, '%s/rc%s' % (name, i),
			cood_data[i]['angle'])
		imcopy('%s/r%s' % (name, i), '%s/s%s' % (name, i),
			cood_data[i]['section'])
		imcopy('%s/rc%s' % (name, i), '%s/sc%s' % (name, i),
			cood_data[i]['section'])
