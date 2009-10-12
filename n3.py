#! /usr/bin/env python

import sys, os
from pyraf import iraf

PREFIX="cghn300"
LOCATION="../n3/"

def get_names(range):
	if type(range) == int:
		range = [range]
	if type(range) == list:
		tmp = []
		for item in range:
			if item < 10:
				tmp.append(PREFIX+'0'+str(item))
			else:
				tmp.append(PREFIX+str(item))
		return tmp
	else:
		raise TypeError("not a range")

def combine_zeros(zeros):
	iraf.noao(_doprint=0)
	iraf.imred(_doprint=0)
	iraf.ccdred(_doprint=0)
	iraf.unlean("zerocombine")
	iraf.zerocombine(zeros)

def main():
	os.chdir(LOCATION)
	zeros = get_names(range(1,15))
	combine_zeros(zeros)

main()
