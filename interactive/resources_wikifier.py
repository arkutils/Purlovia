# flake8: noqa

#%% Setup

from interactive_utils import *  # pylint: disable=wrong-import-order

import csv
import json
from collections import defaultdict

#%% Main
map = 'Valguero'
a = set()

j = defaultdict(list)

with open('output/data/' + map + '.csv', 'rt') as fp:
    with open('/tmp/resources.wiki', 'wt') as fp2:
        for line in fp.read().split('\n'):
            line = line.strip()

            if line == 'ResourceType,Lat,Long,Z,Cave?':
                continue

            if not line:
                continue

            type, lat, long, _, cave = line.split(',')
            lat, long = (float(lat), float(long))
            lat, long = (round(lat, 1), round(long, 1))
            cave = True if cave == '1' else False

            if cave:
                type += ' cave'

            if (lat, long, type) in a:
                continue
            a.add((lat, long, type))

            fp2.write(f'| {lat}, {long}, {type}\n')
            j[type].append((lat, long))

with open('/tmp/resources.json', 'wt') as fp:
    json.dump(j, fp, separators=(',', ':'))
