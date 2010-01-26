from lib import *
import sys, os, numpy

def main():
	#autoscale('ngc3169', .5, 2, .1)
	optimizescale('ngc3169')

def optimizescale(name):
	location = "../n3"
	os.chdir(location)
	set_BASE(os.getcwd())
	try:
		os.mkdir('%s/test' % name)
	except:
		pass
	sky = '%s/sky.1d' % name
	data = get_data(name)
	try:
		os.mkdir('%s/test/solutions' % name)
	except:
		pass
	for i, item in enumerate(data):
		num = zerocount(i)
		xopt = float(sky_subtraction_opt(name, item, sky))
		print "\tSolution for %s: %s" % (num, xopt)
		print "\tSolution divided by width: %s" % (xopt / item['size'])
		imcopy('%s/test/%s/%s.1d' % (name, num, xopt), '%s/test/solutions/%s' % (name, num))

def autoscale(name, min, max, step):
	location = "../n3"
	os.chdir(location)
	set_BASE(os.getcwd())
	try:
		os.mkdir('%s/test' % name)
	except:
		pass
	sky = '%s/sky.1d' % name
	data = get_data(name)
	for magic_number in numpy.arange(min, max, step):
		try:
			os.mkdir('%s/test/%s' % (name, magic_number))
		except:
			pass
	 	for i, item in enumerate(data):
			num = zerocount(i)
			scale = magic_number * get_scaling(name, item, sky)
			scaled_sky = '%s/test/%s/%s.sky' % (name, magic_number, num)
			sarith(sky, '*', scale, scaled_sky)
			sarith('%s/disp/%s.1d' % (name, num), '-', scaled_sky, '%s/test/%s/%s.1d' % (name, magic_number, num))

def manual_scaling(name, min, max, step):
	location = "../n3"
	os.chdir(location)
	set_BASE(os.getcwd())
	try:
		os.mkdir('%s/test' % name)
	except:
		pass
	sky = '%s/sky.1d' % name
	data = get_data(name)
	for magic_number in numpy.arange(min, max, step):
		try:
			os.mkdir('%s/test/%s' % (name, magic_number))
		except:
			pass
	 	for i, item in enumerate(data):
			num = zerocount(i)
			scale = magic_number * item['size']
			scaled_sky = '%s/test/%s/%s.sky' % (name, magic_number, num)
			sarith(sky, '*', scale, scaled_sky)
			sarith('%s/disp/%s.1d' % (name, num), '-', scaled_sky, '%s/test/%s/%s.1d' % (name, magic_number, num))

main()
