import os
import math
import pylab
import coords
import div3lib
import numpy

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
			self.flux = conv(list.pop(0)) / (10 ** -16)
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
			self.__dict__[value] = div3lib.avg(*tmp)
			self.__dict__['%srms' % value] = div3lib.rms(*tmp)
	

class SpectrumClass:
	def __init__(self, id):
		self.id = id
		try:
			self.number = int(id)
		except:
			pass
		self.measurements = []
		self.diagnostics = {
			'r23': 'calculate_r23', 
			'extinction': 'get_extinction', 
			'SFR': 'calculate_SFR', 
			'rdistance': 'calculate_radial_distance', 
			'OH': 'calculate_OH'
		}
	
	def __getattr__(self, name):
		if name[0:2] == '__':
			return eval('self.id.%s' % name)
		elif 'data' in self.__dict__:
			if name in self.data:
				return self.data[name]
		raise AttributeError
	
	def add_measurement(self, line):
		self.measurements.append(MeasurementClass(line))
	
	def add_measurement2(self, name, flux):
		measurement = MeasurementClass('')
		self.measurements.append(measurement)
		measurement.flux = flux
		measurement.name = name
	
	def calculate(self):
		for key, value in self.diagnostics.items():
			try:
				self.__dict__[key] = self.call(value)
			except (ZeroDivisionError, AttributeError):
				self.__dict__[key] = float('NaN')
	
	def calculate_OH(self, disambig=True):
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
		solutions = div3lib.cubic_solve(b0, b1, b2, b3)
		for i, item in enumerate(solutions):
			if item.imag == 0.0:
				solutions[i] = item.real
			else:
				solutions[i] = float('NaN')
		if disambig:
			branch = self.OIII2.flux / self.OII.flux
			_branch = self._OIII2 / self._OII
			if _branch < 2:
				return solutions[2]
			else:
				return solutions[1]
		else:
			return solutions[2]
	
	def calculate_r23(self):
		r2 = self.OII.flux / self.hbeta.flux
		_r2 = self._OII / self._hbeta
		r3 = (self.OIII1.flux + self.OIII2.flux) / self.hbeta.flux
		_r3 = (self._OIII1 + self._OIII2) / self._hbeta
		r23 = r2 + r3
		_r23 = _r2 + _r3
		return _r23
	
	def calculate_radial_distance(self):
		position = coords.Position('%s %s' % (self.ra, self.dec))
		theta = self.center.angsep(position)
		# radial distance in kiloparsecs
		return self.distance * math.tan(math.radians(theta.degrees()))
	
	def calculate_SFR(self):
		'''halpha calibration given by Kennicutt 1998'''
		d = self.distance * 3.0857 * (10 ** 21)
		flux = self.halpha.flux * (10 ** -16) 
		_flux = self._halpha * (10 ** -16)
		luminosity = flux * 4 * math.pi * (d ** 2)
		_luminosity = _flux * 4 * math.pi * (d ** 2)
		return _luminosity * 7.9 * (10 ** -42)
	
	def call(self, method, *args, **kwargs):
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
			self.__dict__[name] = line
			self.__dict__['_' + name] = line.flux
	
	def correct_extinction(self):
		def k(l):
			# for use in the calzetti method
			# convert to micrometers from angstrom		
			l = l / 10000.
			if 0.63 <= l <= 1.0:
				return ((1.86 / l ** 2) - (0.48 / l ** 3) - (0.1 / l) + 1.73)
			elif 0.12 <= l < 0.63:
				return (2.656 * (-2.156 + (1.509 / l) - (0.198 / l ** 2) + 
				(0.011 / l ** 3)) + 4.88)
			else:
				raise ValueError
		
# 		using the method described here: 
# 	<http://www.astro.umd.edu/~chris/publications/html_papers/aat/node13.html>
		R_intr = 2.76
		a = 2.21
		R_obv = self.halpha.flux / self.hbeta.flux
		_R_obv = self._halpha / self._hbeta
		if numpy.isnan(_R_obv):
			self.id = self.id + '*'
			return
		self.E = a * math.log10(R_obv / R_intr)
