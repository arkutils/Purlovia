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
# # Discover all species from the given mod, and convert/output them all
# mod_name = 'ClassicFlyers'
# # mod_name = 'SSFlyers' # doesn't work yet

# # TODO: We need to discover these details from mod.info and modmeta.info as they vary in format
# mod_number = loader.mods_names_to_numbers[mod_name]
# mod_top_level = f'/Game/Mods/{mod_number}/PrimalGameData_BP_{mod_name}'  # not constant!
# print(f'\nLoading {mod_name} ({mod_number}): {mod_top_level}\n')
# asset = loader[mod_top_level]
# species_data = ark.mod.load_all_species(asset)

#%% Convert/output just a single core species for comparison purposes
if 'mod_name' in vars(): del mod_name
load_species = (
    '/Game/PrimalEarth/Dinos/Argentavis/Argent_Character_BP',
    '/Game/PrimalEarth/Dinos/Allosaurus/Allo_Character_BP',
    '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP',
    '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP_Aberrant',
    '/Game/PrimalEarth/Dinos/Turtle/Turtle_Character_BP',
    '/Game/PrimalEarth/Dinos/Tusoteuthis/Tusoteuthis_Character_BP',
    '/Game/PrimalEarth/Dinos/Diplodocus/Diplodocus_Character_BP',

    '/Game/Aberration/Dinos/Crab/Crab_Character_BP',
    '/Game/Aberration/Dinos/LanternGoat/LanternGoat_Character_BP',
    '/Game/Aberration/Dinos/MoleRat/MoleRat_Character_BP',

    '/Game/ScorchedEarth/Dinos/Jerboa/Jerboa_Character_BP',
    '/Game/ScorchedEarth/Dinos/Phoenix/Phoenix_Character_BP',
    '/Game/ScorchedEarth/Dinos/Wyvern/Wyvern_Character_BP_Fire',

    '/Game/Extinction/Dinos/GasBag/GasBags_Character_BP',
    '/Game/Extinction/Dinos/IceJumper/IceJumper_Character_BP',
    '/Game/Extinction/Dinos/Owl/Owl_Character_BP',

    # '/Game/Mods/ClassicFlyers/Dinos/Argent/Argent_Character_BP',
)
print(f'\nLoading specific species...\n')
species_data = []
for pkgname in load_species:
    asset = loader[pkgname]
    props = ark.properties.gather_properties(asset)
    species_data.append((asset, props))

#%% Show which species we're processing
print(f'\nFound species:')
for a, v in species_data:
    print(f'{str(v["DescriptiveName"][0][-1]):>20}: {a.assetname}')

#%% Translate properties for export
values = dict()
values['ver'] = "!*!*! don't know where to get this !*!*!"
values['species'] = list()

for asset, props in species_data:
    species_values = values_for_species(asset, props)
    values['species'].append(species_values)

if 'mod_name' in vars():
    import os.path
    json_output = json.dumps(values)
    filename = os.path.join('output', f'{mod_name.lower()}.json')
    print(f'\nOutputting to: {filename}')
    with open(filename, 'w') as f:
        f.write(json_output)
else:
    # pprint(values)
    printjson(values)
