#!/usr/bin/env python
# encoding: utf-8

import os
import math
import cmath
import numpy
import scipy.optimize
import coords
from mslit.data import get
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


## Useful classes ##


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


class SpectrumClass:
    
    def __init__(self, num):
        self.id = num
        self.number = int(num)
        self.measurements = []
    
    def calculate(self, distance, center, ra, dec):
        self.r23 = calculate_r23(self.hbeta, self.OII, self.OIII1, self.OIII2)
        self.OH = self.calculate_OH(self)
        self.rdistance = calculate_radial_distance(ra, dec, center, distance)
        self.SFR = calculate_sfr(distance, self.halpha)
    
    def calculate_OH(self, disambig=True):
        if disambig:
            branch = self.OIII2 / self.OII
            return calculate_OH(self.r23, branch)
        return calculate_OH(self.r23)
    
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


class GalaxyClass:
    
    def __init__(self, name):
        self.id = name
        self.spectra = []
    
    def add_logs(self):
        fns = os.listdir('%s/measurements/' % self.id)
        spectradict = {}
        for fn in fns:
            if fn[-4:] == '.log':
                spectradict.update(parse_log(self.id, fn, spectradict))
        self.spectra = spectradict.values()
    
    def fit_OH(self):
        lsqout = fit_OH(self.spectra, self.r25)
        self.fit = lsqout
        self.grad = lsqout[0][0]
        self.metal = lsqout[0][1] + lsqout[0][0] * 0.4
    
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


def get_galaxies(fn, keys):
    with open('../other_data/%s' % fn) as f:
        raw = f.readlines()
    galaxies = []
    current = None
    number = None
    for line in raw:
        line = line.strip()
        if line == '':
            pass
        elif line[0] == '*':
            id = line[1:]
            name = 'NGC ' + id
            current = GalaxyClass(id)
            current.name = name
            number = 0
            galaxies.append(current)
            current.distance = keys[id]['distance']
            current.r25 = keys[id]['r_0']
            current.type = keys[id]['type']
            current.bar = keys[id]['bar']
            current.ring = keys[id]['ring']
            current.env = keys[id]['env']
        else:
            (r, hbeta, OII, OIII) = line.split('\t')
            r = float(r)
            hbeta = float(hbeta)
            OII = float(OII)
            OIII = float(OIII)
            r_23 = OII + OIII
            OII = hbeta * OII
            OIII = hbeta * OIII
            r = current.r25 * r
            spectrum = SpectrumClass(str(number))
            current.spectra.append(spectrum)
            spectrum.measurements.append({'name': 'hbeta', 'flux': hbeta})
            spectrum.measurements.append({'name': 'OII', 'flux': OII})
            spectrum.measurements.append({'name': 'OIII1', 'flux': OIII})
            spectrum.distance = current.distance
            spectrum.rdistance = r
            spectrum.r23 = r_23
            spectrum.OH = spectrum.calculate_OH(disambig=False)
            number += 1
    return galaxies


def get_other():
    files = os.listdir('../other_data/')
    for fn in files:
        if fn[-4:] != '.txt':
            files.remove(fn)
    keyfile = files.pop(0)
    keys = parse_keyfile(keyfile)
    others = []
    for item in files:
        galaxies = get_galaxies(item, keys)
        for galaxy in galaxies:
            others.append(galaxy)
    for galaxy in others:
        galaxy.regions = len(galaxy.spectra)
    return others


def parse_keyfile(fn):
    with open('../other_data/%s' % fn) as f:
        raw = f.readlines()
    keys = {}
    for line in raw:
        if line[0:3] == 'ngc':
            pass
        else:
            line = line.strip()
            (ngc, distance, r_0, htype, bar, ring, env) = line.split('\t')
            # convert distance to kpc from Mpc for consistency
            distance = float(distance) * 1000
            # convert r_0 from arcminutes to kpc
            r_0 = distance * math.tan(math.radians(float(r_0) * 60))
            keys.update({ngc: {'distance': distance,
                               'r_0': r_0,
                               'type': htype,
                               'bar': bar,
                               'ring': ring,
                               'env': env}})
    return keys


def main():
    os.chdir('../n3fresh')
    ngc3169 = GalaxyClass('ngc3169')
    ngc3169.name = 'NGC 3169'
    ngc3169.redshift = 0.004130
    ngc3169.center = '10:14:15.0 +03:27:58'
    ngc3169.distance = 20100 #kpc
    ngc3169.r25 = 11.57 #kpc
    ngc3169.type = 'Sa'
    ngc3169.bar = 'A'
    ngc3169.ring = 's'
    ngc3169.env = 'pair'
    
    ngc4725 = GalaxyClass('ngc4725')
    ngc4725.name = 'NGC 4725'
    ngc4725.redshift = 0.004023
    ngc4725.center = '12:50:26.6 +25:30:03'
    ngc4725.distance = 13918 #kpc
    ngc4725.r25 = 26.23 #kpc
    ngc4725.type = 'Sab'
    ngc4725.bar = 'AB'
    ngc4725.ring = 'r'
    ngc4725.env = 'pair'
    
    galaxies = [ngc3169, ngc4725]
    other_data = get_other()
    
    for galaxy in galaxies:
        galaxy.run()
        galaxy.fit_OH()
        galaxy.output_tables()
        galaxy.output_graphs()
    
    for galaxy in other_data:
        galaxy.fit_OH()
    
    groups = {'env': {'Isolated': ('isolated',), 'Group': ('group',),
                      'Pair': ('pair',)},
              'ring': {'S-Shaped': ('s',), 'Intermediate Type': ('rs',),
                       'Ringed': ('r',)},
              'bar': {'No Bar': ('A',), 'Weakly Barred': ('AB',),
                      'Strongly Barred': 'B'},
              'type': {'Sa and Sab': ('Sa', 'Sab'),
                       'Sb and Sbc': ('Sb', 'Sbc'),
                       'Sc and Scd': ('Sc', 'Scd'), 'Sd': ('Sd', 'Irr')}}
    
    compare_basic(galaxies, other_data)
    make_comparison_table(galaxies, other_data)
    make_group_comparison_table(galaxies, other_data, groups)
    for key, groups in groups.items():
        compare(galaxies, other_data, groups, key)


if __name__ == '__main__':
    main()
