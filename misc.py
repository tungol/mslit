#!/usr/bin/env python
# encoding: utf-8

'''
misc.py - contains some basic math functions and some convienience
          functions.

math functions: avg, rms, std
convienience functions: remove_nan, zerocount
'''

import math
import numpy

##########################################
## Some miscellaneous, useful functions ##
##########################################

## Some Math ##


def avg(*args):
    """Return the average of a list of values."""
    float_nums = [float(x) for x in args]
    remove_nan(float_nums)
    if len(float_nums) == 0:
        return float('NaN')
    return sum(float_nums) / len(float_nums)


def rms(*args):
    """Return the root mean square of a list of values."""
    squares = [(float(x) ** 2) for x in args]
    return math.sqrt(avg(*squares))


def std(*args):
    """Return the standard deviation of a list of values."""
    mean = avg(*args)
    deviations = [(float(x) - mean) for x in args]
    return rms(*deviations)


## Convenience functions ##

def remove_nan(*lists):
    """Remove NaNs from one or more lists. If more than one list is given,
       keep the shape of all lists the same."""
    for l in lists:
        count = 0
        for i, item in enumerate(l[:]):
            if numpy.isnan(item):
                for item in lists:
                    del item[i - count]
                count += 1


def zerocount(number):
    """Return the three digit representation of a number."""
    if number < 10:
        return '00%s' % number
    elif number < 100:
        return '0%s' % number
    else:
        return '%s' % number
