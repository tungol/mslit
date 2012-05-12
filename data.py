import math
import yaml
from misc import avg

####################################################
## Functions for working with the metadata I have ##
####################################################

## Functions for low level reading, parsing, and writing ##


def get_raw_data(name):
    fn = 'input/%s-generated.yaml' % name
    with open(fn) as f:
        raw_data = yaml.load(f)
    return raw_data


def write_raw_data(name, raw_data):
    fn = 'input/%s-generated.yaml' % name
    with open(fn, 'w') as f:
        yaml.dump(raw_data, f)


def read_out_file(name):
    fn = 'input/%s.out' % name
    with open(fn) as f:
        raw_out = f.readlines()
    return raw_out


def get_pixel_sizes(name):
    fn = 'input/%s.yaml' % name
    with open(fn) as f:
        data = yaml.load(f.read())
    return data

## Functions for basic manipulation ##


def get_data(name):
    raw = get_raw_data(name)
    data = raw['data']
    return data


def get_groups(path):
    fn = '%s/input/groups.yaml' % path
    with open(fn) as f:
        groups = yaml.load(f.read())
    return groups


def init_data(name, use=None):
    if not use:
        use = name
    raw_out = read_out_file(use)
    data = parse_out_file(raw_out)
    pixel_sizes = get_pixel_sizes(use)
    real_start = float(data[0]['xlo'])
    real_end = float(data[-1]['xhi'])
    coord = get_coord(pixel_sizes, real_start, real_end, data)
    angles = get_angles(coord)
    sections, sizes = get_sections(coord)
    for i, angle in enumerate(angles):
        print i, sections[i]
        data[i].update({'angle': angle, 'section': sections[i],
            'size': sizes[i]})
    write_data(name, data)


def set_obj(name, obj):
    data = get_data(name)
    for i, item in enumerate(data):
        if i != obj:
            if item['type'] == 'HIIREGION':
                item['type'] = 'NIGHTSKY'
    write_data(name, data)


def write_data(name, data):
    try:
        raw_data = get_raw_data(name)
    except (ValueError, IOError):
        raw_data = {}
    raw_data.update({'data': data})
    write_raw_data(name, raw_data)

## Functions for calculations ##


def get_angles(raw_data):
    columns = raw_data.keys()
    list1 = raw_data[columns[0]]
    list2 = raw_data[columns[1]]
    run = float(columns[0]) - float(columns[1])
    angles = []
    for item1, item2 in zip(list1, list2):
        start1 = item1['start']
        end1 = item1['end']
        start2 = item2['start']
        end2 = item2['end']
        mid1 = avg(start1, end1)
        mid2 = avg(start2, end2)
        rise = mid1 - mid2
        slope = rise / run
        angles.append(math.degrees(math.atan(slope)))
    return angles


def get_coord(pixel_sizes, real_start, real_end, data):
    real_size = real_end - real_start
    coord = {}
    for pcol in pixel_sizes:
        
        def convert(real_value, pixel):
            real_value = float(real_value)
            pixel_start = float(pixel['start'])
            pixel_end = float(pixel['end'])
            pixel_size = pixel_end - pixel_start
            return (((real_value - real_start) *
                (pixel_size / real_size)) + pixel_start)
        
        coord.update({pcol['column']: []})
        for item in data:
            start = convert(item['xlo'], pcol)
            end = convert(item['xhi'], pcol)
            coord[pcol['column']].append({'start': start, 'end': end})
    return coord


def get_sections(raw_data):
    columns = raw_data.keys()
    list1 = raw_data[columns[0]]
    list2 = raw_data[columns[1]]
    sections = []
    size = []
    for i, (item1, item2) in enumerate(zip(list1, list2)):
        start1 = item1['start']
        end1 = item1['end']
        start2 = item2['start']
        end2 = item2['end']
        start = avg(start1, start2)
        end = avg(end1, end2)
        start -= 1.5
        end += 1.5
        if math.modf(start)[0] < 0.70:
            start = int(math.floor(start))
        else:
            start = int(math.ceil(start))
        if math.modf(end)[0] > 0.30:
            end = int(math.ceil(end))
        else:
            end = int(math.floor(end))
        size.append(end - start)
        sections.append('[1:2048,%s:%s]' % (start, end))
    return sections, size


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
