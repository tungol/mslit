import os, math, cmath
import pylab, numpy, scipy
import coords
from data import get_data
from generic import remove_nan, avg, rms, std

GRAPH_NUMBER = 0

def get_graph_number():
    GRAPH_NUMBER += 1
    return GRAPH_NUMBER    


## Some Math ##

def cubic_solve(b0, b1, b2, b3):
    a = b2 / b3
    b = b1 / b3
    c = (b0) / b3
    m = 2 * (a ** 3) - 9 * a * b + 27 * c
    k = (a ** 2) - 3 * b
    n = (m ** 2) - 4 * (k ** 3)
    w1 = -.5 + .5 * math.sqrt(3) * 1j
    w2 = -.5 - .5 * math.sqrt(3) * 1j
    alpha = (.5 * (m + cmath.sqrt(n))) ** (1.0/3)
    beta = (.5 * (m - cmath.sqrt(n))) ** (1.0/3)
    solution1 = -(1.0/3) * (a + alpha + beta) 
    solution2 = -(1.0/3) * (a + w2 * alpha + w1 * beta) 
    solution3 = -(1.0/3) * (a + w1 * alpha + w2 * beta)
    return [solution1, solution2, solution3]

def sigfigs_format(x, n):
    if n < 1:
        raise ValueError("number of significant digits must be >= 1")
    string = '%.*e' % (n-1, x)
    value, exponent = string.split('e')
    exponent = int(exponent)
    if exponent == 0:
        return value
    else:
        return '$%s \\times 10^{%s}$' % (value, exponent) 


## Convenience functions ##

def average(items, values, test):
    for item in items[:]:
        if not test(item):
            items.remove(item)
    results = {}
    for value in values:
        tmp = [item.__dict__[value] for item in items]
        remove_nan(tmp)
        a = avg(*tmp)
        s = std(*tmp)
        results.update({value: [a,s]})
    return results

def fit(function, parameters, y, x=None):
    def f(params):
        i = 0
        for p in parameters:
            p.set(params[i])
            i += 1
        return y - function(x)
    
    if x is None:
        x = numpy.arange(y.shape[0])
    p = [param() for param in parameters]
    return scipy.optimize.leastsq(f,p)



## Useful classes ##

class ParameterClass:
    def __init__(self, value):
        self.value = value
    
    def set(self, value):
        self.value = value
    
    def __call__(self):
        return self.value
    

class MeasurementClass:
    def __init__(self, line):
        def conv(str):
            if str == "INDEF":
                str = "NaN"
            return float(str)
        
        if line != '':
            list = line.split()
            self.center = conv(list.pop(0))
            self.cont = conv(list.pop(0))
            self.flux = conv(list.pop(0))
            self.eqw = conv(list.pop(0))
            self.core = conv(list.pop(0))
            self.gfwhm = conv(list.pop(0))
            self.lfwhm = conv(list.pop(0))
    
    def __repr__(self):
        return str(self.flux)
    
    def calculate(self):
        values = ['center', 'cont', 'flux', 'eqw', 'core', 'gfwhm', 'lfwhm']
        for value in values:
            tmp = [x.__dict__[value] for x in self.source]
            self.__dict__[value] = avg(*tmp)
            self.__dict__['%srms' % value] = rms(*tmp)
    

