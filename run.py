import sys, os, math, subprocess
import simplejson as json
from pyraf import iraf
from lib import *

def n3_inital():
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
	rotate_mask('ngc4725', '@lists/henear2')
	imcopy_mask('ngc4725')
	apsum_mask('ngc4725')
#ngc3169	
	rotate_mask('ngc3169', '@lists/henear1')
	imcopy_mask('ngc3169')
	apsum_mask('ngc3169')
#feige34
	rotate_mask('feige34', '@lists/henear1')
	imcopy_mask('feige34')
	apsum_mask('feige34')
#pg1708+602
	rotate_mask('pg1708+602', '@lists/henear2')
	imcopy_mask('pg1708+602')
	apsum_mask('pg1708+602')
	
def n3_dispersion():
#ngc4725
	hedit_mask('ngc4725')
	dispcor_mask('ngc4725')
#ngc3169
	hedit_mask('ngc3169')
	dispcor_mask('ngc3169')
#feige34
	hedit_mask('feige34')
	dispcor_mask('feige34')


def n3():
	location = "../n3"
	os.chdir(location)
	n3_initial()
	#then make sure that you've got strip coordinate files
	n3_slices()
	#then identify everything
	n3_dispersion()
	#then run standard and sensfunc manually
#flux calibration and sky subtraction
	#sky = '../ngc3169/sky.average.1d'
	#sens = '../feige34/feige34.sens'
	#sky_list = [0, 2, 18, 24]
	#combine_sky_spectra('ngc3169', sky_list, scale=True, combine='median', reject='avsigclip', out='no_setup.sky.1d')
	#sky_subtract_mask('ngc3169', 'no_setup.sky.1d', prefix='no_setup/', scale=True)
	#sky_subtract_mask('feige34', '../ngc3169/no_setup.sky.1d', scale=True)
	#calibrate_mask('ngc3169', '../feige34/sfeige34.sens', prefix='sfeige34/')
	

def n6():
	location = '../n6'
	os.chdir(location)
	zerocombine('@lists/zero')
	flatcombine('@lists/flat1', output = "Flat1")
	flatcombine('@lists/flat2', output = 'Flat2')
	#ngc4725
	ccdproc('@lists/ngc4725', zero="Zero", flat="Flat2")
	combine("@lists/ngc4725", "ngc4725/base")
	slice_mask("ngc4725")

n3()
