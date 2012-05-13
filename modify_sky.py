#!/usr/bin/env python
# encoding: utf-8

import os
from argparse import ArgumentParser
from data import get, write
from sky import generate_sky

# call signature: modify_sky night name number op value
# example: ./modify_sky.py n3 ngc3169 15 + 0.5
# which means to increase the scaling of the sky subtracted from
# spectrum 15 of ngc3169 from night three by 0.5


def modify_sky(path, name, number, op, value):
    os.chdir(path)
    number = int(number)
    value = float(value)
    sky_levels = get(name, 'sky')
    sky_level = sky_levels[number]
    if op == '+':
        new_sky_level = sky_level + value
    elif op == '-':
        new_sky_level = sky_level - value
    sky_levels[number] = new_sky_level
    write(name, 'sky', sky_levels)
    generate_sky(name, number, new_sky_level)


def parse_args():
    parser = ArgumentParser(description='')
    parser.add_argument('path')
    parser.add_argument('name')
    parser.add_argument('number')
    parser.add_argument('op')
    parser.add_argument('value')
    return vars(parser.parse_args())

if __name__ == '__main__':
    args = parse_args()
    modify_sky(args['path'], args['name'], args['number'], args['op'],
               args['value'])