class SpectrumClass:
    def __init__(self, id):
        self.id = id
        try:
            self.number = int(id)
        except:
            pass
        self.measurements = []
    
    def __getattr__(self, name):
        # for all internals not otherwise defined, act like the name
        if name[0:2] == '__':
            return eval('self.id.%s' % name)
        # if 'data' is present, lookup in there too
        elif 'data' in self.__dict__:
            if name in self.data:
                return self.data[name]
        raise AttributeError
    
    def add_measurement(self, line):
        """ add a measurement from splot log files """
        self.measurements.append(MeasurementClass(line))
    
    def add_measurement2(self, name, flux):
        """ add a measurement with known name and flux """
        measurement = MeasurementClass('')
        self.measurements.append(measurement)
        measurement.flux = flux
        measurement.name = name
    
    def calculate(self):
        """ run every item in self.computed and save them as the key """
        for key, value in self.computed.items():
            try:
                self.__dict__[key] = self.call(value)
            except (ZeroDivisionError, AttributeError):
                self.__dict__[key] = float('NaN')
    
    def calculate_OH(self, disambig=True):
        """ Calculate metalicity of the spectrum """
        try:
            r23 = self.r23
        except:
            r23 = self.calculate_r23()
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
        if disambig:
            branch = self.OIII2 / self.OII
            if branch < 2:
                return solutions[2]
            else:
                return solutions[1]
        else:
            return solutions[2]
    
    def calculate_r23(self):
        """ calculate and return the value of R_23 """
        r2 = self.OII / self.hbeta
        r3 = (self.OIII1 + self.OIII2) / self.hbeta
        r23 = r2 + r3
        return r23
    
    def calculate_radial_distance(self):
        """ Calculate the galctocentric radius of the region """
        position = coords.Position('%s %s' % (self.ra, self.dec))
        theta = self.center.angsep(position)
        # radial distance in kiloparsecs
        return self.distance * math.tan(math.radians(theta.degrees()))
    
    def calculate_SFR(self):
        """halpha SFR calibration given by Kennicutt 1998"""
        d = self.distance * 3.0857 * (10 ** 21)
        flux = self.halpha
        luminosity = flux * 4 * math.pi * (d ** 2)
        return luminosity * 7.9 * (10 ** -42)
    
    def call(self, method, *args, **kwargs):
        """ call a class method given the name of the method as a string """
        return self.__class__.__dict__[method](self, *args, **kwargs)
    
    def collate_lines(self, lines):
        self.lines = {}
        for name, loc in lines.items():
            self.lines.update({name: MeasurementClass('')})
            self.lines[name].name = name
            self.lines[name].loc = loc
            sources = []
            for measurement in self.measurements:
                if measurement.name == name:
                    sources.append(measurement)
            self.lines[name].source = sources
        for name, line in self.lines.items():
            line.calculate()
            self.__dict__[name] = line.flux
    
    def correct_extinction(self):
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
        
#        using the method described here: 
#  <http://www.astro.umd.edu/~chris/publications/html_papers/aat/node13.html>
        R_intr = 2.76
        a = 2.21
        R_obv = self.halpha / self.hbeta
        if numpy.isnan(R_obv):
            self.corrected = False
            self.id = self.id + '*'
            return
        self.extinction = a * math.log10(R_obv / R_intr)
#        Now using the Calzetti method:
        for line in self.lines.values():
            line.obv_flux = line.flux
            line.flux = line.obv_flux / (10 ** 
                (-0.4 * self.extinction * k(line.loc)))
            self.__dict__[line.name] =  line.flux
        self.corrected = True
    
    def id_lines(self, lines):
        for measurement in self.measurements:
            tmp = {}
            for name in lines:
                tmp.update({(abs(measurement.center - 
                    lines[name])): name})
            name = tmp[min(tmp.keys())]
            measurement.name = name
    

