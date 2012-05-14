#!/usr/bin/env python
# encoding: utf-8

"""
data.py - contains functions for working with metadata about the observations

low level: get, get_groups, get_mslit_data, write
manipulation functions: get_group, get_object_spectra, get_sky_spectra
                        init_data
calculation functions: calculate_angles, calculate_sections,
                       calculate_pixel_coordinates
"""

import math
import os.path
import yaml
from .misc import avg, threshold_round

## Functions for low level reading and writing ##


def get(name, suffix):
    """Get the contents of a previously saved metadata file."""
    fn = 'input/%s-%s.yaml' % (name, suffix)
    with open(fn) as f:
        return yaml.load(f)


def get_groups():
    """Get the contents of the groups file."""
    fn = 'input/groups.yaml'
    with open(fn) as f:
        return yaml.load(f.read())


def get_mslit_data(name):
    """Get the important data from MSLIT's output."""
    fn = 'input/%s.out' % name
    with open(fn) as f:
        raw = f.readlines()
    # 0 is headers, 1 is a blank line, 2+ is data
    # if a header field begins with a (, it's not really a header field
    headers = [h for h in raw[0].split() if h[0] != '(']
    data = []
    for line in raw[2:]:
        pairs = dict(zip(headers, line.split()))
        data.append({'type': pairs['NAME'], 'xlo': pairs['XLO'],
                     'xhi': pairs['XHI']})
    return data


def write(name, suffix, data):
    """Write some metadata to disk."""
    fn = 'input/%s-%s.yaml' % (name, suffix)
    with open(fn, 'w') as f:
        f.write(yaml.dump(data))


## Functions for basic manipulation ##

def get_group(name):
    """Return the group data for a given galaxy or star."""
    groups = get_groups()
    for group in groups:
        if name in group.values():
            return group


def get_object_spectra(name):
    """Return the indexes of the spectra that contain objects."""
    group = get_group(name)
    if name == group['star']:
        return [group['star_num']]
    else:
        items = get(name, 'types')
        return [i for i, x in enumerate(items) if x == 'HIIREGION']


def get_sky_spectra(name):
    """Return the indexes of the spectra that contain sky."""
    group = get_group(name)
    sky_types = ['NIGHTSKY']
    items = get(name, 'types')
    # we can assume that slits marked HIIREGION for calibration star
    # observations also contain sky, but make sure not to include the star.
    if name == group['star']:
        items.pop(group['star_num'])
        sky_types.append('HIIREGION')
    sky_list = [i for i, x in enumerate(items) if x in sky_types]
    return sky_list


def init_data(name):
    """Generate extra data files from name.out and name-pixel.yaml."""
    group = get_group(name)
    use = group['galaxy']
    data = get_mslit_data(use)
    pixel_data = get(use, 'pixel')
    real_sizes = [(float(i['xlo']), float(i['xhi'])) for i in data]
    types = [item['type'] for item in data]
    coord = calculate_pixel_coordinates(pixel_data, real_sizes)
    angles = calculate_angles(coord)
    sections, sizes = calculate_sections(coord)
    write(name, 'angles', angles)
    write(name, 'sections', sections)
    write(name, 'sizes', sizes)
    write(name, 'types', types)
    if not os.path.isfile('input/%s-sky.yaml' % name):
        write(name, 'sky', [None] * len(types))


## Functions for calculations ##


def calculate_angles(data):
    """Calculate the angles described by a set of pixel coordinates."""
    (column1, column2) = data.keys()
    run = column1 - column2
    angles = []
    for item1, item2 in zip(*data.values()):
        mid1 = avg(item1['start'], item1['end'])
        mid2 = avg(item2['start'], item2['end'])
        rise = mid1 - mid2
        slope = rise / run
        angles.append(math.degrees(math.atan(slope)))
    return angles


def calculate_sections(data):
    """Calculate slicing sections for a set of pixel coordinates."""
    sections = []
    size = []
    fudge_factor = 1.5
    rounding_threshold = 0.70
    for (item1, item2) in zip(*data.values()):
        start = avg(item1['start'], item2['start']) - fudge_factor
        end = avg(item1['end'], item2['end']) + fudge_factor
        start = threshold_round(start, rounding_threshold)
        end = threshold_round(end, 1 - rounding_threshold)
        size.append(end - start)
        sections.append('[1:2048,%s:%s]' % (start, end))
    return sections, size


def calculate_pixel_coordinates(pixel_data, real_sizes):
    """Covert physical coordinates from MSLIT .out files into pixel
       coordinates."""
    real_start = real_sizes[0][0]
    real_end = real_sizes[-1][1]
    real_size = real_end - real_start
    coord = {}
    for pixel in pixel_data:
        pixel_size = pixel['end'] - pixel['start']
        ratio = pixel_size / real_size
        values = []
        for item in real_sizes:
            start = ratio * (item[0] - real_start) + pixel['start']
            end = ratio * (item[1] - real_start) + pixel['start']
            values.append({'start': start, 'end': end})
        coord.update({pixel['column']: values})
    return coord
