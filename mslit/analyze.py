#!/usr/bin/env python
# encoding: utf-8

"""
Functions for preforming analysis of measured data.

Primary entry point is the analyze function.

Classes: GalaxyClass, RegionClass

Functions:
Parsing splot logs: get_measurements, get_num, is_labels, is_region_head,
                    parse_line, parse_log
Processing data: collate_lines, id_lines
Parsing data from other_data: process_galaxies, parse_keyfile, get_other
calculating extinction: correct_extinction, extinction_k
calculating metallicity: calculate_OH, calculate_r23, fit_OH
other calculations: calculate_radial_distance, calculate_sfr

"""

from __future__ import with_statement
import math
import os
import os.path
import coords
import numpy
import scipy.optimize
from .const import GROUPS, LINES, LOG_FORMAT
from .data import get, get_groups
from .graphs import compare, compare_basic
from .graphs import graph_metalicity, graph_sfr, graph_sfr_metals
from .misc import avg, cubic_solve, remove_nan
from .tables import make_comparison_table, make_data_table, make_flux_table
from .tables import make_group_comparison_table


def analyze():
    """Run the complete set of data analyzations and output tables and
       graphs."""
    if not os.path.isdir('tables'):
        os.mkdir('tables')
    groups = get_groups()
    galaxies = []
    for group in groups:
        data = get(group['galaxy'], 'key')
        galaxies.append(GalaxyClass(group['galaxy'], data))
    for galaxy in galaxies:
        galaxy.run()
        galaxy.fit_OH()
        galaxy.output()
    other_data = get_other()
    for galaxy in other_data:
        galaxy.fit_OH()
    compare_basic(galaxies, other_data)
    make_comparison_table(galaxies, other_data)
    make_group_comparison_table(galaxies, other_data)
    for key, group in GROUPS.items():
        compare(galaxies, other_data, group, key)


## Useful classes ##


class GalaxyClass:
    """A class for information related to a galaxy of multiple regions."""
    
    def __init__(self, name, data):
        self.name = name     # basic name, for id purposes
        self.regions = []    # list of all the regions, empty for now
        self.fit = None     # least square fitting solution for metallicity
        self.grad = None     # fitted O/H metallicity gradient
        self.metal = None       # standard metallicity of galaxy
        self.region_number = None       # number of regions in galaxy
        self.print_name = data['name']      # printable name for galaxy
        self.distance = data['distance'] # distance to galaxy in kpc
        self.r25 = data['r25']  # r_25 scale measure, in kpc
        self.type = data['type']    # Sa to Sd hubble type
        self.bar = data['bar']      # bar type
        self.ring = data['ring']    # ring type
        self.env = data['env']      # environment: group, pair, isolated
        if 'redshift' in data:
            self.redshift = data['redshift']  # redshift factor for galaxy
        if 'center' in data:
            self.center = data['center']    # Galactic center as RA, DEC string
    
    def fit_OH(self):
        """Find a linear fit of O/H metallicity in galaxy using least
           squares fitting."""
        self.fit = fit_OH(self.regions, self.r25)
        self.grad = self.fit[0][0]
        # standard metallicity is the metallicity at r = 0.4
        self.metal = self.fit[0][1] + self.grad * 0.4
    
    def output(self):
        """Produce table and graph output."""
        graph_metalicity(self)
        graph_sfr(self)
        graph_sfr_metals(self)
        # remove regions with no data
        # go backwards so that indexing is kept as items are deleted
        for region in self.regions[::-1]:
            if numpy.isnan(region.fluxes['halpha']):
                del self.regions[region.number]
        for count, region in enumerate(self.regions):
            region.printnumber = count + 1
        make_flux_table(self)
        make_data_table(self)
    
    def run(self):
        """Setup a galaxy from splot measurements."""
        measurements = get_measurements(self.name)
        self.region_number = len([r for r in measurements if r != []])
        lines = LINES.copy()
        for key, value in lines.items():
            lines.update({key: (value * (self.redshift + 1))})
        for group in measurements:
            id_lines(group, lines)
        groups = [collate_lines(region) for region in measurements]
        data = get(self.name, 'positions')
        for i, (fluxes, centers) in enumerate(groups):
            region = RegionClass(i, fluxes, centers)
            region.distance = self.distance
            region.position = '%s %s' % (data[i]['ra'], data[i]['dec'])
            region.center = self.center
            region.calculate()
            self.regions.append(region)
    

