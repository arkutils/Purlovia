# Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP
# Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Argent
# Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Dodo
# Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Rex
# Game\Extinction\CoreBlueprints\DinoCharacterStatusComponent_BP_Gacha
# Game\Extinction\CoreBlueprints\DinoCharacterStatusComponent_BP_Owl

# Game\PrimalEarth\Dinos\Argentavis\Argent_Character_BP
# Game\PrimalEarth\Dinos\Dodo\Dodo_Character_BP
# Game\PrimalEarth\Dinos\Dodo\Dodo_Character_BP_Aberrant
# Game\PrimalEarth\Dinos\Rex\Rex_Character_BP
# Game\Extinction\Dinos\Gacha\Gacha_Character_BP
# Game\Extinction\Dinos\Owl\Owl_Character_BP

#%% Imports
import os, glob
from pprint import pprint
import uasset
uasset.set_asset_path(r'.')


#%% Load base properties
base = uasset.load_and_parse('Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP')
# print('\Base properties:')
# pprint(base.props)

#%% Load species properties
species = uasset.load_and_parse('Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Dodo')
print('\nSpecies properties:')
pprint(species.props)

#%% Try merge species properties into base ones
combined_props = uasset.merge_properties(base, species)
print('\nCombined properties:')
pprint(combined_props, width=250)


#%% All species
basepath = r'K:\SteamLibrary\steamapps\common\ARK\ShooterGame'
for mod in ('PrimalEarth', 'Extinction'):
    path = os.path.join(basepath, 'Content', mod, 'CoreBlueprints')
    for filename in glob.iglob(os.path.join(path, 'DinoCharacterStatusComponent_BP_*')):
        speciesname = os.path.basename(filename.split(os.sep)[-1])[32:-7]
        asset = uasset.load_and_parse_file(filename)
        print(f'\n{speciesname}:')
        pprint(asset.props, width=250)
        print()
