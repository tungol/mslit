#!/usr/bin/env python

#script for transforming plaintext list of image coordinates into json
# useage: text2json <name.(column1).txt> <name.(column2).txt> <name.types.txt>

import sys, os
import simplejson as json

def main(args):
	internal_dict = {}
	type_file = open(args[-1], 'r')
	for file in args[:-1]:
		name, column, ext = file.split('.')
		#column = raw_input("What column is this for? (%s) " % file)
		internal_dict.update({column: []})
		working_file = open(file, 'r')
		for line in working_file:
			if line[0] == '#':
				pass
			else:
				tmp = line.split('-')
				start = tmp[0].strip()
				end = tmp[1].strip()
				internal_dict[column].append({"start": start,
					"end": end})
	json_fn = '%s_coord.json' % name
	json_file = open(json_fn, "w")
	json.dump(internal_dict, json_file)
	json_file.close()

if __name__ == '__main__':
	main(sys.argv[1:])
