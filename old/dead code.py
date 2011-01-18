
def set_value(name, value_name, value):
	raw_data = get_raw_data(name)
	raw_data.update({value_name: value})
	write_raw_data(name, raw_data)

def get_value(name, value_name):
	raw_data = get_raw_data(name)
	return raw_data[value_name]

def print_size(name, list=''):
	"""I don't think this function is used anywhere"""
	data = get_data(name)
	if list == '':
		list = range(len(data))
	for i in list:
		print i, data[i]['size']

def load_astutil():
	"""Load the astutil package"""
	iraf.astutil(_doprint=0)

def reidentify(reference, images, **kwargs):
	load_onedspec()
	kwargs.setdefault('verbose', 'yes')
	kwargs.setdefault('interactive', 'no')
	kwargs.setdefault('shift', 'INDEF')
	kwargs.setdefault('search', 'INDEF')
	iraf.reidentify.unlearn()
	iraf.reidentify(reference=reference, images=images, **kwargs)

def reidentify_galaxy(name, reference):
	data = get_data(name)
	for i, item in enumerate(data):
		num = zerocount(i)
		reidentify(reference, '%s/%sc.1d.0001' % (name, num))

def sky_subtract_annealing(name, spectra, sky, lines):
	num = zerocount(spectra['number'])
	guess = guess_scaling(name, spectra, sky, lines)
	os.mkdir('%s/tmp/%s' % (name, num))
	# annealing
	#anneal_out = scipy.optimize.anneal(get_std_sky, guess, args=(name, num), lower=0, upper=20, T0=0.4)
	#return anneal_out[0]

def get_std_sky_alt(scale, name, num):
	scale = float(scale)
	sky = '%s/sky.1d' % name
	scaled_sky = '%s/tmp/%s/%s.sky' % (name, num, scale)
	in_fn = '%s/disp/%s.1d' % (name, num)
	out_fn = '%s/tmp/%s/%s.1d' % (name, num, scale)
	sarith(sky, '*', scale, scaled_sky)
	sarith(in_fn, '-', scaled_sky, out_fn)
	fits = pyfits.open('%s.fits' % out_fn)
	loc1 = get_wavelength_location(fits, 5600)
	loc2 = get_wavelength_location(fits, 7000)
	deviation = std(*fits[0].data[loc1:loc2])
	return deviation

def scale_spectra(input, scale, output):
	sarith(input, '/', scale, output)

def get_data_old(name):
	raw_data = get_raw_data(name)
	if 'data' not in raw_data:
		types = raw_data['types'][:]
		angles = get_angles(raw_data['coord'])
		sections, size = get_sections(raw_data['coord'])
		data = []
		for i, angle in enumerate(angles):
			data.append({'angle':angle, 'section':sections[i], 
				'size':size[i], 'type':types[i], 'number':i})
		write_data(name, data)
	else:
		data = raw_data['data']
	return data

def combine_sky_spectra(name, scale=False, **kwargs):
	data = get_data(name)
	list = []
	for i, item in enumerate(data):
		if item['type'] == 'NIGHTSKY':
			list.append(i)
	if scale == True:
		flist = []
		for spectra in list:
			scale = data[spectra]['size']
			num = zerocount(spectra)
			sarith('%s/disp/%s.1d' % (name, num), '/', scale, 
				'%s/sky/%s.scaled' % (name, num))
			flist.append('%s/sky/%s.scaled' % (name, num))
	else:
		flist = []
		for spectra in list:
			num = zerocount(spectra)
			flist.append('%s/disp/%s.1d' % (name, num))
	scombine(list_convert(flist), '%s/sky.1d' % name, **kwargs)

def set_BASE(base):
	"""Sets the value of the base directory"""
	global BASE
	BASE = base

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

		#self.diagnostics = {
		#	'r23': (lambda s: (s.OII.flux + s.OIII1.flux + s.OIII2.flux) / s.hbeta.flux), 
			#'a23': (lambda s: (s.OIII1.flux + s.OIII2.flux) / s.OII.flux),
			#'NII2 / halpha': (lambda s: s.NII2.flux / s.halpha.flux),
			#'OIII2 / NII2': (lambda s: s.OIII2.flux / s.NII2.flux),
			#'NII2 / OII': (lambda s: s.NII2.flux / s.OII.flux),
			#'OIII2 / OII': (lambda s: s.OIII2.flux / s.OII.flux),
			#'halpha / hbeta': (lambda s: s.halpha.flux / self.hbeta.flux),
			# E(B-V) is already calculated by the time this is used
		#	'E(B - V)': (lambda s: s.E),
			# halpha calibration given by Kennicutt 1998
		#	'SFR(M$_\odot$ / year)': (lambda s: 7.9 * 10 ** -42 * s.halpha.flux),
		#	'Radial Distance (kpc)': (lambda s: s.rdistance),
		#	'$12 + \log(O/H)$': lambda s: None
		}

