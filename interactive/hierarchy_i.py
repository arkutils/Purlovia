# Interactive testing of hierarchy utilities

#%% Setup

from interactive.setup import *  # pylint: disable=wrong-import-order

import ue.hierarchy

#%% Discover

ue.hierarchy.tree.clear()
ue.hierarchy.load_internal_hierarchy(Path('config/hierarchy.yaml'))
ue.hierarchy.explore_path('/Game/PrimalEarth/Dinos/Dodo', loader, set())

# ark.discovery.initialise_hierarchy(loader)

#%% Creation

dodo_chr: UAsset = loader['Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP']
assert dodo_chr.default_class and dodo_chr.default_export

#%% Go

list(ue.hierarchy.find_parent_classes(dodo_chr.default_export))

#%% Go

list(ue.hierarchy.find_sub_classes(dodo_chr.default_class))

#%% Go

list(ue.hierarchy.find_sub_classes('/Game/PrimalEarth/CoreBlueprints/Dino_Character_BP.Dino_Character_BP_C'))

#%%
