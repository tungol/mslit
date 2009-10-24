#! /usr/bin/env python

import sys, os, math
import simplejson as json
from pyraf import iraf

LOCATION="../n3/"

def avg(*args):
	floatNums = [float(x) for x in args]
	return sum(floatNums) / len(args)

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
	iraf.ccdproc(images="@lists/ngc4725", fixpix="no", darkcor="no", biassec="[2049:2080,1:501]", trimsec="[1:2048,1:501]", zero="Zero.fits", flat="Flat2.fits")

def combine_ngc4725():
	iraf.combine.unlearn()
	iraf.combine(input="@lists/ngc4725", output="ngc4725")

def tilt_ngc4725():
	json_file = open('input/ngc4725_cood.json', 'r')
	cood = json.load(json_file)
	json_file.close()
	columns = cood.keys()
	column1 = columns[0]
	column2 = columns[1]
	list1 = cood[column1]
	list2 = cood[column2]
	midpoint = avg(column1, column2)
	run = midpoint - float(column1)
	for i in range(len(list1)):
		start1 = list1[i]["start"]
		end1 = list1[i]["end"]
		start2 = list2[i]["start"]
		end2 = list2[i]["end"]
		mid1 = avg(start1, end1)
		mid2 = avg(start2, end2)
		mid3 = avg(mid1, mid2)
		rise = mid1 - mid3
		slope = float(rise) / float(run)
		angle = math.atan(slope)
		print angle
		iraf.geotran.unlearn()
		iraf.geotran(input = "ngc4725.fits", output = ("ngc4725/rotate%s.fits" % i), database = "", xrotation = -angle, yrotation = -angle)

def main():
	os.chdir(LOCATION)
	iraf.noao(_doprint=0)
	iraf.imred(_doprint=0)
	iraf.ccdred(_doprint=0)
#	combine_zeros()
#	combine_flat1()
#	combine_flat2()
#	ccdproc_ngc4725()
#	combine_ngc4725()
	tilt_ngc4725()

main()