class GalaxyClass:
    def __init__(self, id):
        self.id = id
        self.spectradict = {}
        self.lines = {'OII': 3727, 'hgamma': 4341, 'hbeta': 4861, 
            'OIII1': 4959, 'OIII2': 5007, 'NII1': 6548, 
            'halpha': 6563, 'NII2': 6583, 'SII1': 6717, 
            'SII2': 6731, 'OIII3': 4363}
        self.lookup = {
            'OII': '[O II]$\lambda3727$', 
            'hgamma': 'H$\gamma$', 
            'hbeta': 'H$\\beta$',
            'OIII1': '[O III]$\lambda4959$', 
            'OIII2': '[O III]$\lambda5007$',
            'NII1': '[N II]$\lambda6548$', 
            'halpha': 'H$\\alpha$', 
            'NII2': '[N II]$\lambda6583$', 
            'SII1': '[S II]$\lambda6717$', 
            'SII2': '[S II]$\lambda6731$', 
            'OIII3': '[O III]$\lambda4363$',
            'OH': '$12 + \log{\\textnormal{O/H}}$',
            'SFR': 'SFR(M$_\odot$ / year)',
            'rdistance': 'Radial Distance (kpc)',
            'extinction': 'E(B - V)',
            'r23': '$R_{23}$'
        }
        self.computed = {
            'r23': 'calculate_r23', 
            'SFR': 'calculate_SFR', 
            'rdistance': 'calculate_radial_distance', 
            'OH': 'calculate_OH'
        }
    
    def __getattr__(self, name):
        if name == 'spectra':
            spectra = self.spectradict.values()
            spectra.sort()
            return spectra
        elif name == '__repr__':
            return self.id.__repr__
        else:
            raise AttributeError
    
    def add_log(self, fn):
        def is_spectra_head(line):
            if line[:3] in ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'):
                return True
            else:
                return False
        
        def is_labels(line):
            labelstr = "    center      cont      flux       eqw"
            labelstr = labelstr + "      core     gfwhm     lfwhm\n"
            if line == labelstr:
                return True
            return False
        
        def get_num(line):
            start = line.find('[') + 1
            stop = start + 3
            return line[start:stop]
        
        with open('%s/measurements/%s.log' % (self.id, fn)) as f:
            raw = f.readlines()
        for line in raw:
            if is_spectra_head(line):
                num = get_num(line)
                if not num in self.spectradict:
                    self.spectradict.update(
                        {num: SpectrumClass(num)})
            elif is_labels(line):
                pass
            elif line.strip() != '':
                self.spectradict[num].add_measurement(line)
    
    def add_logs(self):
            logs = os.listdir('%s/measurements/' % self.id)
            for log in logs:
                if log[-4:] == '.log':
                    self.add_log(log[:-4])
    
    def add_spectra(self, num, spectra):
        self.spectradict.update({num: spectra})
    
    def calculate(self):
        data = get_data(self.id)
        center = coords.Position(self.center)
        for spectrum in self.spectra:
            sdata = data[spectrum.number]
            sdata.update({'distance': self.distance, 'center': center})
            spectrum.data = sdata
            spectrum.computed = self.computed
            spectrum.calculate()
    
    def collate_lines(self):
        for spectrum in self.spectra:
            spectrum.collate_lines(self.lines)
    
    def correct_extinction(self):
        for spectrum in self.spectra:
            spectrum.correct_extinction()
    
    def fit_OH(self):
        # inital guess: flat and solar metallicity
        slope = ParameterClass(0)
        intercept = ParameterClass(8.6)
        def function(x):
            return (intercept() + slope() * x)
        
        x = [s.rdistance for s in self.spectra]
        y = [s.OH for s in self.spectra]
        remove_nan(x, y)
        x = numpy.array(x)
        y = numpy.array(y)
        x = x / self.r25
        lsqout = fit(function, [slope, intercept], y, x)
        self.fit = lsqout
        self.grad = lsqout[0][0]
        self.metal = lsqout[0][1] + lsqout[0][0] * 0.4
        return lsqout
    
    def get_fit_slope(self):
        return self.grad
    
    def get_metallicity(self):
        return self.metal
    
    def id_lines(self):
        lines = self.lines.copy()
        for item in lines:
            lines.update({item: (lines[item] * (self.redshift + 1))})
        for spectrum in self.spectra:
            spectrum.id_lines(lines)
    
    def output_graphs(self):
        graph_metalicity(self)
        graph_SFR(self)
        graph_SFR_metals(self)
    
    def output_tables(self):
        spectra = self.spectra
        for i, spectrum in enumerate(spectra):
            spectrum.printnumber = i + 1
        make_flux_table(self)
        make_data_table(self)
    
    def run(self):
        self.add_logs()
        self.id_lines()
        self.collate_lines()
        self.correct_extinction()
        self.calculate()
        self.regions = len(self.spectra)
    


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
            (r, hbeta, OII, OIII) =  line.split('\t')
            r = float(r)
            hbeta = float(hbeta)
            OII = float(OII)
            OIII = float(OIII)
            r_23 = OII + OIII
            OII = hbeta * OII
            OIII = hbeta * OIII
            r = current.r25 * r
            spectrum = SpectrumClass(str(number))
            current.add_spectra(number, spectrum)
            spectrum.add_measurement2('hbeta', hbeta)
            spectrum.add_measurement2('OII', OII)
            spectrum.add_measurement2('OIII1', OIII)
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
            keys.update({ngc:{
            'distance': distance, 
            'r_0': r_0,
            'type': htype,
            'bar': bar,
            'ring': ring,
            'env': env
        }})
    return keys



## Make some graphs ##

