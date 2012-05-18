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

def make_tabular(group, lookup, extra, inner_command, outer_command):
    string = ['\\begin{tabular}{ *{%s}{c}}\n' % (len(lookup.keys()) + 1)]
    string += outer_command(group, lookup, extra, inner_command)
    string.append('\\end{tabular}\n')
    return ''.join(string)


def make_table(groups, lookup, name, command):
    string = ['\\toprule\n %s ' % name]
    string += ['& %s ' % lookup[item] for item in lookup.keys()]
    string.append('\\\\\n')
    for group in groups:
        string += command(group, lookup.keys())
    string.append('\\bottomrule\n')
    return string


def make_multitable(galaxies, lookup, (classes, titles), command):
    string = []
    for key in titles:
        v = dict([(header, {}) for header in classes[key]])
        for header, group in classes[key].items():
            for value in ('grad', 'metal'):
                values = [g.__dict__[value] for g in galaxies
                          if g.__dict__[key] in group]
                v[header].update({value: values})
        string += make_table((v,), lookup, titles[key], command)
    return string


def arrange_spectra(spectra, keys):
    string = ['\\midrule\n']
    for spectrum in spectra:
        string.append(' %s' % spectrum)
        if spectrum.corrected != True:
            string.append('$^a$')
        for item in keys:
            string.append(' & %s' % sigfigs_format(spectrum.__dict__[item], 2))
        string.append(' \\\\\n')
    return string


def arrange_galaxies(items, keys):
    string = ['\\midrule\n']
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
    return string


def arrange_group(data, keys):
    string = ['\\midrule\n']
    for header, group in data.items():
        string.append(' %s ' % header)
        for key in keys:
            if key[-4:] != '_std':
                values = group[key]
                remove_nan(values)
                a = sigfigs_format(avg(*values), 2)
                s = sigfigs_format(std(*values), 2)
                string.append('& %s & %s ' % (a, s))
        string.append('\\\\\n')
    return string


def make_data_table(galaxy, lookup):
    values = ['rdistance', 'OH', 'SFR']
    lookup = dict([(item, lookup[item]) for item in values])
    string = make_tabular((galaxy.spectra,), lookup, 'Number', arrange_spectra,
                          make_table)
    with open('tables/%s.tex' % galaxy.id, 'w') as f:
        f.write(string)


def make_flux_table(galaxy, lines, lookup):
    lines.sort()
    for item in lines[:]:
        unused = [numpy.isnan(spec.__dict__[item]) for spec in galaxy.spectra]
        if False not in unused:
            lines.remove(item)
    lookup = dict([(item, lookup[item]) for item in lines])
    string = make_tabular((galaxy.spectra,), lookup, 'Number', arrange_spectra,
                          make_table)
    with open('tables/%sflux.tex' % galaxy.id, 'w') as f:
        f.write(string)


def make_comparison_table(galaxies, other):
    lookup = {'grad': 'Gradient (dex/R$_{25}$)',
              'metal': 'Metalicity at 0.4R$_{25}$',
              'type': 'Hubble Type',
              'bar': 'Bar',
              'ring': 'Ring',
              'env': 'Environment',
              'regions': 'Number of Regions'}
    string = make_tabular((galaxies, other), lookup, 'Name', arrange_galaxies,
                          make_table)
    with open('tables/comparison.tex', 'w') as f:
        f.write(''.join(string))


def make_group_comparison_table(galaxies, other, classes):
    galaxies += other
    lookup = {'grad': 'Gradient (dex/R$_{25}$)',
              'grad_std': 'Standard Deviation',
              'metal': 'Metalicity at 0.4R$_{25}$',
              'metal_std': 'Standard Deviation'}
    titles = {'env': 'Environment', 'ring': 'Ring', 'bar': 'Bar',
              'type': 'Hubble Type'}

    string = make_tabular(galaxies, lookup, (classes, titles), arrange_group,
                           make_multitable)
    with open('tables/comparison2.tex', 'w') as f:
        f.write(''.join(string))
