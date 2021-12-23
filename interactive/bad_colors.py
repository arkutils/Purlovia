# flake8: noqa
# Look for bad colour names

#%% Setup
from interactive_utils import *  # pylint: disable=wrong-import-order

import json

#%% Load values JSON
with open('output/data/asb/values.json', 'rt', encoding='utf-8') as f:
    values = json.load(f)

species = values['species']

dyeNames = set(name for name, _ in values['dyeDefinitions'])
colorNames = set(name for name, _ in values['colorDefinitions'])
names = colorNames | dyeNames


#%% Functions
def _per_species(data, names):
    for region in data.get('colors', ()):
        if not region: continue
        bad = set(region.get('colors', ())) - names
        if bad: yield (region.get('name', '-'), list(bad))


def find_bad_colors(species, names):
    for data in species:
        bad_regions = list(_per_species(data, names))
        if bad_regions: yield dict(name=data['name'], bp=data['blueprintPath'], regions=bad_regions)


#%% Results
for v in find_bad_colors(species, names):
    print()
    print(f'{v["name"]} ({v["bp"].split(".")[0]})')
    for n, bad in v['regions']:
        print(f'  {n}: {", ".join(bad)}')
