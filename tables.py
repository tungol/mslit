import numpy
from mslit.misc import remove_nan, avg, std


def sigfigs_format(x, n):
    if numpy.isnan(x):
        return '. . .'
    if n < 1:
        raise ValueError("number of significant digits must be >= 1")
    string = '%.*e' % (n-1, x)
    value, exponent = string.split('e')
    exponent = int(exponent)
    if exponent == 0:
        return value
    else:
        return '$%s \\times 10^{%s}$' % (value, exponent)


## Make some tables ##

def make_table(groups, lookup, name, command):
    string = ['\\begin{tabular}{ *{%s}{c}}\n' % (len(lookup.keys()) + 1)]
    string.append('\\toprule\n %s ' % name)
    string += ['& %s ' % lookup[item] for item in lookup.keys()]
    string.append('\\\\\n')
    for group in groups:
        command(group, string, lookup.keys())
    string.append('\\bottomrule\n\\end{tabular}\n')
    return ''.join(string)


def arrange_spectra(spectra, string, keys):
    string.append('\\midrule\n')
    for spectrum in spectra:
        print repr(spectrum)
        string.append(' %s' % spectrum)
        if spectrum.corrected != True:
            string.append('$^a$')
        for item in keys:
            string.append(' & %s' % sigfigs_format(spectrum.__dict__[item], 2))
        string.append(' \\\\\n')


def make_data_table(galaxy):
    values = ['rdistance', 'OH', 'SFR']
    lookup = dict([(item, galaxy.lookup[item]) for item in values])
    string = make_table(galaxy.spectra, lookup, 'Number', arrange_spectra)
    with open('tables/%s.tex' % galaxy.id, 'w') as f:
        f.write(string)


def make_flux_table(galaxy):
    lines = galaxy.lines.keys()
    lines.sort()
    for item in lines[:]:
        unused = [numpy.isnan(spec.__dict__[item]) for spec in galaxy.spectra]
        if False not in unused:
            lines.remove(item)
    lookup = dict([(item, galaxy.lookup[item]) for item in lines])
    string = make_table(galaxy.spectra, lookup, 'Number', arrange_spectra)
    with open('tables/%sflux.tex' % galaxy.id, 'w') as f:
        f.write(string)


def compare_table(galaxies, other, groups, key, title):
    lookup = {'grad': 'Gradient (dex/R$_{25}$)',
              'metal': 'Metalicity at 0.4R$_{25}$'}
    galaxies += other
    string = []
    string.append(' %s ' % title)
    for value in lookup.keys():
        string.append('& %s & Standard Deviation ' % lookup[value])
    string.append('\\\\\n\\midrule\n')
    for header, group in groups.items():
        string.append(' %s ' % header)
        for value in lookup.keys():
            values = [g.__dict__[value] for g in galaxies
                      if g.__dict__[key] in group]
            remove_nan(values)
            a = sigfigs_format(avg(*values), 2)
            s = sigfigs_format(std(*values), 2)
            string.append('& %s & %s ' % (a, s))
        string.append('\\\\\n')
    with open('tables/%s_comparison.tex' % key, 'w') as f:
        f.write(''.join(string))


def arrange_galaxies(items, string, keys):
    string.append('\\midrule\n')
    for item in items:
        string.append(' %s ' % item.name)
        for key in keys:
            value = item.__dict__[key]
            if type(value) == str or key == 'regions':
                value = str(value)
            else:
                value = sigfigs_format(value, 3)
            string.append('& %s ' % value)
        string.append('\\\\\n')


def make_comparison_table(galaxies, other):
    lookup = {'grad': 'Gradient (dex/R$_{25}$)',
              'metal': 'Metalicity at 0.4R$_{25}$',
              'type': 'Hubble Type',
              'bar': 'Bar',
              'ring': 'Ring',
              'env': 'Environment',
              'regions': 'Number of Regions'}
    string = make_table((galaxies, other), lookup, 'Name', arrange_galaxies)
    with open('tables/comparison.tex', 'w') as f:
        f.write(string)
