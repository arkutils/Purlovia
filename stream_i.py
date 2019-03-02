#%% Setup
from interactive_utils import *
from stream import MemoryStream
from ue.asset import UAsset
import uasset
import loader

# AllDinosAchievementNameTags (89 entries), GlobalCuddleFoodList (15 entries), DinoEntries (journal? 147 entries)
# PlayerLevelEngramPointsSP, PlayerLevelEngramPoints,
# To checkout:
#   StatusValueModifierDescriptions (array of structs, unreadable)
#   StatusValueDefinitions (unsupported struct x 12)
#   StatusStateDefinitions (unsupported struct x 13...maybe not useful)
# ...are server and single-player default mults in here???
# assetname = r'Game\PrimalEarth\CoreBlueprints\COREMEDIA_PrimalGameData_BP'

# assetname = r'Game\PrimalEarth\CoreBlueprints\PrimalGlobalsBlueprint'
# assetname = r'Game\PrimalEarth\CoreBlueprints\BASE_PrimalGameData_BP' # master item/engram table
# assetname = r'Game\PrimalEarth\CoreBlueprints\PrimalGameData_BP' # post-processing effects
# assetname = r'Game\PrimalEarth\CoreBlueprints\PrimalPlayerDataBP' # not useful
# assetname = r'Game\PrimalEarth\CoreBlueprints\PrimalPlayerDataBP_Base' # player data - ascention
# assetname = r'Game\Aberration\CoreBlueprints\DinoCharacterStatusComponent_BP_MoleRat'

assetname = r'Game\PrimalEarth\Dinos\Dodo\Dodo_Character_BP'
# assetname = r'Game\PrimalEarth\Dinos\Dodo\Dodo_Character_BP_Aberrant'
# assetname = r'Game\Extinction\Dinos\Owl\Owl_Character_BP'
# assetname = r'Game\Extinction\Dinos\Owl\DinoSettings_Carnivore_Large_Owl'
# assetname = r'Game\Aberration\Dinos\MoleRat\MoleRat_Character_BP'

# assetname = r'Game\PrimalEarth\CoreBlueprints\Dino_Character_BP'
# assetname = r'Game\PrimalEarth\CoreBlueprints\Dino_Character_BP_Pack'
# assetname = r'Game\PrimalEarth\CoreBlueprints\DinoColorSet_Dodo'
# assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP'
# assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Dodo'
# assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_Argent'
# assetname = r'Game\PrimalEarth\CoreBlueprints\DinoCharacterStatusComponent_BP_FlyerRide'

filename = loader.convert_asset_name_to_path(assetname)

#%% Load and decode
mem = loader.load_raw_asset_from_file(filename)
stream = MemoryStream(mem, 0, len(mem))
asset = UAsset(stream)
print('Deserialising...')
asset.deserialise()
print('Linking...')
asset.link()
print('Decoding complete.')

#%% More display demos
# print('\nNames:')
# pprint(asset.names)
# print('\nImports:')
# pprint(asset.imports)
# print('\nExports:')
# pprint(asset.exports)

#%%
for i, export in enumerate(asset.exports):
    print(f'\nExport {i}:')
    pprint(export)
    pprint(export.properties)

#%% Try to discover inheritnce
# Find a Default__ export
# for export in asset.exports:
#     if not str(export.name).startswith('Default__'):
#         continue

#     pprint(export.name)
