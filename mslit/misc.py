#!/usr/bin/env python
# encoding: utf-8

'''
Some basic math functions and some convienience functions.

math functions: avg, rms, threshold_round, std
convienience functions: base, list_convert, remove_nan, zerocount
'''

import cmath
import math
import os
import numpy

## Some Math ##


def avg(*args):
    """Return the average of a list of values."""
    float_nums = [float(x) for x in args]
    remove_nan(float_nums)
    if len(float_nums) == 0:
        return float('NaN')
    return sum(float_nums) / len(float_nums)


def cubic_solutions(a, alpha, beta):
    """Calculate the solutions to a cubic function with given simplified
       parameters."""
    w1 = -.5 + .5 * math.sqrt(3) * 1j
    w2 = -.5 - .5 * math.sqrt(3) * 1j
    solution1 = -(1.0 / 3) * (a + alpha + beta)
    solution2 = -(1.0 / 3) * (a + w2 * alpha + w1 * beta)
    solution3 = -(1.0 / 3) * (a + w1 * alpha + w2 * beta)
    return [solution1, solution2, solution3]


def cubic_solve(b0, b1, b2, b3):
    """Calculate the solutions to a cubic function with given parameters."""
    a = b2 / b3
    b = b1 / b3
    c = (b0) / b3
    m = 2 * (a ** 3) - 9 * a * b + 27 * c
    k = (a ** 2) - 3 * b
    n = (m ** 2) - 4 * (k ** 3)
    alpha = (.5 * (m + cmath.sqrt(n))) ** (1.0 / 3)
    beta = (.5 * (m - cmath.sqrt(n))) ** (1.0 / 3)
    return cubic_solutions(a, alpha, beta)



def rms(*args):
    """Return the root mean square of a list of values."""
    squares = [(float(x) ** 2) for x in args]
    return math.sqrt(avg(*squares))


def threshold_round(number, threshold):
    """Round a number using a configurable threshold value."""
    if math.modf(number)[0] < threshold:
        return int(math.floor(number))
    else:
        return int(math.ceil(number))


def std(*args):
    """Return the standard deviation of a list of values."""
    mean = avg(*args)
    deviations = [(float(x) - mean) for x in args]
    return rms(*deviations)


## Convenience functions ##


def base(location, values, step):
    """Increase location by step until values[location] stops decreasing.
       Return this value."""
    while True:
        if values[location] >= values[location + step]:
            location += step
        else:
            break
    return step


def list_convert(pylist):
    """Convert python lists to the strings that IRAF accepts as lists."""
    stringlist = pylist[0]
    for item in pylist[1:]:
        stringlist += ', %s' % item
    return stringlist


def namefix(name):
    """Rename files to get rid of the silly naming scheme that apsum uses."""
    os.rename('%s.0001.fits' % name, '%s.fits' % name)


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
