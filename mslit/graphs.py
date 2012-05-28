#!/usr/bin/env python
# encoding: utf-8

"""
Functions for oupting graphs.

Generic plotting functions: add_solar_metallicity, plot
Single galaxy graphs: graph_metallicity, graph_sfr, graph_sfr_metals
Mutiple galaxy graphs: compare, compare_basic
"""

import matplotlib
from matplotlib.backends.backend_ps import FigureCanvasPS as FigureCanvas
import numpy
from .misc import remove_nan


matplotlib.rc('text', usetex=True)
matplotlib.rc('font', family='serif', serif='Computer Modern Roman')


## Generic plotting functions ##


def add_solar_metallicity(axes):
    """Overplot solar metallicity on a given set of axes."""
    xbound = axes.get_xbound()
    t = numpy.arange(0, xbound[1] * (4 / 3.), xbound[1] * 0.05)
    solardata = 8.69 + t * 0
    axes.plot(t, solardata, 'k--')
    axes.text(xbound[1] * (301 / 300.), 8.665, r'$Z_\odot$',
              transform=axes.transData)


def plot(galaxy_sets, axes, colors, xkey, ykey, only_corrected=False):
    """Make a plot.
       
       galaxy_sets: iterable containing sets of galaxies
       axes: axes to plot on
       colors: matplotlib color codes, matched to the sets in galaxy_sets
       xkey: x values will be region.xkey for every region in a galaxy
       ykey: y values will be region.ykey for every region in a galaxy
       only_corrected: If set to true, only plot regions with extinction
                       correction applied. Defaults to false."""
    for group, color in zip(galaxy_sets, colors):
        for galaxy in group:
            regions = galaxy.regions
            if only_corrected:
                regions = [s for s in regions if s.corrected]
            x = [r.__dict__[xkey] for r in regions]
            y = [r.__dict__[ykey] for r in regions]
            remove_nan(x, y)
            if xkey is 'rdistance':
                x = numpy.array(x)
                x = x / galaxy.r25
            axes.plot(x, y, color)


## Single Galaxy Plots ##


def graph_metalicity(galaxy):
    """Graph the O/H metallicity of a galaxy versus R/R_25 distance. Include
       a linear fitted function."""
    # setup the graph
    fig = matplotlib.figure.Figure(figsize=(5, 5))
    canvas = FigureCanvas(fig)
    axes = fig.add_axes((.125, .1, .775, .8))
    axes.set_xlabel(r'$R/R_{25}$')
    axes.set_ylabel(r'$12 + \log{\textnormal{O/H}}$')
    axes.set_autoscale_on(False)
    axes.set_xbound(lower=0, upper=1.5)
    axes.set_ybound(lower=8.0, upper=9.7)
    # plot the data
    plot(((galaxy,),), axes, ('co',), 'rdistance', 'OH')
    # overplot the fitted function
    t = numpy.arange(0, 2, .1)
    fit = galaxy.fit[0]
    fitdata = fit[1] + t * fit[0]
    axes.plot(t, fitdata, 'k-')
    #overplot solar metalicity
    add_solar_metallicity(axes)
    canvas.print_eps('tables/%s_metals.eps' % galaxy.name)


def graph_sfr(galaxy):
    """Graph the star formation rate within a galaxy versus the R/R_25
       distance."""
    # set up the graph
    fig = matplotlib.figure.Figure(figsize=(5, 5))
    canvas = FigureCanvas(fig)
    axes = fig.add_axes((.125, .1, .775, .8))
    axes.set_xlabel(r'$R/R_{25}$')
    axes.set_ylabel(r'SFR(M$_\odot$ / year)')
    axes.set_autoscalex_on(False)
    axes.set_xbound(lower=0, upper=1.5)
    # plot the data
    plot(((galaxy,),), axes, ('co',), 'rdistance', 'SFR')
    canvas.print_eps('tables/%s_sfr.eps' % galaxy.name)


def graph_sfr_metals(galaxy):
    """Graph metallicity versus star formation rate, excluding regions which
       couldn't be extinction corrected."""
    fig = matplotlib.figure.Figure(figsize=(5, 5))
    canvas = FigureCanvas(fig)
    axes = fig.add_axes((.125, .1, .775, .8))
    axes.set_xlabel(r'SFR(M$_\odot$ / year)')
    axes.set_ylabel(r'$12 + \log{\textnormal{O/H}}$')
    plot(((galaxy,),), axes, ('co',), 'SFR', 'OH', only_corrected=True)
    axes.set_xbound(lower=0)
    axes.set_ybound(lower=8.0, upper=9.7)
    axes.set_autoscale_on(False)
    add_solar_metallicity(axes)
    canvas.print_eps('tables/%s_sfr-metal.eps' % galaxy.name)


## Mutliple Galaxy Plots ##


def compare(galaxies, other, groups, key):
    """Make a plot comparing many galaxies, color coding by groups.
       
       galaxies: list my galaxies
       other: list of other galaxies
       groups: as from mslit.const.GROUPS
       key: function will check galaxy.key for all galaxies"""
    colors = ['y^', 'rd', 'mp', 'bD']
    fig = matplotlib.figure.Figure(figsize=(5, 5))
    canvas = FigureCanvas(fig)
    axes = fig.add_axes((.125, .1, .775, .8))
    axes.set_xlabel(r'$R/R_{25}$')
    axes.set_ylabel(r'$12 + \log{\textnormal{O/H}}$')
    #overplot solar metalicity
    t = numpy.arange(0, 2, .1)
    solardata = 8.69 + t * 0
    axes.plot(t, solardata, 'k--')
    axes.text(1.505, 8.665, r'$Z_\odot$')
    # plot the data
    galaxies += other
    galaxy_sets = []
    for group in groups.values():
        galaxy_set = []
        for galaxy in galaxies:
            if galaxy.__dict__[key] in group:
                galaxy_set.append(galaxy)
        galaxy_sets.append(galaxy_set)
    plot(galaxy_sets, axes, colors, 'rdistance', 'OH')
    axes.set_xbound(lower=0, upper=1.5)
    axes.set_ybound(lower=8.0, upper=9.7)
    canvas.print_eps('tables/%s_comparison.eps' % key)


def compare_basic(galaxies, other):
    """Print metallicity versus galactocentric radius for many galaxies."""
    fig = matplotlib.figure.Figure(figsize=(5, 5))
    canvas = FigureCanvas(fig)
    axes = fig.add_axes((.125, .1, .775, .8))
    axes.set_xlabel(r'$R/R_{25}$')
    axes.set_ylabel(r'$12 + \log{\textnormal{O/H}}$')
    #overplot solar metalicity
    t = numpy.arange(0, 2, .1)
    solardata = 8.69 + t * 0
    axes.plot(t, solardata, 'k--')
    axes.text(1.505, 8.665, r'$Z_\odot$', transform=axes.transData)
    # mine in color, the other data as black diamonds
    plot((other, (galaxies[0],), (galaxies[1],)), axes, ('wd', 'r^', 'co'),
         'rdistance', 'OH')
    axes.set_xbound(lower=0, upper=1.5)
    axes.set_ybound(lower=8.0, upper=9.7)
    canvas.print_eps('tables/basic_comparison.eps')
