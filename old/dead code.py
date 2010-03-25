
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