def graph_metalicity(galaxy):
    graph_number = get_graph_number()
    spectra = galaxy.spectra
    OH = [s.OH for s in spectra]
    r = [s.rdistance for s in spectra]
    remove_nan(OH, r)
    OH = numpy.array(OH)
    r = numpy.array(r)
    r = r / galaxy.r25
    pylab.figure(figsize=(5,5), num=graph_number)
    pylab.xlabel('$R/R_{25}$')
    pylab.ylabel('$12 + \log{\\textnormal{O/H}}$')
    #plot the data
    pylab.plot(r, OH, 'co')
    #overplot the fitted function
    t = numpy.arange(0, 2, .1)
    fit = galaxy.fit[0]
    fitdata = fit[1] + t * fit[0]
    pylab.plot(t, fitdata, 'k-')
    #overplot solar metalicity
    solardata = 8.69 + t * 0
    pylab.plot(t, solardata, 'k--')
    v = (0, 1.5, 8.0, 9.7)
    pylab.axis(v)
    # label solar metalicity
    pylab.text(1.505, 8.665, '$Z_\odot$')
    pylab.savefig('tables/%s_metals.eps' % galaxy.id, format='eps')

def graph_SFR(galaxy):
    graph_number = get_graph_number()
    spectra = galaxy.spectra
    #remove uncorrected values
    for spectrum in spectra[:]:
        if spectrum.id[-1] == '*':
            spectra.remove(spectrum)
    SFR = [s.SFR for s in spectra]
    r = [s.rdistance for s in spectra]
    remove_nan(SFR, r)
    SFR = numpy.array(SFR)
    r = numpy.array(r)
    r = r / galaxy.r25
    pylab.figure(figsize=(5,5), num=graph_number)
    pylab.xlabel('$R/R_{25}$')
    pylab.ylabel('$SFR (M_\odot/\\textnormal{year})$')
    #plot the data
    pylab.plot(r, SFR, 'co')
    v = pylab.axis()
    v = (0, 1.5, v[2], v[3])
    pylab.axis(v)
    pylab.savefig('tables/%s_sfr.eps' % galaxy.id, format='eps')

def graph_SFR_metals(galaxy):
    graph_number = get_graph_number()
    pylab.figure(figsize=(5,5), num=graph_number)
    pylab.xlabel('SFR(M$_\odot$ / year)')
    pylab.ylabel('$12 + \log{\\textnormal{O/H}}$')
    spectra = galaxy.spectra
    #remove uncorrected values
    for spectrum in spectra[:]:
        if spectrum.id[-1] == '*':
            spectra.remove(spectrum)
    OH = [s.OH for s in spectra]
    SFR = [s.SFR for s in spectra]
    remove_nan(OH, SFR)
    pylab.plot(SFR, OH, 'co')
    v = pylab.axis()
    v = (0, v[1], 8.0, 9.7)
    t = numpy.arange(0, v[1]*1.5, v[1]*0.05)
    #overplot solar metalicity
    solardata = 8.69 + t * 0
    pylab.plot(t, solardata, 'k--')
    pylab.text(v[1] * 1.01, 8.665, '$Z_\odot$')
    pylab.axis((v[0], v[1], 8.0, 9.7))
    pylab.savefig('tables/%s_sfr-metal.eps' % galaxy.id, format='eps')

def compare_basic(galaxies, other):
    graph_number = get_graph_number()
    pylab.figure(figsize=(5,5), num=graph_number)
    pylab.xlabel('$R/R_{25}$')
    pylab.ylabel('$12 + \log{\\textnormal{O/H}}$')
    #overplot solar metalicity
    t = numpy.arange(0, 2, .1)
    solardata = 8.69 + t * 0
    pylab.plot(t, solardata, 'k--')
    pylab.text(1.505, 8.665, '$Z_\odot$')
    # plot the other data as black diamonds
    for galaxy in other:
        spectra = galaxy.spectra
        OH = [s.OH for s in spectra]
        r = [s.rdistance for s in spectra]
        remove_nan(OH, r)
        OH = numpy.array(OH)
        r = numpy.array(r)
        r = r / galaxy.r25
        pylab.plot(r, OH, 'wd')
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
    pylab.plot(data[0][0], data[0][1], 'r^')
    pylab.plot(data[1][0], data[1][1], 'co')
    pylab.axis((0, 1.5, 8.0, 9.7))
    pylab.savefig('tables/basic_comparison.eps', format='eps')

