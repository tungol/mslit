import sys, os, math
import simplejson as json
from pyraf import iraf
from lib import *

def n3():
	location = "../n3"
	os.chdir(location)
	#zerocombine("@lists/zero")
	#flatcombine("@lists/flat1", output = "Flat1")
	#flatcombine("@lists/flat2", output = "Flat2")
#ngc4725
	#ccdproc("@lists/ngc4725", zero="Zero", flat="Flat2")
	if not os.path.isdir('./ngc4725'):
		os.mkdir('./ngc4725')
	#combine("@lists/ngc4725", "ngc4725/base")
	#rotate_galaxy('ngc4725', 'cghn30030')
	#imcopy_galaxy('ngc4725')
	#apsum_galaxy('ngc4725')
	#reidentify_galaxy('ngc4725', '016.1d.0001')
	hedit_galaxy('ngc4725')
	dispcor_galaxy('ngc4725')

def n6():
	location = '../n6'
	os.chdir(location)
	zerocombine('@lists/zero')
	flatcombine('@lists/flat1', output = "Flat1")
	flatcombine('@lists/flat2', output = 'Flat2')
	#ngc4725
	ccdproc('@lists/ngc4725', zero="Zero", flat="Flat2")
	combine("@lists/ngc4725", "ngc4725/base")
	slice_galaxy("ngc4725")

n3()
