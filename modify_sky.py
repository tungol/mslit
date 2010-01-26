import sys
from lib import *

def main(name, number, op, value):
	i = int(number)
	num = zerocount(i)
	value = float(value)
	os.mkdir('%s/tmp' % name)
	data = get_data(name)
	item = data[i]
	sky_level = item['sky_level']
	if op = '+':
		new_sky_level = sky_level + value
	elif op = '-':
		new_sky_level = sky_level - value
	sky = '%s/sky.1d' % name
	scaled_sky = '%s/tmp/%s.sky.1d' % (name, num)
	in_fn = '%s/disp/%s.1d' % (name, num)
	out_fn = '%s/tmp/%s.1d' % (name, num)
	sarith(sky, '*', scale, scaled_sky)
	sarith(in_fn, '-', scaled_sky, out_fn)
	loc = '%s/sub/%s.1d' % (name, num)
	sky_loc = '%s/sky/%s.sky.1d' % (name, num)
	subprocess.call(['rm', '-f', '%s.fits' % loc]) 
	subprocess.call(['rm', '-f', '%s.fits' % sky_loc]) 
	imcopy(scaled_sky, sky_loc, verbose='false')
	imcopy(out_fn, loc, verbose='false')
