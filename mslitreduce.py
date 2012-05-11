#!/usr/bin/env python
# encoding: utf-8

import os
from argparse import ArgumentParser
import yaml
from div3lib import zero_flats, init_galaxy, slice_galaxy
from div3lib import disp_galaxy, skies, calibration

#init,slice,disp,skysubtract,calibrate

def get_groups(path):
    fn = '%s/input/groups.yaml' % path
    with open(fn) as f:
        groups = yaml.load(f.read())
    return groups

def init(groups):
    zeros = []
    flats = []
    for group in groups:
        if group['zero'] not in zeros:
            zeros.append(group['zero'])
        if group['flat'] not in flats:
            flats.append(group['flat'])
    # note: this takes the mask from the first group, will cause problems if
    # a single night needs more than one mask.
    zero_flats(groups[0]['mask'], zeros, flats)
    for group in groups:
        init_galaxy(group['galaxy'], group['mask'], group['zero'], group['flat'])
        init_galaxy(group['star'], group['mask'], group['zero'], group['flat'])

def slice(groups):
    for group in groups:
        slice_galaxy(group['galaxy'], group['lamp'])
        slice_galaxy(group['star'], group['lamp'], use=group['galaxy'])

def disp(groups):
    for group in groups:
        disp_galaxy(group['galaxy'])
        disp_galaxy(group['star'], use=group['galaxy'])

def skysubtract(groups):
    lines = [5893, 5578, 6301, 6365]
    for group in groups:
        skies(group['galaxy'], lines)
        skies(group['star'], lines, obj=group['star_num'])

def calibrate(groups):
    for group in groups:
        calibration(group['galaxy'], group['star'])

def main(command, path):
    groups = get_groups(path)
    commands = {'init': init, 'slice': slice, 'disp': disp,
                'skysubtract': skysubtract, 'calibrate': calibrate}
    os.chdir(path)
    commands[command](groups)

def parse_args():
    parser = ArgumentParser(description='')
    parser.add_argument('command')
    parser.add_argument('path')
    return vars(parser.parse_args())

if __name__ == '__main__':
    args = parse_args()
    main(args['command'], args['path'])
