# Asset interactive experiments

#%% Setup

from interactive_utils import *  # pylint: disable=wrong-import-order

import json
from typing import *

from ark.types import PrimalItem
from automate.ark import ArkSteamManager
from ue.asset import UAsset
from ue.gathering import gather_properties
from ue.properties import ArrayProperty
from ue.proxy import UEProxyStructure

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
    'Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_Turkey',
    # 'Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_Carnivore_Huge_Giga_Bone',
    # 'Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_Carnivore_Huge_MegaFireWyvern_Bone',
    # 'Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_Carnivore_Huge_Sauro_Bone',
    # 'Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_Carnivore_Mega_Raptor_Skel',
    # 'Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_Carnivore_Mega_Rex_Bone',
    # 'Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_Carnivore_MegaCarno_Skel',
    # 'Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_Costume_Jerboa_Bone',
    # 'Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_Costume_Quetz_Bone',
    # 'Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_Costume',
    # 'Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_Stego_Skel',
    # 'Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_Trike_Skel',
]

#%% Proxy type


class DinoDrop(
        UEProxyStructure,
        uetype=
        '/Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_BP_Base.DinoDropInventoryComponent_BP_Base_C'):
    ItemSets: Mapping[int, ArrayProperty]
    AdditionalItemSets: Mapping[int, ArrayProperty]


#%% Loot drops


def decode_item_entry(entry):
    d = entry.as_dict()
    return dict(name=str(d['ItemEntryName']),
                weight=float(d['EntryWeight']),
                minQuantity=int(d['MinQuantity']),
                maxQuantity=int(d['MaxQuantity']),
                quantityPower=int(d['QuantityPower']),
                minQuality=int(d['MinQuality']),
                maxQuality=int(d['MaxQuality']),
                qualityPower=int(d['QualityPower']),
                forceBP=bool(d['bForceBlueprint']),
                items=[str(item.value.value.name) for item in d['Items'].values])


def decode_item_set(item_set):
    d = item_set.as_dict()
    return dict(name=str(d['SetName']),
                min=int(d['MinNumItems']),
                max=int(d['MaxNumItems']),
                numItemsPower=int(d['NumItemsPower']),
                setWeight=int(d['SetWeight']),
                entries=[decode_item_entry(entry) for entry in d['ItemEntries'].values])


species = []
for assetname in assetnames:
    asset: UAsset = loader[assetname]
    assert asset.default_export
    assert asset.default_class

    item: DinoDrop = gather_properties(asset.default_export)

    item_sets: List[Any] = []
    if item.has_override('ItemSets', 0):
        item_sets.extend(item.ItemSets[0].values)
    if item.has_override('AdditionalItemSets', 0):
        item_sets.extend(item.AdditionalItemSets[0].values)

    if not item_sets:
        continue

    v: Dict[str, Any] = dict()
    v['class'] = str(asset.default_class.name)
    v['sets'] = [d for d in (decode_item_set(item_set) for item_set in item_sets) if d['entries']]

    species.append(v)

pprint(species[0])

#%% JSON output

with open('export-drops.json', 'wt') as f:
    json.dump(species, f, indent='  ', separators=(',', ': '))

#%%
