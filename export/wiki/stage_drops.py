from logging import NullHandler, getLogger
from pathlib import PurePosixPath
from typing import *

from ark.types import PrimalItem
from automate.hierarchy_exporter import JsonHierarchyExportStage
from ue.hierarchy import find_parent_classes
from ue.properties import ArrayProperty
from ue.proxy import UEProxyStructure

__all__ = [
    'DropsStage',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class DinoDropInventoryComponent(
        UEProxyStructure,
        uetype=
        '/Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_BP_Base.DinoDropInventoryComponent_BP_Base_C'):
    ItemSets: Mapping[int, ArrayProperty]
    ItemSetsOverride: Mapping[int, ArrayProperty]
    AdditionalItemSets: Mapping[int, ArrayProperty]
    AdditionalItemSetsOverride: Mapping[int, ArrayProperty]


class DropsStage(JsonHierarchyExportStage):
    def get_format_version(self) -> str:
        return "2"

    def get_name(self) -> str:
        return "drops"

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_ue_type(self) -> str:
        return DinoDropInventoryComponent.get_ue_type()

    def extract(self, proxy: UEProxyStructure) -> Any:
        inv: DinoDropInventoryComponent = cast(DinoDropInventoryComponent, proxy)

        v: Dict[str, Any] = dict()

        item_sets: List[Any] = []
        if inv.has_override('ItemSetsOverride', 0) and inv.ItemSetsOverride[0].value.value:
            override = _get_item_sets_override(inv.ItemSetsOverride[0])
            item_sets.extend(override)
        elif inv.has_override('ItemSets', 0):
            item_sets.extend(inv.ItemSets[0].values)

        if inv.has_override('AdditionalItemSetsOverride', 0) and inv.AdditionalItemSetsOverride[0].value.value:
            item_sets.extend(_get_item_sets_override(inv.AdditionalItemSetsOverride[0]))
        elif inv.has_override('AdditionalItemSets', 0):
            item_sets.extend(inv.AdditionalItemSets[0].values)

        if not item_sets:
            return None

        v['bp'] = str(proxy.get_source().fullname)
        v['sets'] = [d for d in (decode_item_set(item_set) for item_set in item_sets) if d['entries']]

        if not v['sets']:
            return None

        return v


def decode_item_name(item):
    item = item.value
    if not item: return None
    item = item.value
    if not item: return None
    return str(item.name)


def decode_item_entry(entry):
    d = entry.as_dict()
    return dict(
        name=str(d['ItemEntryName']) or None,
        weight=d['EntryWeight'],
        qty=(d['MinQuantity'], d['MaxQuantity'], d['QuantityPower']),
        quality=(d['MinQuality'], d['MaxQuality'], d['QualityPower']),
        forceBP=d['bForceBlueprint'],
        items=[decode_item_name(item) for item in d['Items'].values],
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


def decode_item_set(item_set):
    if isinstance(item_set, dict):
        d = item_set
        override = None
    else:
        d = item_set.as_dict()
        override = d['ItemSetOverride']

    if override:
        return decode_item_set(_gather_lootitemset_data(override))

    return dict(
        name=d.get('SetName', None) or None,
        weight=d.get('SetWeight', 1.0),
        qtyScale=(d.get('MinNumItems', 1.0), d.get('MaxNumItems', 1.0), d.get('NumItemsPower', 1.0)),
        entries=[decode_item_entry(entry) for entry in d['ItemEntries'].values],
    )
