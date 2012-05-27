#!/usr/bin/env python
# encoding: utf-8

from __future__ import with_statement
import os
import math
import cmath
import numpy
import scipy.optimize
import coords
from .data import get, get_groups
from .misc import remove_nan, avg
from .graphs import graph_metalicity, graph_sfr, graph_sfr_metals
from .graphs import compare_basic, compare
from .tables import make_flux_table, make_data_table, make_comparison_table
from .tables import make_group_comparison_table
from .const import LINES, GROUPS, LOG_FORMAT


## Some Math ##


def cubic_solutions(a, alpha, beta):
    """Calculate the solutions to a cubic function with given simplified
       parameters."""
    w1 = -.5 + .5 * math.sqrt(3) * 1j
    w2 = -.5 - .5 * math.sqrt(3) * 1j
    solution1 = -(1.0 / 3) * (a + alpha + beta)
    solution2 = -(1.0 / 3) * (a + w2 * alpha + w1 * beta)
    solution3 = -(1.0 / 3) * (a + w1 * alpha + w2 * beta)
    return [solution1, solution2, solution3]


def cubic_solve(b0, b1, b2, b3):
    """Calculate the solutions to a cubic function with given parameters."""
    a = b2 / b3
    b = b1 / b3
    c = (b0) / b3
    m = 2 * (a ** 3) - 9 * a * b + 27 * c
    k = (a ** 2) - 3 * b
    n = (m ** 2) - 4 * (k ** 3)
    alpha = (.5 * (m + cmath.sqrt(n))) ** (1.0 / 3)
    beta = (.5 * (m - cmath.sqrt(n))) ** (1.0 / 3)
    return cubic_solutions(a, alpha, beta)


## Log parsing functions ##


def get_measurements(name):
    """For a given galaxy, return a list of all of the measurements taken."""
    fns = os.listdir('%s/measurements/' % name)
    measurements = []
    for fn in fns:
        if fn[-4:] == '.log':
            with open('%s/measurements/%s' % (name, fn)) as f:
                measurements.append(parse_log(f.readlines()))
    collated = measurements[0][:]
    for log in measurements[1:]:
        for i, region in enumerate(log):
            collated[i].extend(region)
    return collated


def get_num(line):
    """Return the number of the region, given it's header line."""
    start = line.find('[') + 1
    return int(line[start:start + 3])


def is_labels(line):
    """Return true if the line from the log is the field labeling line."""
    labelstr = ("    center      cont      flux       eqw      core     gfwhm"
                "     lfwhm\n")
    if line == labelstr:
        return True
    return False


def is_region_head(line):
    """Return true if a line is a region header line. Test this by testing
       if it begins with the abbreviation for a month."""
    if line[:3] in ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug',
                    'Sep', 'Oct', 'Nov', 'Dec'):
        return True
    return False


def parse_line(line):
    """Return a dictionary of the values from a line of the log."""
    values = [float(x) if x != 'INDEF' else float('nan') for x in line.split()]
    return dict(zip(LOG_FORMAT, values))


def parse_log(raw):
    """Parse raw lines from a splot log file and return a list of all the
       measurements found."""
    length = max([get_num(line) for line in raw if is_region_head(line)])
    current = None
    measurements = [[] for i in range(length + 1)]
    for line in raw:
        if is_region_head(line):
            current = get_num(line)
        elif line.strip() != '' and not is_labels(line):
            measurements[current].append(parse_line(line))
    return measurements


## Processing ##


def collate_lines(region):
    """Given all the measurements for a region, return the averaged fluxes of
       each spectral line that we are interested in. Also return the average
       wavelength that the line was found at."""
    # This could be easily modified if you wanted to get the averages of other
    # values that splot provides, or their standard deviations, etc.
    fluxes = {}
    centers = {}
    for name in LINES:
        sources = [measurement for measurement in region
                   if measurement['name'] == name]
        line = {}
        for item in LOG_FORMAT:
            line.update({item: avg(*[s[item] for s in sources])})
        fluxes.update({name: line['flux']})
        centers.update({name: line['center']})
    return fluxes, centers


def id_lines(region, lines):
    """For all the measurements in a region, determine which spectral line they
       are closest to in wavelength."""
    for measurement in region:
        badness = dict([(abs(measurement['center'] - lines[name]), name)
                        for name in lines])
        measurement.update({'name': badness[min(badness.keys())]})


## Useful classes ##

class RegionClass:
    
    def __init__(self, number, fluxes, centers=None):
        self.number = number
        self.fluxes = fluxes
        self.centers = centers
    
    def __repr__(self):
        return str(self.printnumber)
    
    def calculate(self):
        self.correct_extinction()
        self.rdistance = calculate_radial_distance(self.position, self.center,
                                                   self.distance)
        self.r23 = calculate_r23(self.fluxes)
        self.calculate_OH()
        self.SFR = calculate_sfr(self.distance, self.fluxes['halpha'])
    
    def calculate_OH(self, disambig=True):
        if disambig:
            branch = self.fluxes['OIII2'] / self.fluxes['OII']
            self.OH = calculate_OH(self.r23, branch)
        self.OH = calculate_OH(self.r23)
    
    def correct_extinction(self):
        R_obv = self.fluxes['halpha'] / self.fluxes['hbeta']
        if numpy.isnan(R_obv):
            self.corrected = False
        else:
            self.fluxes = correct_extinction(R_obv, self.fluxes, self.centers)
            self.corrected = True
    