def compare_type(galaxies, other):
    graph_number = get_graph_number()
    pylab.figure(figsize=(5,5), num=graph_number)
    pylab.xlabel('$R/R_{25}$')
    pylab.ylabel('$12 + \log{\\textnormal{O/H}}$')
    #overplot solar metalicity
    t = numpy.arange(0, 2, .1)
    solardata = 8.69 + t * 0
    pylab.plot(t, solardata, 'k--')
    pylab.text(1.505, 8.665, '$Z_\odot$')
    # plot the other data
    for galaxy in other:
        spectra = galaxy.spectra
        OH = [s.OH for s in spectra]
        r = [s.rdistance for s in spectra]
        remove_nan(OH, r)
        OH = numpy.array(OH)
        r = numpy.array(r)
        r = r / galaxy.r25
        if galaxy.type in ('Sa', 'Sab'):
            pylab.plot(r, OH, 'y^')
        elif galaxy.type in ('Sb', 'Sbc'):
            pylab.plot(r, OH, 'rd')
        elif galaxy.type in ('Sc', 'Scd'):
            pylab.plot(r, OH, 'mp')
        elif galaxy.type in ('Sd', 'Irr'):
            pylab.plot(r, OH, 'bD')
    #plot my galaxies
    for galaxy in galaxies:
        spectra = galaxy.spectra
        OH = [s.OH for s in spectra]
        r = [s.rdistance for s in spectra]
        remove_nan(OH, r)
        OH = numpy.array(OH)
        r = numpy.array(r)
        r = r / galaxy.r25
        if galaxy.type in ('Sa', 'Sab'):
            pylab.plot(r, OH, 'y^')
        elif galaxy.type in ('Sb', 'Sbc'):
            pylab.plot(r, OH, 'rd')
        elif galaxy.type in ('Sc', 'Scd'):
            pylab.plot(r, OH, 'mp')
        elif galaxy.type in ('Sd', 'Irr'):
            pylab.plot(r, OH, 'bD')
    pylab.axis((0, 1.5, 8.0, 9.7))
    pylab.savefig('tables/type_comparison.eps', format='eps')

def compare_bar(galaxies, other):
    graph_number = get_graph_number()
    pylab.figure(figsize=(5,5), num=graph_number)
    pylab.xlabel('$R/R_{25}$')
    pylab.ylabel('$12 + \log{\\textnormal{O/H}}$')
    #overplot solar metalicity
    t = numpy.arange(0, 2, .1)
    solardata = 8.69 + t * 0
    pylab.plot(t, solardata, 'k--')
    pylab.text(1.505, 8.665, '$Z_\odot$')
    # plot the other data
    for galaxy in other:
        spectra = galaxy.spectra
        OH = [s.OH for s in spectra]
        r = [s.rdistance for s in spectra]
        remove_nan(OH, r)
        OH = numpy.array(OH)
        r = numpy.array(r)
        r = r / galaxy.r25
        if galaxy.bar == 'A':
            pylab.plot(r, OH, 'y^')
        elif galaxy.bar == 'AB':
            pylab.plot(r, OH, 'rd')
        elif galaxy.bar == 'B':
            pylab.plot(r, OH, 'mp')
    #plot my galaxies
    for galaxy in galaxies:
        spectra = galaxy.spectra
        OH = [s.OH for s in spectra]
        r = [s.rdistance for s in spectra]
        remove_nan(OH, r)
        OH = numpy.array(OH)
        r = numpy.array(r)
        r = r / galaxy.r25
        if galaxy.bar == 'A':
            pylab.plot(r, OH, 'y^')
        elif galaxy.bar == 'AB':
            pylab.plot(r, OH, 'rd')
        elif galaxy.bar == 'B':
            pylab.plot(r, OH, 'mp')
    pylab.axis((0, 1.5, 8.0, 9.7))
    pylab.savefig('tables/bar_comparison.eps', format='eps')

def compare_ring(galaxies, other):
    graph_number = get_graph_number()
    pylab.figure(figsize=(5,5), num=graph_number)
    pylab.xlabel('$R/R_{25}$')
    pylab.ylabel('$12 + \log{\\textnormal{O/H}}$')
    #overplot solar metalicity
    t = numpy.arange(0, 2, .1)
    solardata = 8.69 + t * 0
    pylab.plot(t, solardata, 'k--')
    pylab.text(1.505, 8.665, '$Z_\odot$')
    # plot the other data
    for galaxy in other:
        spectra = galaxy.spectra
        OH = [s.OH for s in spectra]
        r = [s.rdistance for s in spectra]
        remove_nan(OH, r)
        OH = numpy.array(OH)
        r = numpy.array(r)
        r = r / galaxy.r25
        if galaxy.ring == 's':
            pylab.plot(r, OH, 'y^')
        elif galaxy.ring == 'rs':
            pylab.plot(r, OH, 'rd')
        elif galaxy.ring == 'r':
            pylab.plot(r, OH, 'mp')
    #plot my galaxies
    for galaxy in galaxies:
        spectra = galaxy.spectra
        OH = [s.OH for s in spectra]
        r = [s.rdistance for s in spectra]
        remove_nan(OH, r)
        OH = numpy.array(OH)
        r = numpy.array(r)
        r = r / galaxy.r25
        if galaxy.ring == 's':
            pylab.plot(r, OH, 'y^')
        elif galaxy.ring == 'rs':
            pylab.plot(r, OH, 'rd')
        elif galaxy.ring == 'r':
            pylab.plot(r, OH, 'mp')
    pylab.axis((0, 1.5, 8.0, 9.7))
    pylab.savefig('tables/ring_comparison.eps', format='eps')