# 		Now using the Calzetti method:
		for line in self.lines.values():
			line.obv_flux = line.flux * (10 ** -16)
			line.flux = line.obv_flux / (10 ** (-0.4 * self.E * k(line.loc)))
			line.flux = line.flux / (10 ** -16)
			self.__dict__['_' + line.name] =  line.flux
	
	def get_extinction(self):
		return self.E
	
	def id_lines(self, lines):
		for measurement in self.measurements:
			tmp = {}
			for name in lines:
				tmp.update({(abs(measurement.center - lines[name])): name})
			name = tmp[min(tmp.keys())]
			measurement.name = name
	

class GalaxyClass:
	def __init__(self, name):
		self.name = name
		self.spectradict = {}
		self.lines = {'OII': 3727, 'hgamma': 4341, 'hbeta': 4861, 
			'OIII1': 4959, 'OIII2': 5007, 'NII1': 6548, 
			'halpha': 6563, 'NII2': 6583, 'SII1': 6717, 
			'SII2': 6731, 'OIII3': 4363}
		self.short = {
			'OII': '[O II] 3727', 
			'hgamma': 'hgamma', 
			'hbeta': 'hbeta',
			'OIII1': '[O III] 4959', 
			'OIII2': '[O III] 5007',
			'NII1': '[N II] 6548', 
			'halpha': 'halpha', 
			'NII2': '[N II] 6583', 
			'SII1': '[S II] 6717', 
			'SII2': '[S II] 6731', 
			'OIII3': '[O III] 4363',
			'OH': '$12 + \log(O/H)$',
			'SFR': 'SFR(M$_\odot$ / year)',
			'rdistance': 'Radial Distance (kpc)',
			'extinction': 'E(B - V)'
		}
	
	def __getattr__(self, name):
		if name == 'spectra':
			spectra = self.spectradict.values()
			spectra.sort()
			return spectra
		elif name == '__repr__':
			return self.name.__repr__
		else:
			raise AttributeError
	
	def add_log(self, fn):
		def is_spectra_head(line):
			if line[:3] in ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul',
				'Aug', 'Sep', 'Oct', 'Nov', 'Dec'):
				return True
			else:
				return False
		
		def is_labels(line):
			labelstr = "    center      cont      flux       eqw      core"
			labelstr = labelstr + "     gfwhm     lfwhm\n"
			if line == labelstr:
				return True
			return False
		
		def get_num(line):
			start = line.find('[') + 1
			stop = start + 3
			return line[start:stop]
		
		file = open('%s/measurements/%s.log' % (self.name, fn))
		raw = file.readlines()
		file.close()
		for line in raw:
			if is_spectra_head(line):
				num = get_num(line)
				if not num in self.spectradict:
					self.spectradict.update({num: SpectrumClass(num)})
			elif is_labels(line):
				pass
			elif line.strip() != '':
				self.spectradict[num].add_measurement(line)
	
	def add_logs(self):
			logs = os.listdir('%s/measurements/' % self.name)
			for log in logs:
				if log[-4:] == '.log':
					self.add_log(log[:-4])
	
	def add_spectra(self, num, spectra):
		self.spectradict.update({num: spectra})
	
	def calculate(self):
		data = div3lib.get_data(self.name)
		center = coords.Position(self.location)
		for spectrum in self.spectra:
			sdata = data[spectrum.number]
			sdata.update({'distance': self.distance, 'center': center})
			spectrum.data = sdata
			spectrum.calculate()
	
	def collate_lines(self):
		for spectrum in self.spectra:
			spectrum.collate_lines(self.lines)
	
	def correct_extinction(self):
		for spectrum in self.spectra:
			spectrum.correct_extinction()
	
	def fit_OH(self):
		# inital guess: flat and solar metallicity
		slope = div3lib.ParameterClass(0)
		intercept = div3lib.ParameterClass(8.6)
		def function(x):
			return (intercept() + slope() * x)
		
		x = [s.rdistance for s in self.spectra]
		y = [s.OH for s in self.spectra]
		div3lib.remove_nan(x, y)
		x = numpy.array(x)
		y = numpy.array(y)
		x = x / self.r25
		fit = div3lib.fit(function, [slope, intercept], y, x)
		self.fit = fit
		self.grad = fit[0][0]
		self.metal = fit[0][1] + fit[0][0] * 0.4
		return fit
	
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
	
	def output_tables(self):
		fn = 'tables/%s.tex' % self.name
		file = open(fn, 'w')
		spectra = self.spectra
		lines = self.lines.keys()
		lines.sort()
		for item in lines[:]:
			unused = True
			for s in spectra:
				if not numpy.isnan(s.__dict__[item].flux):
					unused = False
					break
			if unused == True:
				lines.remove(item)
		diagnostics = spectra[0].diagnostics.keys()
		file.write('\\documentclass{article}\n')
		file.write('\\usepackage{rotating}\n')
		file.write('\\usepackage{booktabs}\n')
		file.write('\\usepackage{graphicx}\n\n')
		file.write('\\begin{document}\n\n')
		file.write(div3lib.make_table(spectra, lines, self.short))
		file.write(div3lib.make_table(spectra, diagnostics, self.short))
		file.write('\\end{document}\n')
		file.close()
	
	def run(self):
		self.add_logs()
		self.id_lines()
		self.collate_lines()
		self.correct_extinction()
		self.calculate()
	

