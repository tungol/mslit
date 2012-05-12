from pyraf import iraf
from misc import set_aperture

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

def fix_image(image, mask):
    """Apply a bad pixel mask to an image"""
    hedit(image, 'BPM', mask)
    fixpix(image, 'BPM', verbose='yes')

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

