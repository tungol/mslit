#!/usr/bin/env python
# encoding: utf-8

"""
Functions for outputting LaTeX tables of data.

Functions:
Formatting: sigfigs_format
Basic tables; make_data_table, make_flux_table
Comparison tables: make_comparison_table, make_group_comparison_table
Table construction: make_table, make_multitable
Table details: arrange_galaxies, arrange_group, arrange_regions
"""

import numpy
from .const import GROUPS, LINES, LOOKUP
from .misc import avg, remove_nan, std


## Formatting ##


def sigfigs_format(x, n):
    """Format a number to a certain amount of significant figures."""
    if numpy.isnan(x):
        return '. . .'
    if n < 1:
        raise ValueError("number of significant digits must be >= 1")
    string = '%.*e' % (n-1, x)
    value, exponent = string.split('e')
    exponent = int(exponent)
    if exponent == 0:
        return value
    else:
        return '$%s \\times 10^{%s}$' % (value, exponent)


## Basic tables ##


def make_data_table(galaxy):
    """Create a table of basic data for a galaxy."""
    keys = ['rdistance', 'OH', 'SFR']
    values = [LOOKUP[key] for key in keys]
    string = make_table((galaxy.regions,), keys, values, 'Number',
                        arrange_regions)
    with open('tables/%s.tex' % galaxy.name, 'w') as f:
        f.write(string)


def make_flux_table(galaxy):
    """Create a table of measured fluxes for all regions in a galaxy."""
    order = ['NII1', 'NII2', 'OII', 'OIII1', 'OIII2', 'OIII3', 'SII1', 'SII2',
            'halpha', 'hbeta', 'hgamma']
    lines = LINES.keys()
    lines.sort()
    for item in lines[:]:
        unused = [numpy.isnan(spec.fluxes[item]) for spec in galaxy.regions]
        if False not in unused:
            lines.remove(item)
    keys = [item for item in order if item in lines]
    values = [LOOKUP[item] for item in lines]
    string = make_table((galaxy.regions,), keys, values, 'Number',
                        arrange_regions)
    with open('tables/%sflux.tex' % galaxy.name, 'w') as f:
        f.write(string)


## Comparison tables ##


def make_comparison_table(galaxies, other):
    """Make a table showing data of different galaxies."""
    keys = ['grad', 'metal', 'type', 'bar', 'ring', 'env', 'region_number']
    values = ['Gradient (dex/R$_{25}$)', 'Metalicity at 0.4R$_{25}$',
              'Hubble Type', 'Bar', 'Ring', 'Environment', 'Number of Regions']
    string = make_table((galaxies, other), keys, values, 'Name',
                        arrange_galaxies)
    with open('tables/comparison.tex', 'w') as f:
        f.write(''.join(string))


def make_group_comparison_table(galaxies, other):
    """Make a table showing data for groups of different kinds of galaxies."""
    galaxies += other
    keys = ['grad', 'grad_std', 'metal', 'metal_std']
    values = ['Gradient (dex/R$_{25}$)', 'Standard Deviation',
              'Metalicity at 0.4R$_{25}$', 'Standard Deviation']
    titles = {'env': 'Environment', 'ring': 'Ring', 'bar': 'Bar',
              'type': 'Hubble Type'}
    string = make_multitable(galaxies, keys, values, titles, arrange_group)
    with open('tables/comparison2.tex', 'w') as f:
        f.write(''.join(string))


## Actual tables ##


def make_table(groups, keys, values, name, command, multi=False):
    """Return a string representing a LaTeX table.
       
       groups: iterable containing different groups of galaxies
       keys: iterable containing the key values to be put on the table
       values: iterable containing the printable names corresponding to the
               keys in keys
       name: name of the first column
       command: every item in groups will be run through this command
       multi: optional parameter, if true, table will be used inside a
              multitable"""
    if multi:
        string = []
    else:
        string = ['\\begin{tabular}{ *{%s}{c}}\n' % (len(keys) + 1)]
    string += ['\\toprule\n %s ' % name]
    string += ['& %s ' % item for item in values]
    string.append('\\\\\n')
    for group in groups:
        string += command(group, keys)
    string.append('\\bottomrule\n')
    if not multi:
        string.append('\\end{tabular}\n')
    return ''.join(string)


def make_multitable(galaxies, keys, values, titles, command):
    """Return a string representing a LaTeX table containing multiple
       sub-tables.
       
       galaxies: list of galaxies
       keys: iterable containing the key values to be put on the table
       titles: dictionary of short name - print name pairs, one pair for each
               subtable
       command: this is passed through to the make_table function."""
    string = ['\\begin{tabular}{ *{%s}{c}}\n' % (len(keys) + 1)]
    for title in titles:
        v = dict([(header, {}) for header in GROUPS[title]])
        for header, group in GROUPS[title].items():
            for item in ('grad', 'metal'):
                items = [g.__dict__[item] for g in galaxies
                          if g.__dict__[title] in group]
                v[header].update({item: items})
        string += make_table((v,), keys, values, titles[title], command, True)
    string.append('\\end{tabular}\n')
    return ''.join(string)


## Details within tables ##


def arrange_galaxies(items, keys):
    """Return details of a table for comparing multiple galaxies."""
    string = ['\\midrule\n']
    for item in items:
        string.append(' %s ' % item.print_name)
        for key in keys:
            value = item.__dict__[key]
            if type(value) == str or key == 'region_number':
                value = str(value)
            else:
                value = sigfigs_format(value, 3)
            string.append('& %s ' % value)
        string.append('\\\\\n')
    return string


def arrange_group(data, keys):
    """Return details of a table comparing groups of different kinds of
       galaxies."""
    string = ['\\midrule\n']
    for header, group in data.items():
        string.append(' %s ' % header)
        for key in keys:
            if key[-4:] != '_std':
                values = group[key]
                remove_nan(values)
                a = sigfigs_format(avg(*values), 2)
                s = sigfigs_format(std(*values), 2)
                string.append('& %s & %s ' % (a, s))
        string.append('\\\\\n')
    return string


def arrange_regions(regions, keys):
    """Return details of a table comapring regions within a galaxy."""
    string = ['\\midrule\n']
    for region in regions:
        string.append(' %s' % region.printnumber)
        if region.corrected != True:
            string.append('$^a$')
        for item in keys:
            if item in region.fluxes:
                value = region.fluxes[item]
            else:
                value = region.__dict__[item]
            string.append(' & %s' % sigfigs_format(value, 2))
        string.append(' \\\\\n')
    return string
