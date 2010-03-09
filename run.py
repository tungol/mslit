import sys, os, math, subprocess, time
import simplejson as json
from pyraf import iraf
from lib import *

def zero_flats(mask):
	zerocombine("@lists/zero")
	flatcombine("@lists/flat1", output = "Flat1")
	flatcombine("@lists/flat2", output = "Flat2")
	fix_image('Flat1', mask)
	fix_image('Flat2', mask)
	fix_image('Zero', mask)

def init_galaxy(name, mask, zero, flat):
	os.mkdir(name)
	fix_galaxy(name, mask)
	ccdproc('%s/@lists/%s' % (name, name), zero=zero, flat=flat)
	combine('%s/@lists/%s' % (name, name), '%s/base' % name)

def slice_galaxy(name, comp):
	rotate_galaxy(name, comp)
	imcopy_galaxy(name)
	apsum_galaxy(name)
	#needed for next step
	os.makedirs('database/id%s/sum' % name)

def disp_galaxy(name):
	os.mkdir('%s/disp' % name)
	hedit_galaxy(name)
	dispcor_galaxy(name)

def skies(name, lines, use=''):
	os.mkdir('%s/sky' % name)
	if use == '':
		combine_sky_spectra(name, scale=True)
	else:
		imcopy('%s/sky.1d' % use, '%s/sky.1d' % name)
	os.mkdir('%s/sub' % name)
	sky_subtract_galaxy(name, lines)
	setairmass_galaxy(name)

def calibration(name, standard):
	os.mkdir('%s/cal' % name)
	calibrate_galaxy(name, standard)

def n3_initial():
	zero_flats('Mask2.pl')
	init_galaxy('ngc4725', 'Mask2.pl', 'Zero', 'Flat2')
	init_galaxy('ngc3169', 'Mask2.pl', 'Zero', 'Flat1')
	init_galaxy('feige34', 'Mask2.pl', 'Zero', 'Flat1')
	init_galaxy('pg1708+602', 'Mask2.pl', 'Zero', 'Flat2')
	
def n3_slices():
	slice_galaxy('ngc4725', 'henear2')
	slice_galaxy('ngc3169', 'henear1')
	slice_galaxy('feige34', 'henear1')
	slice_galaxy('pg1708+602', 'henear2')
	
def n3_dispersion():
	disp_galaxy('ngc3169')
	disp_galaxy('feige34')
	disp_galaxy('pg1708+602')
	disp_galaxy('ngc4725')

def n3_skies():
	lines = [5893, 5578, 6301, 6365]
	skies('ngc3169', lines)
	skies('feige34', lines)
	skies('pg1708+602', lines)
	lines.remove(5578)
	skies('ngc4725', lines, use='ngc3169')

def n3_calibrate():
	calibration('ngc3169', 'feige34')
	calibration('ngc4725', 'pg1708+602')

def n3():
	location = "../n3"
	os.chdir(location)
	set_BASE(os.getcwd())
	#n3_initial()
	#then make sure that you've got strip coordinate files
	#n3_slices()
	#then identify everything
	#n3_dispersion()
	#n3_skies()
	#then run standard and sensfunc manually
	#n3_calibrate()
	
def n6_initial():
	zero_flats('Mask.pl')
	init_galaxy('ngc2985', 'Mask.pl', 'Zero', 'Flat1')
	init_galaxy('ngc4725', 'Mask.pl', 'Zero', 'Flat2')
	init_galaxy('feige34', 'Mask.pl', 'Zero', 'Flat1')
	init_galaxy('feige66', 'Mask.pl', 'Zero', 'Flat2')

def n6_slices():
	slice_galaxy('ngc2985', 'henear1')
	slice_galaxy('ngc4725', 'henear2')
	slice_galaxy('feige34', 'henear1')
	slice_galaxy('feige66', 'henear2')

def n6_dispersion():
	disp_galaxy('ngc2985')
	disp_galaxy('ngc4725')
	disp_galaxy('feige34')
	disp_galaxy('feige66')

def n6_skies():
	lines = [5893, 5578, 6301, 6365]
	skies('ngc2985', lines)
	skies('ngc4725', lines)
	skies('feige34', lines)
	skies('feige66', lines)

def n6_calibrate():
	calibration('ngc2985', 'feige34')
	calibration('ngc4725', 'feige66')

def n6():
	location = "../n6"
	os.chdir(location)
	set_BASE(os.getcwd())
	#n6_initial()
	#then make sure that you've got strip coordinate files
	n6_slices()
	#then identify everything
	#n6_dispersion()
	#n6_skies()
	#then run standard and sensfunc manually
	#n6_calibrate()

n6()
