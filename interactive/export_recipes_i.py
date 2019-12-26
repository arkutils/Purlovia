# Asset interactive experiments

#%% Setup

from interactive_utils import *  # pylint: disable=wrong-import-order

import json
from typing import *

from ark.common import PRIMALITEM_CLS
from ark.discovery import initialise_hierarchy
from ark.types import PrimalItem
from automate.ark import ArkSteamManager
from ue.asset import UAsset
from ue.gathering import gather_properties
from ue.hierarchy import inherits_from

arkman = ArkSteamManager()
loader = arkman.getLoader()
initialise_hierarchy(arkman)

#%% Asset list

assetnames = [
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Cloth/PrimalItem_DodoRexTribute_WinterWonderland',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Allosaurus',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Ankylosaurus',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Argent',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Baryonyx',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Base',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_BogSpider',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Bronto',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Carbonemys',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Carnotaurus',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Castroides',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Cherufe',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Daeodon',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Direwolf',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Doedicurus',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Equus',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Gasbag',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Gigant',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Gigantopithecus',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Iguanodon',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Kentrosaurus',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Mammoth',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Megalania',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Megaloceros',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Megatherium',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_MoleRat',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Moschops',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Oviraptor',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Paraceratherium',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Parasaur',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Phiomia',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Phoenix',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Procoptodon',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Pteranodon',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Pulmonoscorpius',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Quetzal',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Raptor',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Reaper',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Rex',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_RockDrake',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_RockGolem',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Saber',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Shapeshifter_Large',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Shapeshifter_Small',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Sheep',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_SnowOwl',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Spino',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Stego',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Tapejara',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_TerrorBird',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Therizino',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Thylacoleo',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Trike',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_WoollyRhino',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Wyvern',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/PrimalItemSkin_ChibiDino_Yutyrannus',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/SKComponent_SkinAttachment_ChibiDino',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/ChibiDinos/T_ChibiIconBG',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_WW_Nutcracker_Slingshot',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_WW_ReindeerAntlersHat',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_WW_SwimShirt_DinoOrnaments',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_WW_SwimShirt_JerboaWreath',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_WW_Underwear_DinoOrnaments',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_WW_Underwear_JerboaWreath',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_WW_WinterHatA',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_WW_WinterHatB',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_WW_WinterHatC',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_WW_Xmas_Bola',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_WW_XmasSweaterBronto',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_WW_XmasSweaterCarno',
    'Game/PrimalEarth/CoreBlueprints/Items/Armor/Skin/PrimalItemSkin_WW_XmasSweaterChibi',
    'Game/PrimalEarth/CoreBlueprints/Items/Consumables/BaseBPs/PrimalItemConsumable_UnlockEmote_Caroling',
    'Game/PrimalEarth/CoreBlueprints/Items/Consumables/BaseBPs/PrimalItemConsumable_UnlockEmote_HappyClap',
    'Game/PrimalEarth/CoreBlueprints/Items/Consumables/BaseBPs/PrimalItemConsumable_UnlockEmote_NutcrackerDance',
    'Game/PrimalEarth/CoreBlueprints/Items/Consumables/Icons/Emotes/Winterwonderland_Caroling',
    'Game/PrimalEarth/CoreBlueprints/Items/Consumables/Icons/Emotes/Winterwonderland_Happy_Clap',
    'Game/PrimalEarth/CoreBlueprints/Items/Consumables/Icons/Emotes/Winterwonderland_Nutcracker_Dance',
]

#%% Items

items = []
for assetname in assetnames:
    try:
        asset: UAsset = loader[assetname]
    except Exception:
        print(f"Couldn't load: {assetname}")
        continue

    if not asset.default_export or not asset.default_class:
        print(f"No default exports: {assetname}")
        continue

    if not inherits_from(asset.default_export, PRIMALITEM_CLS):
        print(f"Not an item: {assetname}")
        continue

    item: PrimalItem = gather_properties(asset.default_export)

    v: Dict[str, Any] = dict()
    v['name'] = str(item.DescriptiveNameBase[0])
    v['description'] = str(item.ItemDescription[0])
    v['blueprintPath'] = asset.default_class.fullname

    if hasattr(item, 'BaseCraftingResourceRequirements'):
        recipe = item.BaseCraftingResourceRequirements[0]
        if recipe.values:
            v['recipe'] = []
            for entry in recipe.values:
                recipe_line = entry.as_dict()

                v['recipe'].append(
                    dict(
                        exact=bool(recipe_line['bCraftingRequireExactResourceType']),
                        quantity=int(recipe_line['BaseResourceRequirement']),
                        type=str(recipe_line['ResourceItemType'].value.value.name),
                    ))

    if getattr(item, 'ItemIcon', None):
        v['icon'] = item.ItemIcon[0].value.value.fullname
    if getattr(item, 'DefaultFolderPaths', None):
        v['folders'] = [str(folder) for folder in item.DefaultFolderPaths[0].values]

    items.append(v)

#%% JSON output

with open('export-items.json', 'wt') as f:
    json.dump(items, f, indent='  ', separators=(',', ': '))

# %%
