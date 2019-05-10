# Value generation interactive experiments

#%% Setup
from interactive_utils import *

import re
import json
import os.path
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from deepdiff import DeepDiff

from ue.base import UEBase
from ue.asset import UAsset
from ue.loader import AssetLoader
from ue.stream import MemoryStream
from ue.utils import *
from ue.properties import *

import ark.mod
import ark.properties
from ark.export_asb_values import values_for_species
from automate.ark import ArkSteamManager, readModData

arkman = ArkSteamManager('./livedata', skipInstall=True)
loader = arkman.createLoader()

version_string = None

#%% Helpers
replace_name = lambda match: f'{species_names[int(match.group(1))]}'
replace_stat = lambda match: f'stat.{stat_names[int(match.group(1))]}.{stat_fields[int(match.group(2))]}'

SPECIES_REGEX = re.compile(r"root\['species'\]\[(\d+)\]")
STAT_REGEX = re.compile(r"statsRaw\[(\d+)\]\[(\d+)\]")
JOIN_LINES_REGEX = re.compile(r"(?:\n\t+)?(?<=\t)([\d.-]+,?)(?:\n\t+)?")


def clean_diff_output(diff):
    diff = SPECIES_REGEX.sub(replace_name, diff)
    diff = re.sub(r"\['(.*?)'\]", r'.\1', diff)
    # diff = STAT_REGEX.sub(replace_stat, diff)
    # diff = re.sub(r"\"(.*?)\":", r'\1:', diff)
    # diff = re.sub(r"\{'new_value': (.*?), 'old_value': (.*?)\}", r'\2 -> \1', diff)
    return diff


def format_json(data, pretty=False):
    json_string = json.dumps(data, indent=('\t' if pretty else None))
    if pretty:
        json_string = re.sub(JOIN_LINES_REGEX, r" \1", json_string)
        json_string = re.sub(r'(\d)\]', r'\1 ]', json_string)
    return json_string


def save_as_json(data, filename, pretty=False):
    print(f'Outputting to: {filename}')
    json_string = format_json(data, pretty)
    with open(filename, 'w') as f:
        f.write(json_string)


#%% CHOOSE ONE: Gather properties from a mod and brute-force the list of species
# # Discover all species from the given mod, and convert/output them all
# mod_name = 'ClassicFlyers'
# # mod_name = 'Primal_Fear'
# # mod_name = 'SSFlyer'
# # mod_name = 'Gaia'
# # mod_name = 'AE'
# mod_number = loader.modresolver.get_id_from_name(mod_name)
# print(f'\nLoading {mod_name} ({mod_number})\n')
# species_data = []
# all_assetnames = loader.find_assetnames(r'.*(_Character|Character_).*BP.*',
#                                         f'/Game/Mods/{mod_name}',
#                                         exclude=r'.*(_Base|Base_).*')
# for assetname in all_assetnames:
#     asset = loader[assetname]
#     props = ark.mod.gather_properties(asset)
#     species_data.append((asset, props))

#%% CHOOSE ONE: Gather properties from a mod and try to discover the list of species from spawn regions
# # Discover all species from the given mod, and convert/output them all
# mod_name = 'ClassicFlyers'  # Primal_Fear SSFlyers Gaia AE
# modid = loader.modresolver.get_id_from_name(mod_name)
# mod_data = readModData(loader.asset_path, modid)
# asset = loader[mod_data['package']]
# species_data = ark.mod.load_all_species(asset)

# %% CHOOSE ONE: Convert/output specific species for comparison purposes
# if 'mod_name' in vars(): del mod_name
# load_species = (
#     # '/Game/PrimalEarth/Dinos/Argentavis/Argent_Character_BP',
#     # '/Game/PrimalEarth/Dinos/Allosaurus/Allo_Character_BP',
#     # '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP',
#     # '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP_Aberrant',
#     # '/Game/PrimalEarth/Dinos/Turtle/Turtle_Character_BP',
#     # '/Game/PrimalEarth/Dinos/Tusoteuthis/Tusoteuthis_Character_BP',
#     # '/Game/PrimalEarth/Dinos/Diplodocus/Diplodocus_Character_BP',
#     # '/Game/Aberration/Dinos/Crab/Crab_Character_BP',
#     # '/Game/Aberration/Dinos/LanternGoat/LanternGoat_Character_BP',
#     # '/Game/Aberration/Dinos/MoleRat/MoleRat_Character_BP',
#     # '/Game/ScorchedEarth/Dinos/Jerboa/Jerboa_Character_BP',
#     # '/Game/ScorchedEarth/Dinos/Phoenix/Phoenix_Character_BP',
#     # '/Game/ScorchedEarth/Dinos/Wyvern/Wyvern_Character_BP_Fire',
#     # '/Game/Extinction/Dinos/GasBag/GasBags_Character_BP',
#     # '/Game/Extinction/Dinos/IceJumper/IceJumper_Character_BP',
#     # '/Game/Extinction/Dinos/Owl/Owl_Character_BP',
#     # '/Game/PrimalEarth/Dinos/Quetzalcoatlus/BionicQuetz_Character_BP',
#     # '/Game/PrimalEarth/Dinos/Thylacoleo/Thylacoleo_Character_BP',
#     # '/Game/PrimalEarth/Dinos/Quetzalcoatlus/Quetz_Character_BP',
#     # '/Game/PrimalEarth/Dinos/Griffin/Griffin_Character_BP',
#     '/Game/PrimalEarth/Dinos/Compy/Compy_Character_BP',
#     '/Game/PrimalEarth/Dinos/BoaFrill/BoaFrill_Character_BP',
#     '/Game/PrimalEarth/Dinos/BoaFrill/BoaFrill_Character_BP_Aberrant',
#     '/Game/PrimalEarth/Dinos/Troodon/Troodon_Character_BP',
#     '/Game/ScorchedEarth/Dinos/Wyvern/Wyvern_Character_BP_ZombieFire',
#     '/Game/Extinction/Dinos/Gacha/Gacha_Character_BP',

