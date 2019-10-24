# Interactive testing of hierarchy utilities

#%% Setup

import ue.hierarchy
from automate.ark import ArkSteamManager
from ue.asset import UAsset

arkman = ArkSteamManager()
loader = arkman.getLoader()
ue.hierarchy.tree.clear()
ue.hierarchy.load_internal_hierarchy('config/hierarchy.yaml')

#%% Creation

dodo_chr: UAsset = loader['Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP']
map_asset: UAsset = loader['Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP']
assert dodo_chr.default_class

#%% Discover

ue.hierarchy.explore_path('/Game/PrimalEarth/Dinos/Dodo', loader, set())

#%% Go

list(ue.hierarchy.find_parent_classes(dodo_chr.default_export))

#%% Go

list(ue.hierarchy.find_sub_classes(dodo_chr.default_class))

#%% Go

list(ue.hierarchy.find_sub_classes('/Game/PrimalEarth/CoreBlueprints/Dino_Character_BP.Dino_Character_BP_C'))

#%%
