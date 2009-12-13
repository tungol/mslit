#!/usr/bin/env python

#script for transforming plaintext list of image coordinates into json
# useage: text2json <name.(column1).txt> <name.(column2).txt> <name.types.txt>

import sys, os
import simplejson as json

def main(type_fn):
	internal_dict = {}
	type_file = open(type_fn, 'r')
	types = type_file.readlines()
	type_file.close()
	name, foo, ext = type_fn.split('.')
	json_fn = '../input%s_coord.json' % name
	json_file = open(json_fn, 'r')
	data = json.load(json_file)
	json_file.close()
	data.update({'types': types})
	json_file = open(json_fn, "w")
	json.dump(data, json_file)
	json_file.close()

if __name__ == '__main__':
	main(sys.argv[1])
