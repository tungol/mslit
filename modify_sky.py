#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import subprocess
from sky import regenerate_sky
from data import get_sky_levels, write_sky_levels

# call signature: modify_sky night name number op value
# example: ./modify_sky.py n3 ngc3169 15 + 0.5
# which means to increase the scaling of the sky subtracted from
# spectrum 15 of ngc3169 from night three by 0.5


def modify_sky(path, name, number, op, value):
    os.chdir(path)
    number = int(number)
    value = float(value)
    sky_levels = get_sky_levels(name)
    sky_level = sky_levels[number]
    if op == '+':
        new_sky_level = sky_level + value
    elif op == '-':
        new_sky_level = sky_level - value
    sky_levels[number] = new_sky_level
    write_sky_levels(name, sky_levels)
    os.mkdir('%s/tmp' % name)
    regenerate_sky(name, number, new_sky_level)
    subprocess.call(['rm', '-rf', '%s/tmp' % name])


modify_sky(*sys.argv[1:])
