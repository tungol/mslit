#!/usr/bin/env python

# for adding types to json data files. 
#useage: add_types <type file>

import sys, os
import simplejson as json

def main(type_fn):
	internal_dict = {}
	type_file = open(type_fn, 'r')
	types = type_file.readlines()
	for i, item in enumerate(types[:]):
		types[i] = item.strip()
	type_file.close()
	name, foo, ext = type_fn.split('.')
	json_fn = '../input/%s.json' % name
	json_file = open(json_fn, 'r')
	data = json.load(json_file)
	json_file.close()
	data.update({'types': types})
	json_file = open(json_fn, "w")
	json.dump(data, json_file)
	json_file.close()

if __name__ == '__main__':
	main(sys.argv[1])
