#!/usr/bin/env python
# encoding: utf-8

"""
data.py - contains functions for working with metadata about the observations

low level: get_pixel_sizes, get_raw_data, read_out_file, write_raw_data
"""

import math
import os.path
import yaml
from misc import avg, threshold_round

## Functions for low level reading, parsing, and writing ##


def get_angles(name):
    fn = 'input/%s-angles.yaml' % name
    with open(fn) as f:
        return yaml.load(f)


def get_groups():
    fn = 'input/groups.yaml'
    with open(fn) as f:
        return yaml.load(f.read())


def get_pixel_data(name):
    """Load the pixel location records from user-created YAML file."""
    fn = 'input/%s.yaml' % name
    with open(fn) as f:
        return yaml.load(f.read())


def get_sections(name):
    fn = 'input/%s-sections.yaml' % name
    with open(fn) as f:
        return yaml.load(f)


def get_sky_levels(name):
    fn = 'input/%s-sky.yaml' % name
    with open(fn) as f:
        return yaml.load(f)


def get_sizes(name):
    fn = 'input/%s-sizes.yaml' % name
    with open(fn) as f:
        return yaml.load(f)


def get_types(name):
    fn = 'input/%s-types.yaml' % name
    with open(fn) as f:
        return yaml.load(f)


def read_out_file(name):
    fn = 'input/%s.out' % name
    with open(fn) as f:
        return f.readlines()


def write_angles(name, angles):
    fn = 'input/%s-angles.yaml'
    with open(fn, 'w') as f:
        f.write(yaml.dump(angles))


def write_sections(name, sections):
    fn = 'input/%s-sections.yaml'
    with open(fn, 'w') as f:
        f.write(yaml.dump(sections))


def write_sky_levels(name, levels):
    fn = 'input/%s-sky.yaml'
    with open(fn, 'w') as f:
        f.write(yaml.dump(levels))


def write_sizes(name, sizes):
    fn = 'input/%s-sizes.yaml'
    with open(fn, 'w') as f:
        f.write(yaml.dump(sizes))


def write_types(name, types):
    fn = 'input/%s-types.yaml'
    with open(fn, 'w') as f:
        f.write(yaml.dump(types))


## Functions for basic manipulation ##


def init_data(name, use=None):
    if not use:
        use = name
    raw_out = read_out_file(use)
    data = parse_out_file(raw_out)
    pixel_data = get_pixel_data(use)
    real_sizes = [(float(i['xlo']), float(i['xhi'])) for i in data]
    types = [item['type'] for item in data]
    coord = get_pixel_coordinates(pixel_data, real_sizes)
    angles = calculate_angles(coord)
    sections, sizes = calculate_sections(coord)
    write_angles(name, angles)
    write_sections(name, sections)
    write_sizes(name, sizes)
    write_types(name, types)
    if not os.path.isfile('input/%s-sky.yaml'):
        write_sky_levels(name, [None] * len(types))


def get_object_spectra(name):
    groups = get_groups()
    for group in groups:
        if name in group.values():
            if group['star'] == name:
                return [group['star_num']]
            else:
                items = get_types(name)
                return [i for i, x in enumerate(items) if x == 'HIIREGION']


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


def get_pixel_coordinates(pixel_data, real_sizes):
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


def parse_out_file(raw_out):
    data = []
    header = raw_out.pop(0)
    headers = header.split()
    for i, item in enumerate(headers[:]):
        headers.remove(item)
        if item[0] != '(':
            headers.insert(i, item.lower())
    raw_out.pop(0)
    for i, item in enumerate(raw_out):
        values = item.split()
        item_dict = dict(zip(headers, values))
        item_dict.update({'number': i})
        item_dict.update({'type': item_dict['name']})
        data.append(item_dict)
    return data
