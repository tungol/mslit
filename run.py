import os
from div3lib import zero_flats, init_galaxy, slice_galaxy
from div3lib import disp_galaxy, skies, calibration

def n3_initial():
	""" combines zeros and flats, then runs ccdproc and combine """
	zero_flats('Mask.pl')
	init_galaxy('feige34', 'Mask.pl', 'Zero', 'Flat1')
	init_galaxy('ngc3169', 'Mask.pl', 'Zero', 'Flat1')
	init_galaxy('ngc4725', 'Mask.pl', 'Zero', 'Flat2')
	init_galaxy('pg1708+602', 'Mask.pl', 'Zero', 'Flat2')

def n3_slices():
	""" creates 2D slices and then 1D spectra """
	slice_galaxy('feige34', 'henear1', use='ngc3169')
	slice_galaxy('ngc3169', 'henear1')
	slice_galaxy('ngc4725', 'henear2')
	slice_galaxy('pg1708+602', 'henear2', use='ngc4725')

def n3_dispersion():
	""" applies dispersion correction """
	disp_galaxy('feige34', use='ngc3169')
	disp_galaxy('ngc3169')
	disp_galaxy('ngc4725')
	disp_galaxy('pg1708+602', use='ngc4725')

def n3_skies():
	""" performs sky subtraction """
	lines = [5893, 5578, 6301, 6365]
	skies('feige34', lines, obj=10)
	skies('ngc3169', lines)
	skies('ngc4725', lines)
	skies('pg1708+602', lines, obj=20)

def n3_calibrate():
	""" calibrates using a standard star """
	calibration('ngc3169', 'feige34')
	calibration('ngc4725', 'pg1708+602')

def n3():
	location = os.path.expanduser('~/iraf/work/n3')
	os.chdir(location)
	#uncomment and run these steps one at a time to avoid problems
	#n3_initial()
	#n3_slices()
	#then identify everything
	#n3_dispersion()
	#n3_skies()
	#then run standard and sensfunc manually
	#n3_calibrate()
	#now go measure line strengths with splot

n3()