#! /usr/bin/env python

import sys, os, json
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
	iraf.ccdproc(images="@lists/ngc4725", fixpix="no", darkcor="no", biassec="[2049:2080,1:501]", trimsec="[1:2048,1:501]", zero="Zero.fits", flat="Flat2.fits")

def combine_ngc4725():
	iraf.combine.unlearn()
	iraf.combine(input="@lists/ngc4725", output="ngc4725")

def generate_ngc4725_geomap_input():
	json_file = open("input/ngc4725_cood.json", 'r')
	cood = json.load(json_file)
	save = open("input/ngc4725_cood.geomap", "w")
	generate_geomap_input(cood, save)
	save.close()

def generate_geomap_input(cood, save):
	geomap_input = ""
	columns = cood.keys()
	column1 = columns[0]
	column2 = columns[1]
	list1 = cood[column1]
	list2 = cood[column2]
	midpoint = avg(column1, column2)
	for i in range(len(list1)):
		start1 = list1[i]["start"]
		start2 = list2[i]["start"]
		end1 = list1[i]["end"]
		end2 = list2[i]["end"]
		avg_start = avg(start1, start2)
		avg_end = avg(end1, end2)
		geomap_input += ("%s %s %s %s\n" %
			(column1, start1, column1, avg_start))
		geomap_input += ("%s %s %s %s\n" %
			(column1, end1, column1, avg_end))
		geomap_input += ("%s %s %s %s\n" %
			(column2, start2, column2, avg_start))
		geomap_input += ("%s %s %s %s\n" %
			(column2, end2, column2, avg_end))
	geomap_input = geomap_input[:-1] #remove trailing newline
	save.write(geomap_input)

def avg(*args):
	floatNums = [float(x) for x in args]
	return sum(floatNums) / len(args)

def geomap_ngc4725():
	iraf.geomap.unlearn()
	iraf.geomap(input="input/ngc4725_cood.geomap", database="input/ngc4725.trans", interact="no", )

def geotran_ngc4725():
	iraf.geotran.unlearn()
	iraf.geotran(input = "ngc4725.fits", ouput = "ngc4725t.fits", database ="input/ngc4725.trans", transforms = "input/ngc4725_cood.geomap")

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
#	generate_ngc4725_geomap_input()
#	geomap_ngc4725()
	geotran_ngc4725()

main()
