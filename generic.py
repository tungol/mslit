import math
import numpy

####################################
## Some generic, useful functions ##
####################################

## Some Math ##

def avg(*args):
    """Return the average of a list of values"""
    floatNums = [float(x) for x in args]
    remove_nan(floatNums)
    if len(floatNums) == 0:
        return float('NaN')
    return sum(floatNums) / len(floatNums)

def rms(*args):
    """Return the root mean square of a list of values"""
    squares = [(float(x) ** 2) for x in args]
    return math.sqrt(avg(*squares))

def std(*args):
    """Return the standard deviation of a list of values"""
    mean = avg(*args)
    deviations = [(float(x) - mean) for x in args]
    return rms(*deviations)


## Convenience functions ##

def remove_nan(*lists):
    """ remove NaNs from one or more lists 
        if more than one, keep shape of all lists the same """
    for list in lists:
        count = 0
        for i, item in enumerate(list[:]):
            if numpy.isnan(item):
                for item in lists:
                    del item[i - count]
                count += 1

def zerocount(i):
    """Return the three digit representation of a number"""
    if i < 10:
        return '00%s' % i
    elif i < 100:
        return '0%s' % i
    else:
        return '%s' % i

