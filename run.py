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
#after noting down slice begins/ends
	#rotate_galaxy('ngc4725', 'cghn30030')
	#imcopy_galaxy('ngc4725')
	#apsum_galaxy('ngc4725')
# did a manual identify on 16c, manual reidentify on the other comps
	#hedit_galaxy('ngc4725')
	#dispcor_galaxy('ngc4725')
#ngc3169
	#ccdproc('@lists/ngc3169', zero="Zero", flat="Flat1")
	if not os.path.isdir('./ngc3169'):
		os.mkdir('./ngc3169')
	#combine('@lists/ngc3169', 'ngc3169/base')
	# noted slice starts/ends
	#rotate_galaxy('ngc3169', 'cghn30022')
	#imcopy_galaxy('ngc3169')
	#apsum_galaxy('ngc3169')

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
