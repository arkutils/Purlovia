#%% Setup
from interactive_utils import *
from ue.base import UEBase
from ue.asset import UAsset
from ue.loader import AssetLoader

# AllDinosAchievementNameTags (89 entries), GlobalCuddleFoodList (15 entries), DinoEntries (journal? 147 entries)
# PlayerLevelEngramPointsSP, PlayerLevelEngramPoints,
# To checkout:
#   StatusValueModifierDescriptions (array of structs, unreadable)
#   StatusValueDefinitions (unsupported struct x 12)
#   StatusStateDefinitions (unsupported struct x 13...maybe not useful)
# ...are server and single-player default mults in here???
# assetname = r'Game/PrimalEarth/CoreBlueprints/COREMEDIA_PrimalGameData_BP'

# assetname = r'Game/PrimalEarth/CoreBlueprints/PrimalGlobalsBlueprint'
# assetname = r'Game/PrimalEarth/CoreBlueprints/BASE_PrimalGameData_BP' # master item/engram table
# assetname = r'Game/PrimalEarth/CoreBlueprints/PrimalGameData_BP' # post-processing effects
# assetname = r'Game/PrimalEarth/CoreBlueprints/PrimalPlayerDataBP' # not useful
# assetname = r'Game/PrimalEarth/CoreBlueprints/PrimalPlayerDataBP_Base' # player data - ascention
# assetname = r'Game/Aberration/CoreBlueprints/DinoCharacterStatusComponent_BP_MoleRat'

# assetname = r'Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP'
# assetname = r'Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP_Aberrant'
# assetname = r'Game/Extinction/Dinos/Owl/Owl_Character_BP'
# assetname = r'Game/Extinction/Dinos/Owl/DinoSettings_Carnivore_Large_Owl'
# assetname = r'Game/Aberration/Dinos/MoleRat/MoleRat_Character_BP'
assetname = r'Game/PrimalEarth/Dinos/Diplodocus/Diplodocus_Character_BP'
# assetname = r'Game/PrimalEarth/Dinos/Tusoteuthis/Tusoteuthis_Character_BP'
# assetname = r'Game/PrimalEarth/Dinos/Turtle/Turtle_Character_BP'

# assetname = r'Game/PrimalEarth/CoreBlueprints/Dino_Character_BP'
# assetname = r'Game/PrimalEarth/CoreBlueprints/Dino_Character_BP_Pack'
# assetname = r'Game/PrimalEarth/CoreBlueprints/DinoColorSet_Dodo'
# assetname = r'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP'
# assetname = r'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Dodo'
# assetname = r'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Argent'
# assetname = r'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'
# assetname = r'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Diplodocus'
# assetname = r'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Tuso'
# assetname = r'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Turtle'

# assetname = r'Game/ClassicFlyers/Dinos/Ptero/Ptreo_Character_BP'

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
