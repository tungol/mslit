#!/usr/bin/env python
# encoding: utf-8

import argparse
import os
import math
import cmath
import numpy
import scipy.optimize
import coords
from mslit.data import get, get_groups
from mslit.misc import remove_nan, avg
from graphs import graph_metalicity, graph_sfr, graph_sfr_metals
from graphs import compare_basic, compare
from tables import make_flux_table, make_data_table, make_comparison_table
from tables import make_group_comparison_table


LINES = {'OII': 3727, 'hgamma': 4341, 'hbeta': 4861, 'OIII1': 4959,
         'OIII2': 5007, 'NII1': 6548, 'halpha': 6563, 'NII2': 6583,
         'SII1': 6717, 'SII2': 6731, 'OIII3': 4363}

LOOKUP = {'OII': '[O II]$\lambda3727$', 'hgamma': 'H$\gamma$',
          'hbeta': 'H$\\beta$', 'OIII1': '[O III]$\lambda4959$',
          'OIII2': '[O III]$\lambda5007$', 'NII1': '[N II]$\lambda6548$',
          'halpha': 'H$\\alpha$', 'NII2': '[N II]$\lambda6583$',
          'SII1': '[S II]$\lambda6717$', 'SII2': '[S II]$\lambda6731$',
          'OIII3': '[O III]$\lambda4363$',
          'OH': '$12 + \log{\\textnormal{O/H}}$',
          'SFR': 'SFR(M$_\odot$ / year)', 'rdistance': 'Radial Distance (kpc)',
          'extinction': 'E(B - V)', 'r23': '$R_{23}$'}

GROUPS = {'env': {'Isolated': ('isolated',), 'Group': ('group',),
                  'Pair': ('pair',)},
          'ring': {'S-Shaped': ('s',), 'Intermediate Type': ('rs',),
                   'Ringed': ('r',)},
          'bar': {'No Bar': ('A',), 'Weakly Barred': ('AB',),
                  'Strongly Barred': 'B'},
          'type': {'Sa and Sab': ('Sa', 'Sab'),
                   'Sb and Sbc': ('Sb', 'Sbc'),
                   'Sc and Scd': ('Sc', 'Scd'), 'Sd': ('Sd', 'Irr')}}



## Some Math ##


def cubic_solutions(a, alpha, beta):
    w1 = -.5 + .5 * math.sqrt(3) * 1j
    w2 = -.5 - .5 * math.sqrt(3) * 1j
    solution1 = -(1.0 / 3) * (a + alpha + beta)
    solution2 = -(1.0 / 3) * (a + w2 * alpha + w1 * beta)
    solution3 = -(1.0 / 3) * (a + w1 * alpha + w2 * beta)
    return [solution1, solution2, solution3]


def cubic_solve(b0, b1, b2, b3):
    a = b2 / b3
    b = b1 / b3
    c = (b0) / b3
    m = 2 * (a ** 3) - 9 * a * b + 27 * c
    k = (a ** 2) - 3 * b
    n = (m ** 2) - 4 * (k ** 3)
    alpha = (.5 * (m + cmath.sqrt(n))) ** (1.0 / 3)
    beta = (.5 * (m - cmath.sqrt(n))) ** (1.0 / 3)
    return cubic_solutions(a, alpha, beta)


## Convenience functions ##


def parse_line(line, num):
    # format is center, cont, flux, eqw, core, gfwhm, lfwhm
    item = line.split()[num]
    if item == 'INDEF':
        item = "NaN"
    return float(item)


def k(l):
    # for use in the calzetti method
    # convert to micrometers from angstrom
    l = l / 10000.
    if 0.63 <= l <= 1.0:
        return ((1.86 / l ** 2) - (0.48 / l ** 3) -
            (0.1 / l) + 1.73)
    elif 0.12 <= l < 0.63:
        return (2.656 * (-2.156 + (1.509 / l) -
            (0.198 / l ** 2) + (0.011 / l ** 3)) + 4.88)
    else:
        raise ValueError


def correct_extinction(R_obv, lines):
    # using the method described here:
# <http://www.astro.umd.edu/~chris/publications/html_papers/aat/node13.html>
    R_intr = 2.76
    a = 2.21
    extinction = a * math.log10(R_obv / R_intr)
    # Now using the Calzetti method:
    values = []
    for line in lines:
        flux = line['flux'] / (10 ** (-0.4 * extinction *
                                      k(line['center'])))
        values.append((line['name'], flux))
    return values


