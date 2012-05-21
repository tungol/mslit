#!/usr/bin/env python
# encoding: utf-8

"""
graphs.py - functions for oupting graphs

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
    xbound = axes.get_xbound()
    t = numpy.arange(0, xbound[1] * (4 / 3.), xbound[1] * 0.05)
    #overplot solar metalicity
    solardata = 8.69 + t * 0
    axes.plot(t, solardata, 'k--')
    axes.text(xbound[1] * (301 / 300.), 8.665, r'$Z_\odot$',
              transform=axes.transData)


def plot(galaxy_sets, axes, colors, xkey, ykey, only_corrected=False):
    for group, color in zip(galaxy_sets, colors):
        for galaxy in group:
            spectra = galaxy.spectra
            if only_corrected:
                spectra = [s for s in spectra if s.corrected]
            x = [s.__dict__[xkey] for s in spectra]
            y = [s.__dict__[ykey] for s in spectra]
            remove_nan(x, y)
            x = numpy.array(x)
            y = numpy.array(y)
            if xkey is 'rdistance':
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
    canvas.print_eps('tables/%s_metals.eps' % galaxy.num)


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
    canvas.print_eps('tables/%s_sfr.eps' % galaxy.num)


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
    canvas.print_eps('tables/%s_sfr-metal.eps' % galaxy.num)


## Mutliple Galaxy Plots ##


def compare(galaxies, other, groups, key):
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
    for group in groups:
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
    """Print metallicity versus """
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
