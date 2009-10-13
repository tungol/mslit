#! /usr/bin/env python

import sys, os
from pyraf import iraf

LOCATION="../n3/"

def combine_zeros():
	iraf.zerocombine.unlearn()
	iraf.zerocombine(input="@lists/zero")

def combine_flat1():
	iraf.flatcombine.unlearn()
	iraf.flatcombine(input="@lists/flat1", output="Flat1", process="no")

def combine_flat2():
	iraf.flatcombine.unlearn()
	iraf.flatcombine(input="@lists/flat2", output="Flat2", process="no")

def ccdproc_ngc4725():
	iraf.ccdproc.unlearn()
	iraf.ccdproc.(images="@lists/ngc4725", fixpix="no", darkcor="no", biassec="[2049:2080,1:501]", trimsec="[1:2048,1:501]", zero="Zero.fits", flat="Flat2.fits", 

def main():
	os.chdir(LOCATION)
	iraf.noao(_doprint=0)
	iraf.imred(_doprint=0)
	iraf.ccdred(_doprint=0)
#	combine_zeros()
#	combine_flat1()
#	combine_flat2()
	ccdproc_ngc4725()

main()
