#!/usr/bin/env python

#script for transforming plaintext list of image coordinates into json, for use
#in geomap things

import sys, os
import simplejson as json

def main(args):
	json_file_name = args.pop()
	if os.access(json_file_name, os.F_OK):
		json_file = open(json_file_name, 'r')
		internal_dict = json.load(json_file)
		json_file.close()
	else:
		internal_dict = {}
	for file in args:
		column = raw_input("What column is this for? (%s)" % file)
		internal_dict.update({column: []})
		working_file = open(file, r)
		for line in working_file:
			if line[0] = #:
				pass
			else:
				tmp = line.split('-')
				start = tmp[0]
				end = tmp[1]
				internal_dict[column].append({"start": start,
					"end": end})
	json_file = open(json_file_name, "w")
	json.dump(internal_dict, json_file)
	json_file.close()

if __name__ = '__main__':
	main(sys.argv[1:])
