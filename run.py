import sys, os, math, subprocess
import simplejson as json
from pyraf import iraf
from lib import *

def n3_initial():
	zerocombine("@lists/zero")
	flatcombine("@lists/flat1", output = "Flat1")
	flatcombine("@lists/flat2", output = "Flat2")
#ngc4725
	ccdproc("@lists/ngc4725", zero="Zero", flat="Flat2", fixfile="Mask")
	os.mkdir('./ngc4725')
	combine("@lists/ngc4725", "ngc4725/base")
#ngc3169
	ccdproc('@lists/ngc3169', zero="Zero", flat="Flat1", fixfile="Mask")
	os.mkdir('./ngc3169')
	combine('@lists/ngc3169', 'ngc3169/base')
#feige34
	ccdproc('@lists/feige34', zero="Zero", flat='Flat1', fixfile="Mask")
	os.mkdir('./feige34')
	combine('@lists/feige34', 'feige34/base')
#pg1708+602
	ccdproc('@lists/pg1708+602', zero='Zero', flat='Flat2', fixfile='Mask')
	os.mkdir('./pg1708+602')
	combine('@lists/pg1708+602', 'pg1708+602/base')

def n3_slices():
#ngc4725
	rotate_galaxy('ngc4725', '@lists/henear2')
	imcopy_galaxy('ngc4725')
	apsum_galaxy('ngc4725')
#ngc3169	
	rotate_galaxy('ngc3169', '@lists/henear1')
	imcopy_galaxy('ngc3169')
	apsum_galaxy('ngc3169')
#feige34
	rotate_galaxy('feige34', '@lists/henear1')
	imcopy_galaxy('feige34')
	apsum_galaxy('feige34')
#pg1708+602
	rotate_galaxy('pg1708+602', '@lists/henear2')
	imcopy_galaxy('pg1708+602')
	apsum_galaxy('pg1708+602')
	
def n3_dispersion():
#ngc3169
	hedit_galaxy('ngc3169')
	dispcor_galaxy('ngc3169')
	combine_sky_spectra('ngc3169', scale=True)
	sky_subtract_galaxy('ngc3169', scale=True)
#feige34
	hedit_galaxy('feige34')
	dispcor_galaxy('feige34')
	combine_sky_spectra('feige34', scale=True)
	sky_subtract_galaxy('feige34', scale=True)
#pg1708+602
	hedit_galaxy('pg1708+602')
	dispcor_galaxy('pg1708+602')
	combine_sky_spectra('pg1708+602', scale=True)
	sky_subtract_galaxy('pg1708+602', scale=True)
#ngc4725
	hedit_galaxy('ngc4725')
	dispcor_galaxy('ngc4725')
	set_value('ngc4725', 'use_sky', 'ngc3169')
	sky_subtract_galaxy('ngc4725', scale=True)

def n3_calibrate():
	calibrate_galaxy('ngc3169', 'feige34')
	calibrate_galaxy('ngc4725', 'pg1708+602')

def n3():
	location = "../n3"
	os.chdir(location)
	set_BASE(os.getcwd())
	n3_initial()
	#then make sure that you've got strip coordinate files
	n3_slices()
	#then identify everything
	#n3_dispersion()
	#then run standard and sensfunc manually
	#n3_calibrate()
	

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
