import pyraf.iraf
from misc import set_aperture

###############################
## Functions to do with IRAF ##
###############################

## Wrappers for loading IRAF packages ##


def load_apextract():
    """Load the apextract package"""
    pyraf.iraf.noao(_doprint=0)
    pyraf.iraf.twodspec(_doprint=0)
    pyraf.iraf.apextract(_doprint=0)


def load_ccdred():
    """Load the ccdred package"""
    pyraf.iraf.noao(_doprint=0)
    pyraf.iraf.imred(_doprint=0)
    pyraf.iraf.ccdred(_doprint=0)


def load_imgeom():
    """Load the imgeom package"""
    pyraf.iraf.images(_doprint=0)
    pyraf.iraf.imgeom(_doprint=0)


def load_kpnoslit():
    """Load the kpnoslit package"""
    pyraf.iraf.imred(_doprint=0)
    pyraf.iraf.kpnoslit(_doprint=0)


def load_onedspec():
    """Load the onedspec package"""
    pyraf.iraf.noao(_doprint=0)
    pyraf.iraf.onedspec(_doprint=0)

## Wrappers around IRAF functions ##


def apsum(input, output, section, **kwargs):
    load_apextract()
    set_aperture(input, section)
    kwargs.setdefault('format', 'onedspec')
    kwargs.setdefault('interactive', 'no')
    kwargs.setdefault('find', 'no')
    kwargs.setdefault('trace', 'no')
    kwargs.setdefault('fittrace', 'no')
    pyraf.iraf.apsum.unlearn()
    pyraf.iraf.apsum(input=input, output=output, **kwargs)


def calibrate(input, sens, output, **kwargs):
    load_kpnoslit()
    pyraf.iraf.calibrate.unlearn()
    pyraf.iraf.calibrate(input=input, output=output, sens=sens, **kwargs)


def ccdproc(images, **kwargs):
    load_ccdred()
    kwargs.setdefault('darkcor', 'no')
    kwargs.setdefault('fixpix', 'no')
    kwargs.setdefault('biassec', '[2049:2080,1:501]')
    kwargs.setdefault('trimsec', '[1:2048,1:501]')
    pyraf.iraf.ccdproc.unlearn()
    pyraf.iraf.ccdproc(images=images, **kwargs)


def combine(input, output, **kwargs):
    load_ccdred()
    pyraf.iraf.combine.unlearn()
    pyraf.iraf.combine(input=input, output=output, **kwargs)


def dispcor(input, output, **kwargs):
    load_onedspec()
    pyraf.iraf.dispcor.unlearn()
    pyraf.iraf.dispcor(input=input, output=output, **kwargs)


def flatcombine(input, **kwargs):
    load_ccdred()
    kwargs.setdefault('process', 'no')
    pyraf.iraf.flatcombine.unlearn()
    pyraf.iraf.flatcombine(input=input, **kwargs)


def fixpix(image, mask, **kwargs):
    pyraf.iraf.fixpix.unlearn()
    pyraf.iraf.fixpix(images=image, masks=mask, **kwargs)


def fix_image(image, mask):
    """Apply a bad pixel mask to an image"""
    hedit(image, 'BPM', mask)
    fixpix(image, 'BPM', verbose='yes')


def hedit(images, fields, value, **kwargs):
    kwargs.setdefault('add', 'yes')
    kwargs.setdefault('verify', 'no')
    pyraf.iraf.hedit.unlearn()
    pyraf.iraf.hedit(images=images, fields=fields, value=value, **kwargs)


def imcopy(input, output, **kwargs):
    pyraf.iraf.imcopy.unlearn()
    pyraf.iraf.imcopy(input=input, output=output, **kwargs)


def rotate(input, output, angle, **kwargs):
    load_imgeom()
    pyraf.iraf.rotate.unlearn()
    pyraf.iraf.rotate(input=input, output=output, rotation=-angle, **kwargs)


def sarith(input1, op, input2, output, **kwargs):
    load_onedspec()
    pyraf.iraf.sarith.unlearn()
    pyraf.iraf.sarith(input1=input1, op=op, input2=input2, output=output,
        **kwargs)


def scombine(input, output, **kwargs):
    load_onedspec()
    pyraf.iraf.scombine.unlearn()
    pyraf.iraf.scombine(input=input, output=output, **kwargs)


def setairmass(images, **kwargs):
    load_kpnoslit()
    pyraf.iraf.setairmass.unlearn()
    pyraf.iraf.setairmass(images=images, **kwargs)


def zerocombine(input, **kwargs):
    load_ccdred()
    pyraf.iraf.zerocombine.unlearn()
    pyraf.iraf.zerocombine(input=input, **kwargs)