def calculate_OH(r23, branch=None):
    """ Calculate metalicity of the spectrum """
    # uses conversion given by nagao 2006
    b0 = 1.2299 - math.log10(r23)
    b1 = -4.1926
    b2 = 1.0246
    b3 = -6.3169 * 10 ** -2
    # solving the equation
    solutions = cubic_solve(b0, b1, b2, b3)
    for i, item in enumerate(solutions):
        if item.imag == 0.0:
            solutions[i] = item.real
        else:
            solutions[i] = float('NaN')
    if branch is not None:
        # if given, branch should be the ratio OIII2 / OII
        if branch < 2:
            return solutions[2]
        else:
            return solutions[1]
    else:
        return solutions[2]


def calculate_r23(hbeta, OII, OIII1, OIII2):
    r2 = OII / hbeta
    r3 = (OIII1 + OIII2) / hbeta
    r23 = r2 + r3
    return r23


def calculate_radial_distance(ra, dec, center, distance):
    """ Calculate the galctocentric radius of the region """
    position = coords.Position('%s %s' % (ra, dec))
    theta = coords.Position(center).angsep(position)
    # radial distance in kiloparsecs
    return distance * math.tan(math.radians(theta.degrees()))


def calculate_sfr(distance, halpha_flux):
    """halpha SFR calibration given by Kennicutt 1998"""
    d = distance * 3.0857 * (10 ** 21)
    luminosity = halpha_flux * 4 * math.pi * (d ** 2)
    return luminosity * 7.9 * (10 ** -42)


def is_spectra_head(line):
    if line[:3] in ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'):
        return True
    else:
        return False


def is_labels(line):
    labelstr = ("    center      cont      flux       eqw      core     gfwhm"
                "     lfwhm\n")
    if line == labelstr:
        return True
    return False


def get_num(line):
    start = line.find('[') + 1
    return line[start:start + 3]


def parse_log(name, fn, spectradict):
    with open('%s/measurements/%s' % (name, fn)) as f:
        raw = f.readlines()
    current = None
    for line in raw:
        if is_spectra_head(line):
            num = get_num(line)
            if num in spectradict:
                current = spectradict[num]
            else:
                current = SpectrumClass(num)
                spectradict.update({num: current})
        elif line.strip() != '' and not is_labels(line):
            current.measurements.append({'flux': parse_line(line, 2),
                                         'center': parse_line(line, 0)})
    return spectradict


def fit_OH(spectra, r25):
    # inital guess: flat and solar metallicity
    slope = 0
    intercept = 8.6
    x = [s.rdistance for s in spectra]
    y = [s.OH for s in spectra]
    remove_nan(x, y)
    x = numpy.array(x)
    y = numpy.array(y)
    x = x / r25
    
    def f((slope, intercept)):
        return y - (intercept + slope * x)
    
    return scipy.optimize.leastsq(f, (slope, intercept))


## Useful classes ##

class SpectrumClass:
    
    def __init__(self, num, data=None):
        self.id = num
        self.number = int(num)
        self.measurements = []
        if data:
            (r, hbeta, OII, OIII, r25, distance) = data
            r_23 = OII + OIII
            OII = hbeta * OII
            OIII = hbeta * OIII
            r = r25 * r
            self.measurements.append({'name': 'hbeta', 'flux': hbeta})
            self.measurements.append({'name': 'OII', 'flux': OII})
            self.measurements.append({'name': 'OIII1', 'flux': OIII})
            self.rdistance = r
            self.r23 = r_23
            self.distance = distance
            self.calculate_OH(disambig=False)
            
    
    def __repr__(self):
        return str(self.printnumber)
    
    def calculate(self, distance, center, ra, dec):
        self.r23 = calculate_r23(self.hbeta, self.OII, self.OIII1, self.OIII2)
        self.calculate_OH(self)
        self.rdistance = calculate_radial_distance(ra, dec, center, distance)
        self.SFR = calculate_sfr(distance, self.halpha)
    
    def calculate_OH(self, disambig=True):
        if disambig:
            branch = self.OIII2 / self.OII
            self.OH = calculate_OH(self.r23, branch)
        self.OH = calculate_OH(self.r23)
    
    def collate_lines(self):
        self.lines = {}
        for name, location in LINES.items():
            line = {'name': name, 'center': location}
            self.lines.update({name: line})
            sources = [m for m in self.measurements if m['name'] == name]
            flux = avg(*[s['flux'] for s in sources])
            self.lines[name].update({'flux': flux})
            self.__dict__[name] = flux
    
    def correct_extinction(self):
        R_obv = self.halpha / self.hbeta
        if numpy.isnan(R_obv):
            self.corrected = False
            self.id = self.id + '*'
        else:
            values = correct_extinction(R_obv, self.lines.values())
            for name, flux in values:
                self.__dict__[name] = flux
            self.corrected = True
    
    def id_lines(self, lines):
        for measurement in self.measurements:
            badness = dict([(abs(measurement['center'] - lines[name]), name)
                            for name in lines])
            measurement.update({'name': badness[min(badness.keys())]})
    

