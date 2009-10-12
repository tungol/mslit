#! /usr/bin/env python

import sys
from pyraf import iraf

def main():
	zeros = get_names('cghn300', range(1,15))
	combine_zeros