def compare_env(galaxies, other):
    graph_number = get_graph_number()
    pylab.figure(figsize=(5,5), num=graph_number)
    pylab.xlabel('$R/R_{25}$')
    pylab.ylabel('$12 + \log{\\textnormal{O/H}}$')
    #overplot solar metalicity
    t = numpy.arange(0, 2, .1)
    solardata = 8.69 + t * 0
    pylab.plot(t, solardata, 'k--')
    pylab.text(1.505, 8.665, '$Z_\odot$')
    # plot the other data
    for galaxy in other:
        spectra = galaxy.spectra
        OH = [s.OH for s in spectra]
        r = [s.rdistance for s in spectra]
        remove_nan(OH, r)
        OH = numpy.array(OH)
        r = numpy.array(r)
        r = r / galaxy.r25
        if galaxy.env == 'isolated':
            pylab.plot(r, OH, 'y^')
        elif galaxy.env == 'group':
            pylab.plot(r, OH, 'rd')
        elif galaxy.env == 'pair':
            pylab.plot(r, OH, 'mp')
    #plot my galaxies
    for galaxy in galaxies:
        spectra = galaxy.spectra
        OH = [s.OH for s in spectra]
        r = [s.rdistance for s in spectra]
        remove_nan(OH, r)
        OH = numpy.array(OH)
        r = numpy.array(r)
        r = r / galaxy.r25
        if galaxy.env == 'isolated':
            pylab.plot(r, OH, 'y^')
        elif galaxy.env == 'group':
            pylab.plot(r, OH, 'rd')
        elif galaxy.env == 'pair':
            pylab.plot(r, OH, 'mp')
    pylab.axis((0, 1.5, 8.0, 9.7))
    pylab.savefig('tables/env_comparison.eps', format='eps')


## Make some tables ##

def make_data_table(galaxy):
    spectra = galaxy.spectra
    values = ['rdistance', 'OH', 'SFR']
    string = ''
    string += '\\begin{tabular}{ *{4}{c}}\n'
    string += '\\toprule\n'
    string += ' Number '
    for item in values:
        string += '& %s ' % galaxy.lookup[item]
    string += '\\\\\n'
    string += '\\midrule\n'
    for spectrum in spectra:
        if spectrum.corrected == True:
            string += ' %s ' % spectrum.printnumber
        else:
            string += ' ~%s$^a$' % spectrum.printnumber
        for item in values:
            value = spectrum.__dict__[item]
            if numpy.isnan(value):
                value = '. . .'
            else:
                value = sigfigs_format(value, 2)
            string += '& %s ' % value
        string += '\\\\\n'
    string += '\\bottomrule\n'
    string += '\\end{tabular}\n'
    fn = 'tables/%s.tex' % galaxy.id
    with open(fn, 'w') as f:
        f.write(string)

def make_flux_table(galaxy):
    spectra = galaxy.spectra
    lines = galaxy.lines.keys()
    lines.sort()
    for item in lines[:]:
        unused = True
        for s in spectra:
            if not numpy.isnan(s.__dict__[item]):
                unused = False
                break
        if unused == True:
            lines.remove(item)
    string = ''
    string += '\\begin{tabular}{ *{%s}{c}}\n' % (len(lines) + 1)
    string += '\\toprule\n'
    string += ' Number '
    for item in lines:
        string += '& %s ' % galaxy.lookup[item]
    string += '\\\\\n'
    string += '\\midrule\n'
    for spectrum in spectra:
        if spectrum.corrected == True:
            string += ' %s ' % spectrum.printnumber
        else:
            string += ' ~%s$^a$' % spectrum.printnumber
        for line in lines:
            value = spectrum.__dict__[line]
            if numpy.isnan(value):
                value = '. . .'
            else:
                value = sigfigs_format(value, 2)
            string += '& %s ' % value
        string += '\\\\\n'
    string += '\\bottomrule\n'
    string += '\\end{tabular}\n'
    fn = 'tables/%sflux.tex' % galaxy.id
    with open(fn, 'w') as f:
        f.write(string)

