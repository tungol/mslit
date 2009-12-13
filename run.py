import sys, os, math, subprocess
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
	#os.mkdir('./ngc4725')
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
	#os.mkdir('./ngc3169')
	#combine('@lists/ngc3169', 'ngc3169/base')
	# noted slice starts/ends
	#rotate_galaxy('ngc3169', 'cghn30022')
	#imcopy_galaxy('ngc3169')
	#apsum_galaxy('ngc3169')
	#reidentified 000c.1d.001 using ngc4725/016c.1d.001
	#reidentified remaning comps using 000c.1d.001
	#hedit_galaxy('ngc3169')
	#dispcor_galaxy('ngc3169')
#flux correction (feige34)
	#ccdproc('cghn30017', zero="Zero", flat='Flat1')
	#os.mkdir('./feige34')
	#subprocess.call(['cp', 'cghn30017.fits', './feige34/base.fits'])
	#rotate_galaxy('feige34', 'cghn30022')
	#imcopy_galaxy('feige34')
	#apsum_galaxy('feige34')
	#manually ran identify
	#hedit_galaxy('feige34')
	#dispcor_galaxy('feige34')
	#then run standard and sensfunc manually
#flux calibration and sky subtraction
	#sky = '../ngc3169/sky.average.1d'
	sens = '../feige34/feige34.sens'
	#sky_list = [0, 2, 18, 24]
	#combine_sky_spectra('ngc3169', sky_list, scale=True, combine='median', reject='avsigclip', out='no_setup.sky.1d')
	#sky_subtract_galaxy('ngc3169', 'no_setup.sky.1d', prefix='no_setup/', scale=True)
	#sky_subtract_galaxy('feige34', '../ngc3169/no_setup.sky.1d', scale=True)
	calibrate_galaxy('ngc3169', '../feige34/sfeige34.sens', prefix='sfeige34/')
	

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
