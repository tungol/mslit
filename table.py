import os, math

class MeasurementClass:
	def __init__(self, line):
		if line != '':
			list = line.split()
			self.center = self.conv(list.pop(0))
			self.cont = self.conv(list.pop(0))
			self.flux = self.conv(list.pop(0))
			self.eqw = self.conv(list.pop(0))
			self.core = self.conv(list.pop(0))
			self.gfwhm = self.conv(list.pop(0))
			self.lfwhm = self.conv(list.pop(0))

	def conv(self, str):
		if str == "INDEF":
			str = "NaN"
		return float(str)

	def calculate(self):
		values = ['center', 'cont', 'flux', 'eqw', 'core', 'gfwhm', 'lfwhm']
		for value in values:
			tmp = [x.__dict__[value] for x in self.source]
			self.__dict__[value] = self.avg(*tmp)
			self.__dict__['%srms' % value] = self.rms(*tmp)

	def avg(self, *args):
		if len(args) == 0:
			args = ["0"]
		floatNums = [float(x) for x in args]
		return sum(floatNums) / len(args)

	def rms(self, *args):
		if len(args) == 0:
			args = ["0"]
		squares = [(float(x) ** 2) for x in args]
		return math.sqrt(self.avg(*squares))

class SpectrumClass:
	def __init__(self, num):
		self.num = num
		self.measurements = []
		self.short = {'[O II] 3727': 'OII', 'hgamma': 'hgamma', 'hbeta': 'hbeta',
                        '[O III] 4959': 'OIII1', '[O III] 5007': 'OIII2', '[N II] 6548': 'NII1',
                        'halpha': 'halpha', '[N II] 6583': 'NII2', '[S II] 6717': 'SII1',
                        '[S II] 6731': 'SII2', '[O III] 4363': 'OIII3'}
		self.diagnostics = { 
			'r23': (lambda s: (s.OII.flux + s.OIII1.flux + s.OIII2.flux) / s.hbeta.flux), 
			'a23': (lambda s: (s.OIII1.flux + s.OIII2.flux) / s.OII.flux),
			'NII2 / halpha': (lambda s: s.NII2.flux / s.halpha.flux),
			'OIII2 / NII2': (lambda s: s.OIII2.flux / s.NII2.flux),
			'NII2 / OII': (lambda s: s.NII2.flux / s.OII.flux),
			'OIII2 / OII': (lambda s: s.OIII2.flux / s.OII.flux),
			'halpha / hbeta': (lambda s: s.halpha.flux / self.hbeta.flux)}

	def __lt__(self, other):
		return self.num.__lt__(other)
		
	def __gt__(self, other):
		return self.num.__gt__(other)

	def __eq__(self, other):
		return self.num.__eq__(other)

	def __ne__(self, other):
		return self.num.__ne__(other)

	def __repr__(self):
		return self.num

	def add_measurement(self, line, type):
		self.measurements.append(MeasurementClass(line))
		self.measurements[-1].type = type

	def id_lines(self, lines):
		for measurement in self.measurements:
			tmp = {}
			for line in lines:
				tmp.update({(abs(measurement.center - lines[line])): line})
			line = tmp[min(tmp.keys())]
			measurement.line = line

	def collate_lines(self, lines):
		self.lines = {}
		for line, loc in lines.items():
			self.lines.update({line: MeasurementClass('')})
			self.lines[line].line = line
			self.lines[line].loc = loc
			tmp = []
			for measurement in self.measurements:
				if measurement.line == line:
					tmp.append(measurement)
			self.lines[line].source = tmp
			self.lines[line].name = line
		for key, value in self.short.items():
			self.__dict__[value] = self.lines[key]
			self.__dict__[key] = self.lines[key]
		for line in self.lines.values():
			line.calculate()

	def calculate(self):
		for key, value in self.diagnostics.items():
			try:
				self.__dict__[key] = value(self)
			except ZeroDivisionError:
				self.__dict__[key] = 'INDEF'

	def correct_extinction(self):
		def k(l):
			# for use in the calzetti method
			# convert to micrometers from angstrom		
			l = l / 10000.
			if 0.63 <= l <= 1.0:
				return ((1.86 / l ** 2) - (0.48 / l ** 3) - (0.1 / l) + 1.73)
			elif 0.12 <= l < 0.63:
				return (2.656 * (-2.156 + (1.509 / l) - (0.198 / l ** 2) + (0.011 / 
				l ** 3)) + 4.88)
			else:
				raise ValueError

# 		using the method described here: 
# 		<http://www.astro.umd.edu/~chris/publications/html_papers/aat/node13.html>

		R_intr = 2.76
		a = 2.21
		try:
			R_obv = self.halpha.flux / self.hbeta.flux
			self.E = a * math.log10(R_obv / R_intr)