class RegionClass:
    """A class for data related to individual regions."""
    
    def __init__(self, number, fluxes, centers=None):
        self.number = number     # number of the region
        self.fluxes = fluxes     # list of averaged flux measurements
        self.centers = centers   # list of averaged wavelength centers
        self.corrected = False  # has extinction correction been applied?
        self.distance = None    # distance to galaxy
        self.center = None      # RA, Dec of galactic center
        self.OH = None      # O/H metallicity
        self.SFR = None        # Star formation rate
        self.rdistance = None   # galactocentric radius
        self.position = None        # RA, Dec of the region
        self.r23 = None     # r23 metallicity
    
    def calculate(self):
        """Perform astrophysical calculations related to the region."""
        self.correct_extinction()
        self.rdistance = calculate_radial_distance(self.position, self.center,
                                                   self.distance)
        self.r23 = calculate_r23(self.fluxes)
        self.calculate_OH()
        self.SFR = calculate_sfr(self.distance, self.fluxes['halpha'])
    
    def calculate_OH(self, disambig=True):
        """Calculate O/H metallicity for a region, optionally checking which
           branch of the solution it is on."""
        if disambig:
            branch = self.fluxes['OIII2'] / self.fluxes['OII']
            self.OH = calculate_OH(self.r23, branch)
        self.OH = calculate_OH(self.r23)
    
    def correct_extinction(self):
        """If possible, correct for all the regions flux measurements for
           extinction."""
        R_obv = self.fluxes['halpha'] / self.fluxes['hbeta']
        if not numpy.isnan(R_obv):
            self.fluxes = correct_extinction(R_obv, self.fluxes, self.centers)
            self.corrected = True
    

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
    """For all the measurements in a region, determine which spectral line
       they are closest to in wavelength."""
    for measurement in region:
        badness = dict([(abs(measurement['center'] - lines[name]), name)
                        for name in lines])
        measurement.update({'name': badness[min(badness.keys())]})


## Functions for reading in tables of data ##


def process_galaxies(fn, galaxydict):
    """Read data from a file in other_data, and add that data to the
       appropriate galaxy in galaxydict."""
    with open('other_data/%s' % fn) as f:
        raw = [line.strip() for line in f.readlines()]
    current = None
    number = None
    for line in raw:
        if line == '':
            pass
        elif line[0] == '*':
            current = galaxydict[line[1:]]
            number = 0
        else:
            (r, hbeta, r2, r3) = [float(item) for item in line.split('\t')]
            data = {'hbeta': hbeta, 'OII': r2 * hbeta, 'OIII1': r3 * hbeta}
            region = RegionClass(number, data)
            region.r23 = r2 + r3
            region.rdistance = current.r25 * r
            region.distance = current.distance
            region.calculate_OH(disambig=False)
            current.regions.append(region)
            number += 1


def parse_keyfile():
    """Return a dictionary of the galaxies described in other_data/key.txt."""
    with open('other_data/key.txt') as f:
        raw = f.readlines()
    del raw[0]
    galaxydict = {}
    for line in raw:
        line = line.strip()
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


def get_other():
    """Return a list of galaxy objects, one for each galaxy described in
       the other_data directory."""
    files = os.listdir('other_data/')
    files = [fn for fn in files if fn.startswith('table')]
    galaxydict = parse_keyfile()
    for fn in files:
        process_galaxies(fn, galaxydict)
    for galaxy in galaxydict.values():
        galaxy.region_number = len(galaxy.regions)
    return galaxydict.values()


## Calculating extinction ##


def correct_extinction(R_obv, fluxes, centers):
    """Given an halpha/hbeta ratio, and a list of fluxes and their wavelength
       locations, return extinction corrected fluxes. Uses the Calzetti
       method."""
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


def extinction_k(l):
    """Inner 'k' function for use in the Calzetti method of extinction
       correction."""
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


## Calculating metallicity ##


def calculate_OH(r23, branch=None):
    """Convert r_23 to O/H metallicity, using conversion given by Nagao
       2006."""
    b0 = 1.2299 - math.log10(r23)
    b1 = -4.1926
    b2 = 1.0246
    b3 = -6.3169 * 10 ** -2
    # solving the equation
    solutions = cubic_solve(b0, b1, b2, b3)
    solutions = [x.real if x.imag == 0.0 else float('nan') for x in solutions]
    if branch is not None:
        # if given, branch should be the ratio OIII2 / OII
        if branch < 2:
            return solutions[2]
        return solutions[1]
    return solutions[2]


def calculate_r23(fluxes):
    """Return the calucated R_23 metallicity, given a set of fluxes."""
    r2 = fluxes['OII'] / fluxes['hbeta']
    r3 = (fluxes['OIII1'] + fluxes['OIII2']) / fluxes['hbeta']
    r23 = r2 + r3
    return r23


def fit_OH(regions, r25):
    """Use least squares method to find a linear fit for O/H metallicity over
       a set of regions."""
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
        """Function to be fit by scipy.optimize.leastsq."""
        return y - (intercept + slope * x)
    
    return scipy.optimize.leastsq(f, (slope, intercept))


## Other calculations ##

def calculate_radial_distance(position1, position2, distance):
    """Calculate the distance between two sky locations at the same distance
       from earth."""
    position = coords.Position(position1)
    theta = coords.Position(position2).angsep(position)
    # radial distance returned in whatever units distance is in
    return distance * math.tan(math.radians(theta.degrees()))


def calculate_sfr(distance, halpha_flux):
    """Calculate star formation rate from H_alpha flux, using the calibration
       given by Kennicutt 1998."""
    d = distance * 3.0857 * (10 ** 21)
    luminosity = halpha_flux * 4 * math.pi * (d ** 2)
    return luminosity * 7.9 * (10 ** -42)
