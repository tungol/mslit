import sys, os, math, subprocess, time
import simplejson as json
from pyraf import iraf
from lib import *

def init_galaxy(name, mask, zero, flat):
	os.mkdir(name)
	fix_galaxy(name, mask)
	ccdproc('%s/@lists/%s' % (name, name), zero=zero, flat=flat)
	combine('%s/@lists/%s' % (name, name), '%s/base' % name)

def n3_initial():
	zerocombine("@lists/zero")
	flatcombine("@lists/flat1", output = "Flat1")
	flatcombine("@lists/flat2", output = "Flat2")
	fix_image('Flat1', 'Mask2.pl')
	fix_image('Flat2', 'Mask2.pl')
	fix_image('Zero', 'Mask2.pl')
	init_galaxy('ngc4725', 'Mask2.pl', 'Zero', 'Flat2')
	init_galaxy('ngc3169', 'Mask2.pl', 'Zero', 'Flat1')
	init_galaxy('feige34', 'Mask2.pl', 'Zero', 'Flat1')
	init_galaxy('pg1708+602', 'Mask2.pl', 'Zero', 'Flat2')

def slice_galaxy(name, comp):
	rotate_galaxy(name, comp)
	imcopy_galaxy(name)
	apsum_galaxy(name)
	
def n3_slices():
	slice_galaxy('ngc4725', 'henear2')
	slice_galaxy('ngc3169', 'henear1')
	slice_galaxy('feige34', 'henear1')
	slice_galaxy('pg1708+602', 'henear2')
	#some folders needed in the next part
	os.makedirs('database/idngc4725/sum')
	os.makedirs('database/idngc3169/sum')
	os.makedirs('database/idfeige34/sum')
	os.makedirs('database/idpg1708+602/sum')

def disp_galaxy(name):
	os.mkdir('%s/disp' % name)
	hedit_galaxy(name)
	dispcor_galaxy(name)
	
def n3_dispersion():
	disp_galaxy('ngc3169')
	disp_galaxy('feige34')
	disp_galaxy('pg1708+602')
	disp_galaxy('ngc4725')

def skies(name, lines):
	#os.mkdir('%s/sky' % name)
	#combine_sky_spectra(name, scale=True)
	os.mkdir('%s/sub' % name)
	sky_subtract_galaxy(name, lines)

def n3_skies():
	lines = [5893, 5578, 6301, 6365]
#ngc3169
	#skies('ngc3169', lines)
#feige34
	#skies('feige34', lines)
#pg1708+602
	#skies('pg1708+602', lines)
#ngc4725
	lines.remove(5578)
	#os.mkdir('ngc4725/sky')
	#imcopy('ngc3169/sky.1d', 'ngc4725/sky.1d')
	os.mkdir('ngc4725/sub')
	sky_subtract_galaxy('ngc4725', lines)

def n3_calibrate():
	calibrate_galaxy('ngc3169', 'feige34')
	calibrate_galaxy('ngc4725', 'pg1708+602')

def n3():
	location = "../n3"
	os.chdir(location)
	set_BASE(os.getcwd())
	#n3_initial()
	#then make sure that you've got strip coordinate files
	#n3_slices()
	#then identify everything
	#n3_dispersion()
	n3_skies()
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
