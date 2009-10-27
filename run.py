import sys, os, math
import simplejson as json
from pyraf import iraf
from lib import *

def n3():
	location = "../n3"
	os.chdir(location)
	zerocombine("@lists/zero")
	flatcombine("@lists/flat1", output = "Flat1")
	flatcombine("@lists/flat2", output = "Flat2")
#ngc4725
	ccdproc("@lists/ngc4725", zero="Zero", flat="Flat2")
	combine("@lists/ngc4725", "ngc4725/base")
	cood_data = coodproc('input/ngc4725_cood.json')
	for i in range(len(cood_data)):
		rotate('ngc4725/base', 'ngc4725/r%s' % i,
			cood_data[i]['angle'])
		rotate('cghn30030', 'ngc4725/rc%s' %i,
			cood_data[i]['angle'])
		imcopy('ngc4725/r%s' % i, 'ngc4725/s%s' % i,
			cood_data[i]['section'])
		imcopy('ngc4725/rc%s' % i, 'ngc4725/sc%s' % i,
			cood_data[i]['section'])

n3()