# 		Now using the Calzetti method:
			for line in self.lines.values():
				line.obv_flux = line.flux
				line.flux = line.obv_flux / (10 ** (-0.4 * self.E * k(line.loc)))
		except OverflowError:
			self.num = self.num + '*'
		except ZeroDivisionError:
			self.num = self.num + '*'

class ImageClass:
	def __init__(self, name):
		self.name = name
		self.spectradict = {}
		self.lines = {'[O II] 3727': 3727, 'hgamma': 4341, 'hbeta': 4861, 
			'[O III] 4959': 4959, '[O III] 5007': 5007, '[N II] 6548': 6548, 
			'halpha': 6563, '[N II] 6583': 6583, '[S II] 6717': 6717, 
			'[S II] 6731': 6731, '[O III] 4363': 4363}

	def add_log(self, fn):
		file = open('%s/measurements/%s.log' % (self.name, fn))
		raw = file.readlines()
		file.close()
		for line in raw:
			if self.is_spectra_head(line):
				num = self.get_num(line)
				if not num in self.spectradict:
					self.spectradict.update({num: SpectrumClass(num)})
			elif self.is_labels(line):
				pass
			elif line.strip() != '':
				self.spectradict[num].add_measurement(line, fn)

	def add_logs(self):
			logs = os.listdir('%s/measurements/' % self.name)
			for log in logs:
				if log[-4:] == '.log':
					self.add_log(log[:-4])

	def is_labels(self, line):
		if (line == 
			"    center      cont      flux       eqw      core     gfwhm     lfwhm\n"):
			return True
		return False
	
	def is_spectra_head(self, line):
		if line[:3] in ('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 
			'Nov', 'Dec'):
			return True
		else:
			return False

	def get_num(self, line):
		start = line.find('[') + 1
		stop = start + 3
		return line[start:stop]

	def spectra(self):
		return self.spectradict.values()

	def id_lines(self):
		lines = self.lines.copy()
		for item in lines:
			lines.update({item: (lines[item] * (self.redshift + 1))})
		for spectrum in self.spectra():
			spectrum.id_lines(lines)

	def collate_lines(self):
		for spectrum in self.spectra():
			spectrum.collate_lines(self.lines)

	def calculate(self):
		for spectrum in self.spectra():
			spectrum.calculate()

	def correct_extinction(self):
		for spectrum in self.spectra():
			spectrum.correct_extinction()

	def output(self, fn):
		file = open(fn, 'w')
		spectra = self.spectra()
		spectra.sort()
		tsize = len(spectra[0].diagnostics)
		keys = self.lines.keys()
		keys.sort()
		diagnostics = spectra[0].diagnostics.keys()
		file.write('\\documentclass{article}\n')
		file.write('\\usepackage{rotating}\n')
		file.write('\\usepackage{booktabs}\n')
		file.write('\\begin{document}\n')
		self.make_table(spectra, keys[:6], file)
		self.make_table(spectra, keys[6:], file)
		self.make_table(spectra, diagnostics, file)
		file.write('\\end{document}\n')
		file.close()

	def make_table(self, spectra, keys, file):
		file.write('\\begin{sidewaystable}\n')
		file.write('\\begin{tabular}{ *{%s}{r}}\n' % (len(keys) + 1))
		file.write('\\toprule\n')
		file.write(' Number ')
		for item in keys:
			file.write('& %s' % item)
		file.write('\\\\\n')
		file.write('\\midrule\n')
		for item in spectra:
			if item.halpha.flux != 0:
				file.write(' %s ' % item.num)
				for line in keys:
					if type(item.__dict__[line]) in (float, str):
						file.write('& %s ' % scinot(item.__dict__[line]))
					else:
						file.write('& %s ' % scinot(item.__dict__[line].flux))
				file.write('\\\\\n')
		file.write('\\bottomrule\n')
		file.write('\\end{tabular}\n')
		file.write('\\end{sidewaystable}\n')
		


def scinot(value):
	value = str(value)
	if 'e' not in value:
		return value
	tmp = str(value).split('e')
	val, pow = tmp[0], tmp[1]
	if val[-3:] == '667':
		tmp = val[-2::-1]
		for i, item in enumerate(tmp):
			if item != '6':
				break
		val = val[:-i]
	elif val[-3:] == '333':
		tmp = val[::-1]
		for i, item in enumerate(tmp):
			if item != '3':
				break
		val = val[:-(i-1)]
	return 'e'.join((val, pow))
	

def main():
	os.chdir('../n3')
	image = ImageClass('ngc3169')
	image.add_logs()
	image.redshift = 0.004130
	image.id_lines()
	image.collate_lines()
	image.correct_extinction()
	image.calculate()
	image.output('tables/ngc3169.tex')
	image = ImageClass('ngc4725')
	image.add_logs()
	image.redshift = 0.004023
	image.id_lines()
	image.collate_lines()
	image.correct_extinction()
	image.calculate()
	image.output('tables/ngc4725.tex')
	

main()