def get_other():
	files = os.listdir('../other_data/')
	keyfile = files.pop(0)
	keys = parse_keyfile(keyfile)
	others = []
	for item in files:
		galaxies = get_galaxies(item, keys)
		for galaxy in galaxies:
			others.append(galaxy)
	return others

def compare(galaxies, other):
	graph_number - get_graph_number()
	pylab.figure(figsize=(5,5), num=graph_number)
	pylab.xlabel('Radial Distance $R/R_{25}$')
	pylab.ylabel('$12 + \log(O/H)$')
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
		div3lib.remove_nan(OH, r)
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
		div3lib.remove_nan(OH, r)
		OH = numpy.array(OH)
		r = numpy.array(r)
		r = r / galaxy.r25
		data.append((r, OH))
	pylab.plot(data[0][0], data[0][1], 'ro')
	pylab.plot(data[1][0], data[1][1], 'co')
	pylab.axis((0, 1.5, 8.0, 9.7))
	pylab.savefig('tables/compare.eps', format='eps')

def parse_keyfile(fn):
	keyfile = open('../other_data/%s' % fn, 'r')
	raw = keyfile.readlines()
	keyfile.close()
	keys = {}
	for line in raw:
		if line[0:3] == 'ngc':
			pass
		else:
			line = line.strip()
			(ngc, distance, r_0, htype, bar) = line.split('\t')
			# convert distance to kpc from Mpc for consistency
			distance = float(distance) * 1000
			# convert r_0 from arcminutes to kpc
			r_0 = distance * math.tan(math.radians(float(r_0) * 60))
			htype = int(htype)
			bar = int(bar)
			keys.update({ngc:{
			'distance': distance, 
			'r_0': r_0,
			'type': htype,
			'bar': bar
		}})
	return keys

def get_galaxies(fn, keys):
	gfile = open('../other_data/%s' % fn, 'r')
	raw = gfile.readlines()
	gfile.close()
	galaxies = []
	current = None
	number = None
	for line in raw:
		line = line.strip()
		if line == '':
			pass
		elif line[0] == '*':
			name = line[1:]
			current = GalaxyClass(name)
			number = 0
			galaxies.append(current)
			current.distance = keys[name]['distance']
			current.r25 = keys[name]['r_0']
			current.type = keys[name]['type']
			current.bar = keys[name]['bar']
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

