#!/usr/bin/env python
# encoding: utf-8

import sys
from sky import modify_sky

# call signature: modify_sky night name number op value
# example: ./modify_sky.py n3 ngc3169 15 + 0.5
# which means to increase the scaling of the sky subtracted from
# spectrum 15 of ngc3169 from night three by 0.5

modify_sky(*sys.argv[1:])
