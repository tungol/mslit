from lib import *
import sys

location = "../n3"
os.chdir(location)
set_BASE(os.getcwd())
name = 'ngc3169'
data = get_data(name)
sky = get_value(name, 'sky_spectra')
scale = get_scaling(name, data[20], sky)
print scale
scale = float(sys.argv[1])
num = zerocount(6)
scaled_sky = '%s/test/sky.%s' % (name, scale)
sarith(sky, '*', scale, scaled_sky)
sarith('%s/corrected' % name, '-', scaled_sky, '%s/test/%s' % (name, scale))