class GalaxyClass:
    
    def __init__(self, name, data=None):
        self.id = name
        self.spectra = []
        if data:
            self.name = data['name']
            self.distance = data['distance'] # in kpc
            self.r25 = data['r25'] # in kpc
            self.type = data['type']
            self.bar = data['bar']
            self.ring = data['ring']
            self.env = data['env']
            if 'redshift' in data:
                self.redshift = data['redshift']
            if 'center' in data:
                self.center = data['center']
    
    def add_logs(self):
        fns = os.listdir('%s/measurements/' % self.id)
        spectradict = {}
        for fn in fns:
            if fn[-4:] == '.log':
                spectradict.update(parse_log(self.id, fn, spectradict))
        self.spectra = spectradict.values()
        self.spectra.sort(key=lambda x: x.id)
    
    def fit_OH(self):
        lsqout = fit_OH(self.spectra, self.r25)
        self.fit = lsqout
        self.grad = lsqout[0][0]
        # standard metallicity is the metallicity at r = 0.4
        self.metal = lsqout[0][1] + self.grad * 0.4
    
    def output_graphs(self):
        graph_metalicity(self)
        graph_sfr(self)
        graph_sfr_metals(self)
    
    def output_tables(self):
        spectra = self.spectra
        for i, spectrum in enumerate(spectra):
            spectrum.printnumber = i + 1
        make_flux_table(self, LINES.keys(), LOOKUP)
        make_data_table(self, LOOKUP)
    
    def run(self):
        self.add_logs()
        lines = LINES.copy()
        for item in lines:
            lines.update({item: (lines[item] * (self.redshift + 1))})
        data = get(self.id, 'positions')
        self.regions = len(self.spectra)
        for spectrum in self.spectra:
            spectrum.id_lines(lines)
            spectrum.collate_lines()
            spectrum.correct_extinction()
            sdata = data[spectrum.number]
            spectrum.calculate(self.distance, self.center, sdata['ra'],
                               sdata['dec'])
    

## Functions for reading in tables of data ##


def process_galaxies(fn, galaxydict):
    with open('other_data/%s' % fn) as f:
        raw = f.readlines()
    current = None
    number = None
    for line in raw:
        line = line.strip()
        if line == '':
            pass
        elif line[0] == '*':
            current = galaxydict[line[1:]]
            number = 0
        else:
            # r, hbeta, OII, OIII
            data = [float(item) for item in line.split('\t')]
            data += [current.r25, current.distance]
            spectrum = SpectrumClass(str(number), data)
            current.spectra.append(spectrum)
            number += 1


def get_other():
    files = os.listdir('other_data/')
    files = [fn for fn in files if fn.startswith('table')]
    galaxydict = parse_keyfile()
    for fn in files:
        process_galaxies(fn, galaxydict)
    for galaxy in galaxydict.values():
        galaxy.regions = len(galaxy.spectra)
    return galaxydict.values()


def parse_keyfile():
    with open('other_data/key.txt') as f:
        raw = f.readlines()
    galaxydict = {}
    for line in raw:
        line = line.strip()
        if line != 'ngc	D (mpc)	r_0	type	bar	ring	env': # header
            (ngc, distance, r_0, htype, bar, ring, env) = line.split('\t')
            # convert distance to kpc from Mpc for consistency
            distance = float(distance) * 1000
            # convert r_0 from arcminutes to kpc
            r_0 = distance * math.tan(math.radians(float(r_0) * 60))
            data = {'distance': distance, 'r25': r_0, 'type': htype,
                    'bar': bar, 'ring': ring, 'env': env,
                    'name': 'NGC %s' % ngc}
            galaxydict.update({ngc: GalaxyClass(ngc, data)})
    return galaxydict


def main(path):
    os.chdir(path)
    groups = get_groups()
    galaxies = []
    for group in groups:
        data = get(group['galaxy'], 'key')
        galaxies.append(GalaxyClass(group['galaxy'], data))
    other_data = get_other()
    for galaxy in galaxies:
        galaxy.run()
        galaxy.fit_OH()
        galaxy.output_tables()
        galaxy.output_graphs()
    for galaxy in other_data:
        galaxy.fit_OH()
    compare_basic(galaxies, other_data)
    make_comparison_table(galaxies, other_data)
    make_group_comparison_table(galaxies, other_data, GROUPS)
    for key, group in GROUPS.items():
        compare(galaxies, other_data, group, key)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    args = vars(parser.parse_args())
    return args['path']


if __name__ == '__main__':
    main(parse_args())
