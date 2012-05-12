import math
import os
import os.path
import numpy

##########################################
## Some miscellaneous, useful functions ##
##########################################

## Some Math ##


def avg(*args):
    """Return the average of a list of values"""
    float_nums = [float(x) for x in args]
    remove_nan(float_nums)
    if len(float_nums) == 0:
        return float('NaN')
    return sum(float_nums) / len(float_nums)


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
    for l in lists:
        count = 0
        for i, item in enumerate(l[:]):
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



## Functions to smooth over the interface to IRAF ##


def namefix(name):
    """Rename files to get rid of silly naming scheme of apsum"""
    os.rename('%s.0001.fits' % name, '%s.fits' % name)


def list_convert(pylist):
    """Convert python lists to the strings that IRAF accepts as lists"""
    stringlist = pylist[0]
    for item in pylist[1:]:
        stringlist += ', %s' % item
    return stringlist


def set_aperture(input, section):
    """Create an aperture definition file for apsum"""
    (row, column) = section[1:-1].split(',')
    (left, right) = row.split(':')
    (down, up) = column.split(':')
    center = (float(up) - float(down) + 1) / 2.
    rup = center
    rdown = -center
    tmp = []
    tmp.append('begin\taperture %s 1 1024. %s\n' % (input, center))
    tmp.append('\timage\t%s\n' % input)
    tmp.append('\taperture\t1\n')
    tmp.append('\tbeam\t1\n')
    tmp.append('\tcenter\t1024. %s\n' % center)
    tmp.append('\tlow\t-1023. %s\n' % rdown)
    tmp.append('\thigh\t1024. %s\n' % rup)
    tmp.append('\tbackground\n')
    tmp.append('\t\txmin -10.\n')
    tmp.append('\t\txmax 10.\n')
    tmp.append('\t\tfunction chebyshev\n')
    tmp.append('\t\torder 1\n')
    tmp.append('\t\tsample -10:-6,6:10\n')
    tmp.append('\t\tnaverage -3\n')
    tmp.append('\t\tniterate 0\n')
    tmp.append('\t\tlow_reject 3.\n')
    tmp.append('\t\thigh_reject 3.\n')
    tmp.append('\t\tgrow 0.\n')
    tmp.append('\taxis\t2\n')
    tmp.append('\tcurve\t5\n')
    tmp.append('\t\t2.\n')
    tmp.append('\t\t1.\n')
    tmp.append('\t\t1.\n')
    tmp.append('\t\t2048.\n')
    tmp.append('\t\t0.\n')
    tmp.append('\n')
    if not os.path.isdir('./database'):
        os.mkdir('./database')
    with open('./database/ap%s' % input.replace('/', '_'), 'w') as f:
        f.writelines(tmp)