def compare_type_table(galaxies, other):
    keys = ['grad', 'metal']
    lookup = {
        'grad': 'Gradient (dex/R$_{25}$)', 
        'metal': 'Metalicity at 0.4R$_{25}$',
    }
    for item in other:
        galaxies.append(item)
    group1 = average(galaxies[:], keys, lambda g: g.type in ('Sa', 'Sab'))
    group2 = average(galaxies[:], keys, lambda g: g.type in ('Sb', 'Sbc'))
    group3 = average(galaxies[:], keys, lambda g: g.type in ('Sc', 'Scd'))
    group4 = average(galaxies[:], keys, lambda g: g.type in ('Sd', 'Irr'))
    string = ''
    string += 'Hubble Type '
    for value in keys:
        string += '& %s & Standard Deviation ' % lookup[value]
    string += '\\\\\n'
    string += '\\midrule\n'
    string += ' Sa and Sab '
    for value in keys:
        string += '& %s ' % sigfigs_format(group1[value][0], 2)
        string += '& %s ' % sigfigs_format(group1[value][1], 2)
    string += '\\\\\n'
    string += ' Sb and Sbc '
    for value in keys:
        string += '& %s ' % sigfigs_format(group2[value][0], 2)
        string += '& %s ' % sigfigs_format(group3[value][1], 2)
    string += '\\\\\n'
    string += ' Sc and Scd '
    for value in keys:
        string += '& %s ' % sigfigs_format(group3[value][0], 2)
        string += '& %s ' % sigfigs_format(group3[value][1], 2)
    string += '\\\\\n'
    string += ' Sd '
    for value in keys:
        string += '& %s ' % sigfigs_format(group4[value][0], 2)
        string += '& %s ' % sigfigs_format(group4[value][1], 2)
    string += '\\\\\n'
    fn = 'tables/type_comparison.tex'
    with open(fn, 'w') as f:
        f.write(string)

def compare_bar_table(galaxies, other):
    keys = ['grad', 'metal']
    lookup = {
        'grad': 'Gradient (dex/R$_{25}$)', 
        'metal': 'Metalicity at 0.4R$_{25}$',
    }
    for item in other:
        galaxies.append(item)
    group1 = average(galaxies[:], keys, lambda g: g.bar == 'A')
    group2 = average(galaxies[:], keys, lambda g: g.bar == 'AB')
    group3 = average(galaxies[:], keys, lambda g: g.bar == 'B')
    string = ''
    string += ' Bar '
    for value in keys:
        string += '& %s & Standard Deviation ' % lookup[value]
    string += '\\\\\n'
    string += '\\midrule\n'
    string += ' No Bar '
    for value in keys:
        string += '& %s ' % sigfigs_format(group1[value][0], 2)
        string += '& %s ' % sigfigs_format(group1[value][1], 2)
    string += '\\\\\n'
    string += ' Weakly Barred '
    for value in keys:
        string += '& %s ' % sigfigs_format(group2[value][0], 2)
        string += '& %s ' % sigfigs_format(group3[value][1], 2)
    string += '\\\\\n'
    string += ' Strongly Barred '
    for value in keys:
        string += '& %s ' % sigfigs_format(group3[value][0], 2)
        string += '& %s ' % sigfigs_format(group3[value][1], 2)
    string += '\\\\\n'
    fn = 'tables/bar_comparison.tex'
    with open(fn, 'w') as f:
        f.write(string)

def compare_ring_table(galaxies, other):
    keys = ['grad', 'metal']
    lookup = {
        'grad': 'Gradient (dex/R$_{25}$)', 
        'metal': 'Metalicity at 0.4R$_{25}$',
    }
    for item in other:
        galaxies.append(item)
    group1 = average(galaxies[:], keys, lambda g: g.ring == 's')
    group2 = average(galaxies[:], keys, lambda g: g.ring == 'rs')
    group3 = average(galaxies[:], keys, lambda g: g.ring == 'r')
    string = ''
    string += ' Ring '
    for value in keys:
        string += '& %s & Standard Deviation ' % lookup[value]
    string += '\\\\\n'
    string += '\\midrule\n'
    string += ' S-Shaped '
    for value in keys:
        string += '& %s ' % sigfigs_format(group1[value][0], 2)
        string += '& %s ' % sigfigs_format(group1[value][1], 2)
    string += '\\\\\n'
    string += ' Intermediate Type '
    for value in keys:
        string += '& %s ' % sigfigs_format(group2[value][0], 2)
        string += '& %s ' % sigfigs_format(group3[value][1], 2)
    string += '\\\\\n'
    string += ' Ringed '
    for value in keys:
        string += '& %s ' % sigfigs_format(group3[value][0], 2)
        string += '& %s ' % sigfigs_format(group3[value][1], 2)
    string += '\\\\\n'
    fn = 'tables/ring_comparison.tex'
    with open(fn, 'w') as f:
        f.write(string)