def graph_metalicity(galaxy):
	graph_number = get_graph_number()
	spectra = galaxy.spectra
	OH = [s.OH for s in spectra]
	r = [s.rdistance for s in spectra]
	div3lib.remove_nan(OH, r)
	OH = numpy.array(OH)
	r = numpy.array(r)
	r = r / galaxy.r25
	pylab.figure(figsize=(5,5), num=graph_number)
	pylab.xlabel('Radial Distance $R/R_{25}$')
	pylab.ylabel('$12 + \log(O/H)$')
	#plot the data
	pylab.plot(r, OH, 'o')
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
	pylab.savefig('tables/%s_imetals.eps' % galaxy.name, format='eps')

def graph_SFR(galaxy):
	graph_number = get_graph_number()
	spectra = galaxy.spectra
	#remove uncorrected values
	for spectrum in spectra[:]:
		if spectrum.id[-1] == '*':
			spectra.remove(spectrum)
	SFR = [s.SFR for s in spectra]
	r = [s.rdistance for s in spectra]
	div3lib.remove_nan(SFR, r)
	SFR = numpy.array(SFR)
	r = numpy.array(r)
	r = r / galaxy.r25
	pylab.figure(figsize=(5,5), num=graph_number)
	pylab.xlabel('Radial Distance $R/R_{25}$')
	pylab.ylabel('$SFR (M_\odot/\\textnormal{year})$')
	#plot the data
	pylab.plot(r, SFR, 'o')
	v = pylab.axis()
	v = (0, 1.5, v[2], v[3])
	pylab.axis(v)
	pylab.savefig('tables/%s_sfr.eps' % galaxy.name, format='eps')

def graph_metal_SFR(galaxy):
	graph_number = get_graph_number()
	pylab.figure(figsize=(5,5), num=graph_number)
	pylab.xlabel('SFR(M$_\odot$ / year)')
	pylab.ylabel('$12 + \log(O/H)$')
	spectra = galaxy.spectra
	#remove uncorrected values
	for spectrum in spectra[:]:
		if spectrum.id[-1] == '*':
			spectra.remove(spectrum)
	OH = [s.OH for s in spectra]
	SFR = [s.SFR for s in spectra]
	div3lib.remove_nan(OH, SFR)
	pylab.plot(SFR, OH, 'o')
	v = pylab.axis()
	v = (0, v[1], 8.0, 9.7)
	t = numpy.arange(0, v[1]*1.5, v[1]*0.05)
	#overplot solar metalicity
	solardata = 8.69 + t * 0
	pylab.plot(t, solardata, 'k--')
	pylab.text(v[1] * 1.01, 8.665, '$Z_\odot$')
	pylab.axis((v[0], v[1], 8.0, 9.7))
	pylab.savefig('tables/%s_sfr-metal.eps' % galaxy.name, format='eps')

def get_graph_number():
	global graph_number
	try:
		graph_number += 1
	except NameError:
		graph_number = 0
	return graph_number	

def main():
	os.chdir('../n3')
	ngc3169 = GalaxyClass('ngc3169')
	ngc3169.redshift = 0.004130
	ngc3169.location = '10:14:15.0 +03:27:58'
	ngc3169.distance = 20100 #kpc
	ngc3169.r25 = 11.57 #kpc
	ngc3169.run()
	ngc3169.fit_OH()
	
	ngc4725 = GalaxyClass('ngc4725')
	ngc4725.redshift = 0.004023
	ngc4725.location = '12:50:26.6 +25:30:03'
	ngc4725.distance = 13918 #kpc
	ngc4725.r25 = 26.23 #kpc
	ngc4725.run()
	ngc4725.fit_OH()
	
	galaxies = (ngc3169, ngc4725)
	other_data = get_other()
	ngc3169.output_tables()
	ngc4725.output_tables()
	
	for galaxy in galaxies:
		graph_metalicity(galaxy)
		graph_SFR(galaxy)
		graph_metal_SFR(galaxy)
		print '%s: %s' % (galaxy.name, galaxy.get_metallicity())
		print '\t%s' % galaxy.get_fit_slope()
	
#	for galaxy in other_data:
#		galaxy.fit_OH()
#		graph_metalicity(galaxy)
#		print '%s: %s' % (galaxy.name, galaxy.get_metallicity())
#		print '\t%s' % galaxy.get_fit_slope()
		
	compare(galaxies, other_data)

main()
