# Value generation interactive experiments

#%% Setup
from interactive_utils import *

import json
from collections import defaultdict

from ue.base import UEBase
from ue.asset import UAsset
from ue.loader import AssetLoader
from ue.stream import MemoryStream
from ue.utils import *
from ue.properties import *

import ark.mod
import ark.properties
from ark.export_asb_values import values_for_species

loader = AssetLoader()

#%% Gather properties from a mod
if 'mod_name' in vars(): del mod_name

if True:
    # Attempt to discover all species from the given mod, and convert/output them all
    mod_name = 'ClassicFlyers'
    # mod_name = 'SSFlyers' # doesn't work yet

    # TODO: We need to discover these details from mod.info and modmeta.info as they vary in format
    mod_number = loader.mods_names_to_numbers[mod_name]
    mod_top_level = f'/Game/Mods/{mod_number}/PrimalGameData_BP_{mod_name}'  # not constant!

    print(f'\nLoading {mod_name} ({mod_number}): {mod_top_level}\n')
    asset = loader[mod_top_level]
    species_data = ark.mod.load_all_species(asset)
else:
    # Convert/output just a single core species for comparison purposes
    core_creature = '/Game/PrimalEarth/Dinos/Argentavis/Argent_Character_BP'
    print(f'\nLoading single character: {core_creature}\n')
    asset = loader[core_creature]
    props = ark.properties.gather_properties(asset)
    species_data = [(asset, props)]

#%% Show what we got
print(f'\nFound species:')
pprint([v['DescriptiveName'][0][-1] for a, v in species_data])

# pprint([(a.assetname, v['DescriptiveName'][0][-1], dict(v['MaxStatusValues'])) for a, v in species_data])

#%% Translate properties for export
values = dict()
values['ver'] = "!*!*! don't know where to get this !*!*!"
values['species'] = list()

for asset, props in species_data:
    species_values = values_for_species(asset, props)
    values['species'].append(species_values)

# printjson(values)
if 'mod_name' in vars():
    import os.path
    json_output = json.dumps(values)
    filename = os.path.join('output', f'{mod_name.lower()}.json')
    print(f'\nOutputting to: {filename}')
    with open(filename, 'w') as f:
        f.write(json_output)
else:
    printjson(values)
