import os, os.path
from pyraf import iraf

###############################
## Functions to do with IRAF ##
###############################

## Wrappers for loading IRAF packages ##

def load_apextract():
    """Load the apextract package"""
    iraf.noao(_doprint=0)
    iraf.twodspec(_doprint=0)
    iraf.apextract(_doprint=0)

def load_ccdred():
    """Load the ccdred package"""
    iraf.noao(_doprint=0)
    iraf.imred(_doprint=0)
    iraf.ccdred(_doprint=0)

def load_imgeom():
    """Load the imgeom package"""
    iraf.images(_doprint=0)
    iraf.imgeom(_doprint=0)

def load_kpnoslit():
    """Load the kpnoslit package"""
    iraf.imred(_doprint=0)
    iraf.kpnoslit(_doprint=0)

def load_onedspec():
    """Load the onedspec package"""
    iraf.noao(_doprint=0)
    iraf.onedspec(_doprint=0)

## Wrappers around IRAF functions ##

def apsum(input, output, section, **kwargs):
    load_apextract()
    set_aperture(input, section)
    kwargs.setdefault('format', 'onedspec')
    kwargs.setdefault('interactive', 'no')
    kwargs.setdefault('find', 'no')
    kwargs.setdefault('trace', 'no')
    kwargs.setdefault('fittrace', 'no')
    iraf.apsum.unlearn()
    iraf.apsum(input=input, output=output, **kwargs)

def calibrate(input, sens, output, **kwargs):
    load_kpnoslit()
    iraf.calibrate.unlearn()
    iraf.calibrate(input=input, output=output, sens=sens, **kwargs)

def ccdproc(images, **kwargs):
    load_ccdred()
    kwargs.setdefault('darkcor', 'no')
    kwargs.setdefault('fixpix', 'no')
    kwargs.setdefault('biassec', '[2049:2080,1:501]')
    kwargs.setdefault('trimsec', '[1:2048,1:501]')
    iraf.ccdproc.unlearn()
    iraf.ccdproc(images=images, **kwargs)

def combine(input, output, **kwargs):
    load_ccdred()
    iraf.combine.unlearn()
    iraf.combine(input=input, output=output, **kwargs)

def dispcor(input, output, **kwargs):
    load_onedspec()
    iraf.dispcor.unlearn()
    iraf.dispcor(input=input, output=output, **kwargs)

def flatcombine(input, **kwargs):
    load_ccdred()
    kwargs.setdefault('process', 'no')
    iraf.flatcombine.unlearn()
    iraf.flatcombine(input = input, **kwargs)

def fixpix(image, mask, **kwargs):
    iraf.fixpix.unlearn()
    iraf.fixpix(images = image, masks = mask, **kwargs)

def hedit(images, fields, value, **kwargs):
    kwargs.setdefault('add', 'yes')
    kwargs.setdefault('verify', 'no')
    iraf.hedit.unlearn()
    iraf.hedit(images=images, fields=fields, value=value, **kwargs)

def imcopy(input, output, **kwargs):
    iraf.imcopy.unlearn()
    iraf.imcopy(input=input, output=output, **kwargs)

def rotate(input, output, angle, **kwargs):
    load_imgeom()
    iraf.rotate.unlearn()
    iraf.rotate(input=input, output=output, rotation=-angle, **kwargs)

def sarith(input1, op, input2, output, **kwargs):
    load_onedspec()
    iraf.sarith.unlearn()
    iraf.sarith(input1=input1, op=op, input2=input2, output=output, 
        **kwargs)

def scombine(input, output, **kwargs):
    load_onedspec()
    iraf.scombine.unlearn()
    iraf.scombine(input=input, output=output, **kwargs)

def setairmass(images, **kwargs):
    load_kpnoslit()
    iraf.setairmass.unlearn()
    iraf.setairmass(images=images, **kwargs)

def zerocombine(input, **kwargs):
    load_ccdred()
    iraf.zerocombine.unlearn()
    iraf.zerocombine(input = input, **kwargs)

## Functions to smooth over the interface to IRAF ##

def list_convert(list):
    """Convert python lists to the strings that IRAF accepts as lists"""
    str = list.pop(0)
    for item in list:
        str += ', %s' % item
    return str

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
    file = open('./database/ap%s' % input.replace('/', '_'), 'w')
    file.writelines(tmp)