#     # '/Game/Mods/ClassicFlyers/Dinos/Argent/Argent_Character_BP',
# )
# print(f'\nDecoding specific species...\n')
# species_data = []
# for pkgname in load_species:
#     asset = loader[pkgname]
#     props = ark.properties.gather_properties(asset)
#     species_data.append((asset, props))

#%% CHOOSE ONE: Gather species list from existing ASB values.json
if 'mod_name' in vars(): del mod_name
value_json = json.load(open(os.path.join('asb_json', 'values.json')))
load_species = [species['blueprintPath'].split('.')[0] for species in value_json['species']]
version_string = f'{arkman.ensureGameUpdated(skipInstall=True)}.{int(datetime.utcnow().timestamp())}'
print(f'\nDecoding all values.json species...\n')
species_data = []
for pkgname in load_species:
    asset = loader[pkgname]
    props = ark.properties.gather_properties(asset)
    species_data.append((asset, props))

#%% Gather expected resutls from original ASB values files
if 'mod_name' in vars():
    asb_values_filename = mod_name.lower() + ".json"
else:
    asb_values_filename = "values.json"
print(f"\nReading expected data from: {asb_values_filename}")
expected_values_json = json.load(open(os.path.join('asb_json', asb_values_filename)))
expected_values = dict()
expected_values['ver'] = expected_values_json['ver']
expected_values['species'] = list()
expected_species_data = dict((species['blueprintPath'].split('.')[0], species) for species in expected_values_json['species'])
for v in expected_species_data.values():
    if 'colors' in v: del v['colors']
    if 'taming' in v: del v['taming']
    if 'immobilizedBy' in v: del v['immobilizedBy']
    if 'boneDamageAdjusters' in v: del v['boneDamageAdjusters']

#%% Show which species we're processing
print(f'\nFound species:')
species_names = []
for i, (a, v) in enumerate(species_data):
    name = str(v["DescriptiveName"][0][-1])
    species_names.append(name.replace(' ', ''))
    print(f'{i:>3} {name:>20}: {a.assetname}')

    # Record the expected data for this species
    try:
        expected_values['species'].append(expected_species_data[a.assetname])
    except:
        # print(f'ASB data not found for species: {name} ({a.assetname})')
        pass

#%% Translate properties for export
values = dict()
values['ver'] = version_string or datetime.utcnow().isoformat()
values['species'] = list()

all_props = 'mod_name' in vars()

for asset, props in species_data:
    species_values = values_for_species(asset, props, all=all_props, fullStats=True)
    values['species'].append(species_values)

#%% Show diff from ASB expected values
# stat_names = ('health', 'stam', 'oxy', 'food', 'weight', 'dmg', 'speed', 'torpor')
# stat_fields = ('B', 'Iw', 'Id', 'Ta', 'Tm')

# print(f'\nDifferences:')
# diff = DeepDiff(expected_values, values, ignore_numeric_type_changes=True, exclude_paths={"root['ver']"}, significant_digits=2)
# diff = pretty(diff, max_width=130)
# diff = clean_diff_output(diff)
# print(diff)
# # pprint(diff)

#%% Write output
if 'mod_name' in vars():
    filename = Path('.') / 'output' / f'{mod_name.lower()}.json'
    save_as_json(values, filename, pretty=True)
else:
    # pprint(values)
    # printjson(values)
    filename = Path('.') / 'output' / 'values.json'
    save_as_json(values, filename, pretty=True)

#%% Example diffing two assets
# def prep_props_for(assetname):
#     asset = loader[assetname]
#     merged_props = ark.properties.gather_properties(asset)
#     simplified = ark.properties.flatten_to_strings(merged_props)
#     return simplified

# a = prep_props_for('Game/PrimalEarth/Dinos/Beaver/Beaver_Character_BP')
# b = prep_props_for('Game/PrimalEarth/Dinos/Turtle/Turtle_Character_BP')
# pprint(DeepDiff(a, b))

# %% Check for overlaps between Character and DCSC properties
# print('\nChecking for overlapping properties:')
# for asset, props in species_data:
#     assetname = asset.assetname.split('/')[-1]
#     for name, indexed in props.items():
#         # print(name, end='')
#         for i, values in indexed.items():
#             if not isinstance(values, (StringProperty, IntProperty, BoolProperty, FloatProperty)):
#                 continue
#             typename = None
#             for v in values:
#                 name = v.asset.assetname.split('/')[-1]
#                 if 'StatusComponent' in name:
#                     name = 'DCSC'
#                 elif '_Character_' in name:
#                     name = 'Chr'

#                 if typename and name != typename:
#                     print(f'{assetname}.{name}[{i}] = {pretty(values)}')

#                 typename = typename or name
# print('Done')
