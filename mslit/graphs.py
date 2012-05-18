import matplotlib
from matplotlib.backends.backend_ps import FigureCanvasPS as FigureCanvas
import numpy
from .misc import remove_nan


matplotlib.rc('text', usetex=True)
matplotlib.rc('font', family='serif', serif='Computer Modern Roman')


## Make some graphs ##


def graph_metalicity(galaxy):
    spectra = galaxy.spectra
    OH = [s.OH for s in spectra]
    r = [s.rdistance for s in spectra]
    remove_nan(OH, r)
    OH = numpy.array(OH)
    r = numpy.array(r)
    r = r / galaxy.r25
    fig = matplotlib.figure.Figure(figsize=(5, 5))
    canvas = FigureCanvas(fig)
    #plot the data
    axes = fig.add_axes((.125, .1, .775, .8))
    axes.set_xlabel(r'$R/R_{25}$')
    axes.set_ylabel(r'$12 + \log{\textnormal{O/H}}$')
    axes.set_autoscale_on(False)
    axes.set_xbound(lower=0, upper=1.5)
    axes.set_ybound(lower=8.0, upper=9.7)
    axes.plot(r, OH, 'co')
    #overplot the fitted function
    t = numpy.arange(0, 2, .1)
    fit = galaxy.fit[0]
    fitdata = fit[1] + t * fit[0]
    axes.plot(t, fitdata, 'k-')
    #overplot solar metalicity
    solardata = 8.69 + t * 0
    axes.plot(t, solardata, 'k--')
    # label solar metalicity
    axes.text(1.505, 8.665, r'$Z_\odot$', transform=axes.transData)
    canvas.print_eps('tables/%s_metals.eps' % galaxy.num)


def graph_sfr(galaxy):
    spectra = [s for s in galaxy.spectra if s.corrected]
    SFR = [s.SFR for s in spectra]
    r = [s.rdistance for s in spectra]
    remove_nan(SFR, r)
    SFR = numpy.array(SFR)
    r = numpy.array(r)
    r = r / galaxy.r25
    fig = matplotlib.figure.Figure(figsize=(5, 5))
    canvas = FigureCanvas(fig)
    axes = fig.add_axes((.125, .1, .775, .8))
    axes.set_xlabel(r'$R/R_{25}$')
    axes.set_ylabel(r'SFR(M$_\odot$ / year)')
    axes.set_autoscalex_on(False)
    axes.set_xbound(lower=0, upper=1.5)
    #plot the data
    axes.plot(r, SFR, 'co')
    canvas.print_eps('tables/%s_sfr.eps' % galaxy.num)


def graph_sfr_metals(galaxy):
    fig = matplotlib.figure.Figure(figsize=(5, 5))
    canvas = FigureCanvas(fig)
    axes = fig.add_axes((.125, .1, .775, .8))
    axes.set_xlabel(r'SFR(M$_\odot$ / year)')
    axes.set_ylabel(r'$12 + \log{\textnormal{O/H}}$')
    spectra = galaxy.spectra
    #remove uncorrected values
    for spectrum in spectra[:]:
        if spectrum.num[-1] == '*':
            spectra.remove(spectrum)
    OH = [s.OH for s in spectra]
    SFR = [s.SFR for s in spectra]
    remove_nan(OH, SFR)
    axes.plot(SFR, OH, 'co')
    axes.set_xbound(lower=0)
    axes.set_ybound(lower=8.0, upper=9.7)
    axes.set_autoscale_on(False)
    xbound = axes.get_xbound()
    t = numpy.arange(0, xbound[1] * 1.5, xbound[1] * 0.05)
    #overplot solar metalicity
    solardata = 8.69 + t * 0
    axes.plot(t, solardata, 'k--')
    axes.text(xbound[1] * 1.01, 8.665, r'$Z_\odot$')
    canvas.print_eps('tables/%s_sfr-metal.eps' % galaxy.num)


def compare_basic(galaxies, other):
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
    # plot the other data as black diamonds
    for galaxy in other:
        spectra = galaxy.spectra
        OH = [s.OH for s in spectra]
        r = [s.rdistance for s in spectra]
        remove_nan(OH, r)
        OH = numpy.array(OH)
        r = numpy.array(r)
        r = r / galaxy.r25
        axes.plot(r, OH, 'wd')
    #plot my galaxies
    data = []
    for galaxy in galaxies:
        spectra = galaxy.spectra
        OH = [s.OH for s in spectra]
        r = [s.rdistance for s in spectra]
        remove_nan(OH, r)
        OH = numpy.array(OH)
        r = numpy.array(r)
        r = r / galaxy.r25
        data.append((r, OH))
    axes.plot(data[0][0], data[0][1], 'r^')
    axes.plot(data[1][0], data[1][1], 'co')
    axes.set_xbound(lower=0, upper=1.5)
    axes.set_ybound(lower=8.0, upper=9.7)
    canvas.print_eps('tables/basic_comparison.eps')


def plot(galaxies, key, axes, groups):
    colors = ['y^', 'rd', 'mp', 'bD']
    for galaxy in galaxies:
        spectra = galaxy.spectra
        OH = [s.OH for s in spectra]
        r = [s.rdistance for s in spectra]
        remove_nan(OH, r)
        OH = numpy.array(OH)
        r = numpy.array(r)
        r = r / galaxy.r25
        for group, color in zip(groups, colors):
            if galaxy.__dict__[key] in group:
                axes.plot(r, OH, color)

def compare(galaxies, other, groups, key):
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
    # plot the other data
    plot(other, key, axes, groups.values())
    #plot my galaxies
    plot(galaxies, key, axes, groups.values())
    axes.set_xbound(lower=0, upper=1.5)
    axes.set_ybound(lower=8.0, upper=9.7)
    canvas.print_eps('tables/%s_comparison.eps' % key)
