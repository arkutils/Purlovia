#%% Setup
from interactive_utils import *
from ue.base import UEBase
from ue.asset import UAsset
from ue.loader import AssetLoader
from ue.stream import MemoryStream
from ue.properties import *

# AllDinosAchievementNameTags (89 entries), GlobalCuddleFoodList (15 entries), DinoEntries (journal? 147 entries)
# PlayerLevelEngramPointsSP, PlayerLevelEngramPoints,
# To checkout:
#   StatusValueModifierDescriptions (array of structs, unreadable)
#   StatusValueDefinitions (unsupported struct x 12)
#   StatusStateDefinitions (unsupported struct x 13...maybe not useful)
# ...are server and single-player default mults in here???
assetname = 'Game/PrimalEarth/CoreBlueprints/COREMEDIA_PrimalGameData_BP'

# assetname = 'Game/PrimalEarth/CoreBlueprints/PrimalGlobalsBlueprint'  # !*!*! DECODE ERROR
# assetname = 'Game/PrimalEarth/CoreBlueprints/BASE_PrimalGameData_BP'  # master item/engram table
# assetname = 'Game/PrimalEarth/CoreBlueprints/PrimalGameData_BP'  # post-processing effects
# assetname = 'Game/PrimalEarth/CoreBlueprints/PrimalPlayerDataBP'  # not useful
# assetname = 'Game/PrimalEarth/CoreBlueprints/PrimalPlayerDataBP_Base'  # player data - ascention
# assetname = 'Game/Aberration/CoreBlueprints/DinoCharacterStatusComponent_BP_MoleRat'

# assetname = 'Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP'
# assetname = 'Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP_Aberrant'
# assetname = 'Game/Extinction/Dinos/Owl/Owl_Character_BP'
# assetname = 'Game/Extinction/Dinos/Owl/DinoSettings_Carnivore_Large_Owl'
# assetname = 'Game/Aberration/Dinos/MoleRat/MoleRat_Character_BP'
# assetname = 'Game/PrimalEarth/Dinos/Diplodocus/Diplodocus_Character_BP'
# assetname = 'Game/PrimalEarth/Dinos/Tusoteuthis/Tusoteuthis_Character_BP'
# assetname = 'Game/PrimalEarth/Dinos/Turtle/Turtle_Character_BP'

# assetname = 'Game/PrimalEarth/CoreBlueprints/Dino_Character_BP'
# assetname = 'Game/PrimalEarth/CoreBlueprints/Dino_Character_BP_Pack'
# assetname = 'Game/PrimalEarth/CoreBlueprints/DinoColorSet_Dodo'
# assetname = 'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP'
# assetname = 'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Dodo'
# assetname = 'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Argent'
# assetname = 'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'
# assetname = 'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Diplodocus'
# assetname = 'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Tuso'
# assetname = 'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Turtle'

# assetname = 'Game/Mods/ClassicFlyers/Dinos/Ptero/Ptero_Character_BP'
# assetname = 'Game/Mods/895711211/PrimalGameData_BP_ClassicFlyers'

loader = AssetLoader()
# filename = loader.convert_asset_name_to_path(assetname)
asset = loader[assetname]
print('Decoding complete.')

#%% More display demos
# print('\nNames:')
# pprint(asset.names)
# print('\nImports:')
# pprint(asset.imports)
# print('\nExports:')
# pprint(asset.exports)

#%%
# for i, export in enumerate(asset.exports):
#     print(f'\nExport {i}:')
#     pprint(export)
#     pprint(export.properties)

#%% Try to discover inheritance
print('\nParent package:')
default_export = asset.findDefaultExport()
parent_pkg = asset.findParentPackageForExport(default_export)
print(parent_pkg)

#%% Try to discover sub-components
print('\nSub-component packages:')
pprint(list(asset.findSubComponents()))

#%%
print('\nMod AdditionalDinoEntries:')
new_entries = next((prop.value for prop in default_export.properties if str(prop.header.name) == 'AdditionalDinoEntries'), None)
if not new_entries:
    print('-not found-')
else:
    for entry in new_entries.values:
        print(f'    {str(entry.value.value.outer_index.value.name)}')

print('\nMod Remap_NPC:')
remap_entries = next((prop.value for prop in default_export.properties if str(prop.header.name) == 'Remap_NPC'), None)
pprint(remap_entries)
