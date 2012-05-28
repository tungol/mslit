#!/usr/bin/env python
# encoding: utf-8

"""
Library for reduction and analysis of multi-slit spectroscopic data.
"""

from .analyze import analyze
from .data import get_groups
from .iraf_high import calibrate_galaxy, dispcor_galaxy, init_galaxy
from .iraf_high import slice_galaxy, zero_flats
from .sky import skies, modify_sky


__all__ = ['analyze', 'calibrate_galaxy', 'dispcor_galaxy', 'get_groups',
           'init_galaxy', 'modify_sky', 'skies', 'slice_galaxy', 'zero_flats']
