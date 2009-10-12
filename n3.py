#! /usr/bin/env python

import sys, os
from pyraf import iraf

LOCATION="../n3/"

def combine_zeros():
	iraf.noao(_doprint=0)
	iraf.imred(_doprint=0)
	iraf.ccdred(_doprint=0)
	iraf.zerocombine.unlearn()
	iraf.zerocombine(input="@lists/zero")

def main():
	os.chdir(LOCATION)
	combine_zeros()

main()
