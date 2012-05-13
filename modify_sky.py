#!/usr/bin/env python
# encoding: utf-8

import os
import sys
import subprocess
from data import get_data, write_data
from sky import regenerate_sky

# call signature: modify_sky night name number op value
# example: ./modify_sky.py n3 ngc3169 15 + 0.5
# which means to increase the scaling of the sky subtracted from
# spectrum 15 of ngc3169 from night three by 0.5


def modify_sky(path, name, number, op, value):
    os.chdir(path)
    number = int(number)
    value = float(value)
    data = get_data(name)
    item = data[number]
    sky_level = item['sky_level']
    if op == '+':
        new_sky_level = sky_level + value
    elif op == '-':
        new_sky_level = sky_level - value
    item.update({'sky_level': new_sky_level})
    write_data(name, data)
    os.mkdir('%s/tmp' % name)
    regenerate_sky(name, item)
    subprocess.call(['rm', '-rf', '%s/tmp' % name])


modify_sky(*sys.argv[1:])
