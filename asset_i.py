# Asset interactive experiments

#%% Setup
from interactive_utils import *
from ue.base import UEBase
from ue.asset import UAsset
from ue.loader import AssetLoader
from ue.stream import MemoryStream
from ue.utils import *
from ue.properties import *
from automate.ark import ArkSteamManager
import ark.mod
import ark.asset

arkman = ArkSteamManager(skipInstall=True)
loader = arkman.createLoader()

#%% Select asset
# AllDinosAchievementNameTags (89 entries), GlobalCuddleFoodList (15 entries), DinoEntries (journal? 147 entries)
# PlayerLevelEngramPointsSP, PlayerLevelEngramPoints,
# To checkout:
#   StatusValueModifierDescriptions (array of structs, unreadable)
#   StatusValueDefinitions (unsupported struct x 12)
#   StatusStateDefinitions (unsupported struct x 13...maybe not useful)
# ...are server and single-player default mults in here???
# assetname = '/Game/PrimalEarth/CoreBlueprints/COREMEDIA_PrimalGameData_BP'

# assetname = '/Game/PrimalEarth/CoreBlueprints/PrimalGlobalsBlueprint'  # !*!*! DECODE ERROR
# assetname = '/Game/PrimalEarth/CoreBlueprints/BASE_PrimalGameData_BP'  # master item/engram table
# assetname = '/Game/PrimalEarth/CoreBlueprints/PrimalGameData_BP'  # post-processing effects
# assetname = '/Game/PrimalEarth/CoreBlueprints/PrimalPlayerDataBP'  # not useful
# assetname = '/Game/PrimalEarth/CoreBlueprints/PrimalPlayerDataBP_Base'  # player data - ascention
# assetname = '/Game/Aberration/CoreBlueprints/DinoCharacterStatusComponent_BP_MoleRat'

# assetname = '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP'
# assetname = '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP_Aberrant'
# assetname = '/Game/Extinction/Dinos/Owl/Owl_Character_BP'
# assetname = '/Game/Extinction/Dinos/Owl/DinoSettings_Carnivore_Large_Owl'
# assetname = '/Game/Aberration/Dinos/MoleRat/MoleRat_Character_BP'
# assetname = '/Game/PrimalEarth/Dinos/Diplodocus/Diplodocus_Character_BP'
# assetname = '/Game/PrimalEarth/Dinos/Tusoteuthis/Tusoteuthis_Character_BP'
# assetname = '/Game/PrimalEarth/Dinos/Turtle/Turtle_Character_BP'
# assetname = '/Game/PrimalEarth/Dinos/Troodon/Troodon_Character_BP'

# assetname = '/Game/PrimalEarth/CoreBlueprints/Dino_Character_BP'
# assetname = '/Game/PrimalEarth/CoreBlueprints/Dino_Character_BP_Pack'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoColorSet_Dodo'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Dodo'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Argent'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Diplodocus'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Tuso'
# assetname = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_Turtle'

assetname = '/Game/Mods/ClassicFlyers/Dinos/Ptero/Ptero_Character_BP'
# assetname = '/Game/Mods/895711211/PrimalGameData_BP_ClassicFlyers'

# Failure case: fails to decode the only export (properties, invalid name)
# assetname = '/Game/Mods/ClassicFlyers/Dinos/AdminArgent/Assets/T_AdminArgent_Smaller_Colorize_d'

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
if asset.default_export:
    parent_pkg = ark.asset.findParentPackage(asset.default_export)
    print(parent_pkg)
else:
    print('-not found-')

#%% Try to discover sub-components
print('\nComponents:')
pprint(list(export.name for export in ark.asset.findComponentExports(asset)))
print('\nSub-components:')
pprint(list(export.name for export in ark.asset.findSubComponents(asset)))

#%% Mod info
print('\nMod adds species:')
pprint(ark.mod.get_species_from_mod(asset))

#%%
