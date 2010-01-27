import sys
from lib import *

def main(name, number, op, value):
	location = "../n3"
	os.chdir(location)
	set_BASE(os.getcwd())
	i = int(number)
	num = zerocount(i)
	value = float(value)
	os.mkdir('%s/tmp' % name)
	data = get_data(name)
	item = data[i]
	sky_level = item['sky_level']
	if op == '+':
		new_sky_level = sky_level + value
	elif op == '-':
		new_sky_level = sky_level - value
	data[i].update({'sky_level':new_sky_level})
	write_data(name, data)
	regenerate_sky(name, i, data)
	subprocess.call(['rm', '-rf', '%s/tmp' % name])

main(*sys.argv[1:])
