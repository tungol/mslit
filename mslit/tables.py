#!/usr/bin/env python
# encoding: utf-8

"""
tables.py - functions for outputting LaTeX tables of data


"""

import numpy
from .misc import remove_nan, avg, std
from .const import GROUPS, LOOKUP, LINES

def sigfigs_format(x, n):
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


## Make some tables ##

def make_tabular(group, keys, values, extra, inner_command, outer_command):
    string = ['\\begin{tabular}{ *{%s}{c}}\n' % (len(keys) + 1)]
    string += outer_command(group, keys, values, extra, inner_command)
    string.append('\\end{tabular}\n')
    return ''.join(string)


def make_table(groups, keys, values, name, command):
    string = ['\\toprule\n %s ' % name]
    string += ['& %s ' % item for item in values]
    string.append('\\\\\n')
    for group in groups:
        string += command(group, keys)
    string.append('\\bottomrule\n')
    return string


def make_multitable(galaxies, keys, values, (classes, titles), command):
    string = []
    for title in titles:
        v = dict([(header, {}) for header in classes[title]])
        for header, group in classes[title].items():
            for item in ('grad', 'metal'):
                items = [g.__dict__[item] for g in galaxies
                          if g.__dict__[title] in group]
                v[header].update({item: items})
        string += make_table((v,), keys, values, titles[title], command)
    return string


def arrange_spectra(spectra, keys):
    string = ['\\midrule\n']
    for spectrum in spectra:
        string.append(' %s' % spectrum)
        if spectrum.corrected != True:
            string.append('$^a$')
        for item in keys:
            if item in spectrum.fluxes:
                value = spectrum.fluxes[item]
            else:
                value = spectrum.__dict__[item]
            string.append(' & %s' % sigfigs_format(value, 2))
        string.append(' \\\\\n')
    return string


def arrange_galaxies(items, keys):
    string = ['\\midrule\n']
    for item in items:
        string.append(' %s ' % item.name)
        for key in keys:
            value = item.__dict__[key]
            if type(value) == str or key == 'regions':
                value = str(value)
            else:
                value = sigfigs_format(value, 3)
            string.append('& %s ' % value)
        string.append('\\\\\n')
    return string


def arrange_group(data, keys):
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


def make_data_table(galaxy):
    keys = ['rdistance', 'OH', 'SFR']
    values = [LOOKUP[key] for key in keys]
    string = make_tabular((galaxy.spectra,), keys, values, 'Number',
                          arrange_spectra, make_table)
    with open('tables/%s.tex' % galaxy.num, 'w') as f:
        f.write(string)


def make_flux_table(galaxy):
    order = ['NII1', 'NII2', 'OII', 'OIII1', 'OIII2', 'OIII3', 'SII1', 'SII2',
            'halpha', 'hbeta', 'hgamma']
    lines = LINES.keys()
    lines.sort()
    for item in lines[:]:
        unused = [numpy.isnan(spec.fluxes[item]) for spec in galaxy.spectra]
        if False not in unused:
            lines.remove(item)
    keys = [item for item in order if item in lines]
    values = [LOOKUP[item] for item in lines]
    string = make_tabular((galaxy.spectra,), keys, values, 'Number',
                          arrange_spectra, make_table)
    with open('tables/%sflux.tex' % galaxy.num, 'w') as f:
        f.write(string)


def make_comparison_table(galaxies, other):
    keys = ['grad', 'metal', 'type', 'bar', 'ring', 'env', 'regions']
    values = ['Gradient (dex/R$_{25}$)', 'Metalicity at 0.4R$_{25}$',
              'Hubble Type', 'Bar', 'Ring', 'Environment', 'Number of Regions']
    string = make_tabular((galaxies, other), keys, values, 'Name',
                          arrange_galaxies, make_table)
    with open('tables/comparison.tex', 'w') as f:
        f.write(''.join(string))


def make_group_comparison_table(galaxies, other):
    galaxies += other
    keys = ['grad', 'grad_std', 'metal', 'metal_std']
    values = ['Gradient (dex/R$_{25}$)', 'Standard Deviation',
              'Metalicity at 0.4R$_{25}$', 'Standard Deviation']
    titles = {'env': 'Environment', 'ring': 'Ring', 'bar': 'Bar',
              'type': 'Hubble Type'}
    string = make_tabular(galaxies, keys, values, (GROUPS, titles),
                          arrange_group, make_multitable)
    with open('tables/comparison2.tex', 'w') as f:
        f.write(''.join(string))