def compare(gal1, gal2):
	spectra_a = gal1.spectra
	OH_a = [s.OH for s in spectra_a]
	rdist_a = [s.rdistance for s in spectra_a]
	r25_a = [dist / gal1.r25 for dist in rdist_a]
	spectra_b = gal2.spectra
	OH_b = [s.OH for s in spectra_b]
	rdist_b = [s.rdistance for s in spectra_b]
	r25_b = [dist / gal2.r25 for dist in rdist_b]
	i = get_graph_number()
	pylab.figure(figsize=(10,10), num=i)
	pylab.subplots_adjust(left=0.1)
	pylab.plot(r25_a, OH_a, 'o', label=gal1.name)
	pylab.plot(r25_b, OH_b, 'o', label=gal2.name)
	pylab.ylabel('$12 + \log(O/H)$')
	pylab.xlabel('Radial Distance to object divided by r$_{25}$')
	pylab.legend()
	pylab.savefig('tables/comparison.eps', format='eps')


	def fit_metal_sfr(self):
		# inital guess: flat and solar metallicity
		slope = div3lib.ParameterClass(0)
		intercept = div3lib.ParameterClass(8.6)
		def function(x):
			return (intercept() + slope() * x)
		
		x = [s.SFR for s in self.spectra]
		y = [s.OH for s in self.spectra]
		div3lib.remove_nan(x, y)
		x = numpy.array(x)
		y = numpy.array(y)
		fit = div3lib.fit(function, [slope, intercept], y, x)
		self.metal_sfr_fit = fit
		self.metal_sfr_grad = fit[0][0]
		return fit

def n6_initial():
	zero_flats('Mask.pl')
	init_galaxy('feige34', 'Mask.pl', 'Zero', 'Flat1')
	init_galaxy('feige66', 'Mask.pl', 'Zero', 'Flat2')
	init_galaxy('ngc2985', 'Mask.pl', 'Zero', 'Flat1')
	init_galaxy('ngc4725', 'Mask.pl', 'Zero', 'Flat2')

def n6_slices():
	#slice_galaxy('feige34', 'henear1', use='ngc2985')
	slice_galaxy('feige66', 'henear2', use='ngc4725')
	#slice_galaxy('ngc2985', 'henear1')
	slice_galaxy('ngc4725', 'henear2')

def n6_dispersion():
	#disp_galaxy('feige34', use='ngc2985')
	disp_galaxy('feige66', use='ngc4725')
	#disp_galaxy('ngc2985')
	disp_galaxy('ngc4725')

def n6_skies():
	lines = [5893, 5578, 6301, 6365]
	#skies('feige34', lines, obj=10)
	skies('feige66', lines, obj=18)
	#skies('ngc2985', lines)
	skies('ngc4725', lines)

def n6_calibrate():
	#calibration('ngc2985', 'feige34')
	calibration('ngc4725', 'feige66')

def n6():
	location = os.path.expanduser('~/iraf/work/n6')
	os.chdir(location)
	#n6_initial()
	#n6_slices()
	#then identify everything
	#n6_dispersion()
	#n6_skies()
	#then run standard and sensfunc manually
	#n6_calibrate()
	#now go measure line strengths with splot


def make_table(spectra, keys, lookup):
	string = ''
	string += '\\begin{tabular}{ *{%s}{c}}\n' % (len(keys) + 1)
	string += '\\toprule\n'
	string += ' Number '
	for item in keys:
		string += '& %s' % lookup[item]
	string += '\\\\\n'
	string += '\\midrule\n'
	for item in spectra:
		if item.halpha != 0:
			string += ' %s ' % item.id
			for key in keys:
				value = item.__dict__[key]
				if numpy.isnan(value):
					value = '. . .'
				else:
					value = '%.4g' % value
				string += '& %s ' % value
			string += '\\\\\n'
	string += '\\bottomrule\n'
	string += '\\end{tabular}\n'
	return string