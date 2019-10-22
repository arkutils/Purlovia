# Asset interactive experiments

#%% Setup

from interactive_utils import *  # pylint: disable=wrong-import-order

import json
from typing import *

from ark.types import PrimalItem
from automate.ark import ArkSteamManager
from ue.asset import UAsset
from ue.gathering import gather_properties

arkman = ArkSteamManager()
loader = arkman.getLoader()

#%% Asset list

# /Game/PrimalEarth/CoreBlueprints/Items/Structures/Halloween
# /Game/PrimalEarth/Effects/Particles/Env/Halloween
# /Game/PrimalEarth/Environment/Seasonal/Halloween
# /Game/PrimalEarth/Human/Female/Outfits/Halloween
# /Game/PrimalEarth/Human/Male/Outfits/Halloween
# /Game/PrimalEarth/Structures/Halloween

assetnames = [
    'Game/PrimalEarth/CoreBlueprints/Items/Structures/Halloween/PrimalItemStructure_EasterEgg',
    'Game/PrimalEarth/CoreBlueprints/Items/Structures/Halloween/PrimalItemStructure_HW_Grave',
    'Game/PrimalEarth/CoreBlueprints/Items/Structures/Halloween/PrimalItemStructure_Pumpkin',
    'Game/PrimalEarth/CoreBlueprints/Items/Structures/Halloween/PrimalItemStructure_Scarecrow',
    'Game/PrimalEarth/CoreBlueprints/Items/Structures/Halloween/PrimalItemStructure_TrainingDummy',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_FE_HeadlessHat',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_FE_PumpkinHat',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_FE_ScaryFaceMask',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_FE_SwimShirt_Araneo',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_FE_SwimShirt_Onyc',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_FE_SwimShirt_VampireDodo',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_FE_Underwear_Araneo',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_FE_Underwear_Onyc',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_FE_Underwear_VampireDodo',
    'Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_FE_Craftable_CandyCorn',
    'Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_FE_Crafted_CandyCorn',
]

#%% Recipes

recipes = []
for assetname in assetnames:
    asset: UAsset = loader[assetname]
    assert asset.default_export
    assert asset.default_class
    item: PrimalItem = gather_properties(asset.default_export)
    recipe = item.BaseCraftingResourceRequirements[0]
    if not recipe.values:
        continue

    v: Dict[str, Any] = dict()
    v['name'] = str(item.DescriptiveNameBase[0])
    v['description'] = str(item.ItemDescription[0])
    v['blueprintPath'] = asset.default_class.fullname
    v['recipe'] = []
    for entry in recipe.values:
        recipe_line = entry.as_dict()

        v['recipe'].append(
            dict(
                exact=bool(recipe_line['bCraftingRequireExactResourceType']),
                quantity=int(recipe_line['BaseResourceRequirement']),
                type=str(recipe_line['ResourceItemType'].value.value.name),
            ))

    recipes.append(v)

pprint(recipes[0])

#%% JSON output

with open('halloween-recipes.json', 'wt') as f:
    json.dump(recipes, f, indent='  ', separators=(',', ': '))