class GalaxyClass:
    
    def __init__(self, name, data=None):
        self.num = name
        self.regions = []
        self.fit = None
        self.grad = None
        self.metal = None
        self.region_number = None
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
    
    def fit_OH(self):
        lsqout = fit_OH(self.regions, self.r25)
        self.fit = lsqout
        self.grad = lsqout[0][0]
        # standard metallicity is the metallicity at r = 0.4
        self.metal = lsqout[0][1] + self.grad * 0.4
    
    def output(self):
        graph_metalicity(self)
        graph_sfr(self)
        graph_sfr_metals(self)
        # go backwards so that indexing is kept as items are deleted
        for region in self.regions[::-1]:
            if numpy.isnan(region.fluxes['halpha']):
                del self.regions[region.number]
        count = 1
        for region in self.regions:
            region.printnumber = count
            count += 1
        make_flux_table(self)
        make_data_table(self)
    
    def run(self):
        measurements = get_measurements(self.num)
        self.region_number = len([r for r in measurements if r != []])
        lines = LINES.copy()
        for key, value in lines.items():
            lines.update({key: (value * (self.redshift + 1))})
        for group in measurements:
            id_lines(group, lines)
        groups = [collate_lines(region) for region in measurements]
        data = get(self.num, 'positions')
        for i, (fluxes, centers) in enumerate(groups):
            region = RegionClass(i, fluxes, centers)
            region.distance = self.distance
            region.position = '%s %s' % (data[i]['ra'], data[i]['dec'])
            region.center = self.center
            region.calculate()
            self.regions.append(region)
    

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
            (r, hbeta, r2, r3) = [float(item) for item in line.split('\t')]
            # values I got were divided by hbeta
            data = {'hbeta': hbeta, 'OII': r2 * hbeta, 'OIII1': r3 * hbeta}
            region = RegionClass(number, data)
            region.r23 = r2 + r3
            region.rdistance = current.r25 * r
            region.distance = current.distance
            region.calculate_OH(disambig=False)
            current.regions.append(region)
            number += 1


def get_other():
    files = os.listdir('other_data/')
    files = [fn for fn in files if fn.startswith('table')]
    galaxydict = parse_keyfile()
    for fn in files:
        process_galaxies(fn, galaxydict)
    for galaxy in galaxydict.values():
        galaxy.region_number = len(galaxy.regions)
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


def analyze():
    groups = get_groups()
    galaxies = []
    for group in groups:
        data = get(group['galaxy'], 'key')
        galaxies.append(GalaxyClass(group['galaxy'], data))
    other_data = get_other()
    for galaxy in galaxies:
        galaxy.run()
        galaxy.fit_OH()
        galaxy.output()
    for galaxy in other_data:
        galaxy.fit_OH()
    compare_basic(galaxies, other_data)
    make_comparison_table(galaxies, other_data)
    make_group_comparison_table(galaxies, other_data)
    for key, group in GROUPS.items():
        compare(galaxies, other_data, group, key)


################################
## Astrophysical calculations ##
################################

## Extinction ##


def extinction_k(l):
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
        return float('nan')


def correct_extinction(R_obv, fluxes, centers):
    # using the method described here:
# <http://www.astro.umd.edu/~chris/publications/html_papers/aat/node13.html>
    R_intr = 2.76
    a = 2.21
    extinction = a * math.log10(R_obv / R_intr)
    # Now using the Calzetti method:
    values = {}
    for name, flux in fluxes.items():
        flux = flux / (10 ** (-0.4 * extinction *
                              extinction_k(centers[name])))
        values.update({name: flux})
    return values


## Metallicity ##


def calculate_OH(r23, branch=None):
    """ Calculate metalicity of the region """
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


def calculate_r23(fluxes):
    r2 = fluxes['OII'] / fluxes['hbeta']
    r3 = (fluxes['OIII1'] + fluxes['OIII2']) / fluxes['hbeta']
    r23 = r2 + r3
    return r23


def fit_OH(regions, r25):
    # inital guess: flat and solar metallicity
    slope = 0
    intercept = 8.6
    x = [s.rdistance for s in regions]
    y = [s.OH for s in regions]
    remove_nan(x, y)
    x = numpy.array(x)
    y = numpy.array(y)
    x = x / r25
    
    def f((slope, intercept)):
        return y - (intercept + slope * x)
    
    return scipy.optimize.leastsq(f, (slope, intercept))


## Distance ##

def calculate_radial_distance(position1, position2, distance):
    """Calculate the distance between two sky locations at the same distance
       from earth."""
    position = coords.Position(position1)
    theta = coords.Position(position2).angsep(position)
    # radial distance returned in whatever units distance is in
    return distance * math.tan(math.radians(theta.degrees()))


## Star formation rate ##

def calculate_sfr(distance, halpha_flux):
    """halpha SFR calibration given by Kennicutt 1998"""
    d = distance * 3.0857 * (10 ** 21)
    luminosity = halpha_flux * 4 * math.pi * (d ** 2)
    return luminosity * 7.9 * (10 ** -42)
