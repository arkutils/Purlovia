from itertools import chain, repeat
from typing import Any, List, Optional

from export.wiki.models import MinMaxPowerRange
from export.wiki.types import PrimalInventoryComponent, PrimalStructureItemContainer_SupplyCrate
from ue.hierarchy import find_parent_classes

from .models import ItemSet, ItemSetEntry


def get_loot_sets(lootinv: PrimalInventoryComponent | PrimalStructureItemContainer_SupplyCrate) -> List[Any]:
    item_sets: List[Any] = []
    # Add base item sets to the list
    base_sets = lootinv.get('ItemSetsOverride', fallback=None)
    if base_sets and base_sets.value and base_sets.value.value:
        sets = _get_item_sets_override(base_sets)
        item_sets.extend(sets)
    else:
        base_sets = lootinv.get('ItemSets', fallback=None)
        if base_sets and base_sets.values:
            sets = base_sets.values
            item_sets.extend(sets)

    # Add additional item sets to the list
    extra_sets = lootinv.get('AdditionalItemSetsOverride', fallback=None)
    if extra_sets and extra_sets.value and extra_sets.value.value:
        sets = _get_item_sets_override(extra_sets)
        item_sets.extend(sets)
    else:
        extra_sets = lootinv.get('AdditionalItemSets', fallback=None)
        if extra_sets and extra_sets.values:
            sets = extra_sets.values
            item_sets.extend(sets)

    return item_sets


def decode_item_name(item):
    item = item.value
    if not item:
        return None
    item = item.value
    if not item:
        return None
    return str(item.name)


def decode_item_entry(entry) -> ItemSetEntry:
    d = entry.as_dict()

    items_iter = (decode_item_name(item) for item in d['Items'].values)
    weights_iter = chain(d['ItemsWeights'].values, repeat(1))

    return ItemSetEntry(
        name=d['ItemEntryName'] or None,
        weight=d['EntryWeight'],
        rollOneItemOnly=d.get('bApplyQuantityToSingleItem', False),  # may not be present in old mods
        qty=MinMaxPowerRange(min=d['MinQuantity'], max=d['MaxQuantity'], pow=d['QuantityPower']),
        quality=MinMaxPowerRange(min=d['MinQuality'], max=d['MaxQuality'], pow=d['QualityPower']),
        bpChance=max(0, min(1, d['bForceBlueprint'] and 1 or d['ChanceToBeBlueprintOverride'])),
        grindable=d.get('bForcePreventGrinding', False),  # may not be present in old mods
        statMaxMult=d.get('ItemStatClampsMultiplier', 0) or 1,  # may not be present in old mods
        items=list(zip(weights_iter, items_iter)),
    )


def _gather_lootitemset_data(asset_ref):
    loader = asset_ref.asset.loader
    asset = loader.load_related(asset_ref)
    assert asset.default_export
    d = dict()

    for node in find_parent_classes(asset.default_export):
        if not node.startswith('/Game/'):
            break

        asset = loader[node]
        assert asset.default_export

        item_set = asset.default_export.properties.get_property('ItemSet', fallback=None)
        if item_set:
            set_data = item_set.as_dict()
            for key, value in set_data.items():
                if key not in d:
                    d[key] = value

    return d


def _get_item_sets_override(asset_ref):
    loader = asset_ref.asset.loader
    asset = loader.load_related(asset_ref)
    assert asset.default_export

    for node in find_parent_classes(asset.default_export):
        if not node.startswith('/Game/'):
            break

        asset = loader[node]
        assert asset.default_export

        sets = asset.default_export.properties.get_property('ItemSets', fallback=None)
        if sets:
            return sets.values

    return []


def decode_item_set(item_set, bp: Optional[str] = None) -> ItemSet:
    if isinstance(item_set, dict):
        d = item_set
        override = None
    else:
        d = item_set.as_dict()
        override = d['ItemSetOverride']

    if override:
        return decode_item_set(_gather_lootitemset_data(override), bp=override.value.value.fullname)

    return ItemSet(
        bp=bp,
        name=d.get('SetName', None) or None,
        weight=d.get('SetWeight', 1.0),
        canRepeatItems=not d.get('bItemsRandomWithoutReplacement', False),
        qtyScale=MinMaxPowerRange(
            min=d.get('MinNumItems', 1.0),
            max=d.get('MaxNumItems', 1.0),
            pow=d.get('NumItemsPower', 1.0),
        ),
        entries=[decode_item_entry(entry) for entry in d['ItemEntries'].values],
    )