def compare_env_table(galaxies, other):
    keys = ['grad', 'metal']
    lookup = {
        'grad': 'Gradient (dex/R$_{25}$)', 
        'metal': 'Metalicity at 0.4R$_{25}$',
    }
    for item in other:
        galaxies.append(item)
    group1 = average(galaxies[:], keys, lambda g: g.env == 'isolated')
    group2 = average(galaxies[:], keys, lambda g: g.env == 'group')
    group3 = average(galaxies[:], keys, lambda g: g.env == 'pair')
    string = ''
    string += ' Environment '
    for value in keys:
        string += '& %s & Standard Deviation ' % lookup[value]
    string += '\\\\\n'
    string += '\\midrule\n'
    string += ' Isolated '
    for value in keys:
        string += '& %s ' % sigfigs_format(group1[value][0], 2)
        string += '& %s ' % sigfigs_format(group1[value][1], 2)
    string += '\\\\\n'
    string += ' Group '
    for value in keys:
        string += '& %s ' % sigfigs_format(group2[value][0], 2)
        string += '& %s ' % sigfigs_format(group3[value][1], 2)
    string += '\\\\\n'
    string += ' Pair '
    for value in keys:
        string += '& %s ' % sigfigs_format(group3[value][0], 2)
        string += '& %s ' % sigfigs_format(group3[value][1], 2)
    string += '\\\\\n'
    fn = 'tables/env_comparison.tex'
    with open(fn, 'w') as f:
        f.write(string)

def make_comparison_table(galaxies, other):
    keys = ['grad', 'metal', 'type', 'bar', 'ring', 'env', 'regions']
    lookup = {
        'grad': 'Gradient (dex/R$_{25}$)', 
        'metal': 'Metalicity at 0.4R$_{25}$',
        'type': 'Hubble Type',
        'bar': 'Bar',
        'ring': 'Ring',
        'env': 'Environment',
        'regions': 'Number of Regions'
    }
    string = ''
    string += '\\begin{tabular}{ *{%s}{c}}\n' % (len(keys) + 1)
    string += '\\toprule\n'
    string += ' Name '
    for item in keys:
        string += '& %s ' % lookup[item]
    string += '\\\\\n'
    string += '\\midrule\n'
    for item in galaxies:
        string += ' %s ' % item.name
        for key in keys:
            value = item.__dict__[key]
            if type(value) == str:
                string += '& %s ' % value
            else:
                if numpy.isnan(value):
                    value = '. . .'
                elif key == 'regions':
                    value = str(value)
                else:
                    value = sigfigs_format(value, 3)
                string += '& %s ' % value
        string += '\\\\\n'
    string += '\\midrule\n'
    for item in other:
        string += ' %s ' % item.name
        for key in keys:
            value = item.__dict__[key]
            if type(value) == str:
                string += '& %s ' % value
            else:
                if numpy.isnan(value):
                    value = '. . .'
                elif key == 'regions':
                    value = str(value)
                else:
                    value = sigfigs_format(value, 3)
                string += '& %s ' % value
        string += '\\\\\n'
    string += '\\bottomrule\n'
    string += '\\end{tabular}\n'
    fn = 'tables/comparison.tex'
    with open(fn, 'w') as f:
        f.write(string)


def main():
	os.chdir('../n3')
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
			
	compare_basic(galaxies, other_data)
	compare_type(galaxies, other_data)
	compare_bar(galaxies, other_data)
	compare_ring(galaxies, other_data)
	compare_env(galaxies, other_data)
	make_comparison_table(galaxies, other_data)
	compare_type_table(galaxies, other_data)
	compare_bar_table(galaxies, other_data)
	compare_ring_table(galaxies, other_data)
	compare_env_table(galaxies, other_data)
	

main()
