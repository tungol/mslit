#!/usr/bin/env python
# encoding: utf-8

"""
Reduce multi-slit spectroscopic data.

Commands:

zeroflat: combine any zero and flat images for a night
init: initialize a galaxy or star
extract: extract one dimensional spectra from a galaxy or star
disp: apply dispersion correction to a galaxy or star
sky: perform sky subtraction for a galaxy or star
calibrate: flux calibrate a galaxy
analyze: produce graphs and tables of measured data
"""


import argparse
import os
from mslit import analyze, calibrate_galaxy, dispcor_galaxy, get_groups
from mslit import init_galaxy, slice_galaxy, skies, zero_flats


def main(command, path, name):
    """Execute commands from the command line."""
    commands = {'init': init_galaxy, 'extract': slice_galaxy,
                'disp': dispcor_galaxy,
                'sky': skies, 'calibrate': calibrate_galaxy}
    os.chdir(path)
    if command == 'zeroflat':
        zero_flats()
    elif command == 'analyze':
        analyze()
    elif name == 'all':
        groups = get_groups()
        for group in groups:
            commands[command](group['galaxy'])
            if command != 'calibrate':
                commands[command](group['star'])
    else:
        names = name.split(',')
        for name in names:
            commands[command](name)


def parse_args():
    """Parse the arguments from the command line."""
    parser = argparse.ArgumentParser(
             description='Reduce multi-slit spectroscopic data.',
             formatter_class=argparse.RawDescriptionHelpFormatter,
             epilog="""\
Commands:

zeroflat: combine any zero and flat images for a night
init: initialize a galaxy or star
extract: extract one dimensional spectra from a galaxy or star
disp: apply dispersion correction to a galaxy or star
sky: perform sky subtraction for a galaxy or star
calibrate: flux calibrate a galaxy
analyze: produce graphs and tables of measured data""")
    parser.add_argument('command', help="command to run",
                        choices=['zeroflat', 'init', 'extract', 'disp', 'sky',
                                 'calibrate', 'analyze'])
    parser.add_argument('path', help="path to the set of files")
    parser.add_argument('-n', '--name', default="all",
                        help="name of the galaxy or star to act on (default: "
                             "%(default)s)")
    args = vars(parser.parse_args())
    return (args['command'], args['path'], args['name'])

if __name__ == '__main__':
    main(*parse_args())
