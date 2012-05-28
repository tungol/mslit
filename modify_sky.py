#!/usr/bin/env python
# encoding: utf-8

"""
Change sky subtraction levels for a region by an increment.
"""

from argparse import ArgumentParser
from mslit import modify_sky


def parse_args():
    """Parse arguments form the command line."""
    parser = ArgumentParser(description='Change the sky subtraction level for '
                            'a region by an increment.')
    parser.add_argument('path', help="path to the set of files")
    parser.add_argument('name', help='name of the galaxy')
    parser.add_argument('number', help='number of the region to act on',
                        type='int')
    parser.add_argument('op', help='operation to preform', choices=['+', '-'])
    parser.add_argument('value', help='increment', type='float')
    args = vars(parser.parse_args())
    return (args['path'], args['name'], args['number'], args['op'],
            args['value'])

if __name__ == '__main__':
    modify_sky(*parse_args())
