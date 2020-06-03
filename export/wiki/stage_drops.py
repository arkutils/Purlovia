from typing import Any, List, Mapping, Optional, Union, cast

from automate.hierarchy_exporter import ExportFileModel, ExportModel, Field, JsonHierarchyExportStage
from export.wiki.types import PrimalStructureItemContainer_SupplyCrate
from ue.hierarchy import find_parent_classes
from ue.properties import ArrayProperty, BoolProperty, FloatProperty, StringLikeProperty
from ue.proxy import UEProxyStructure
from utils.log import get_logger

from .models import MinMaxPowerRange

__all__ = [
    'DropsStage',
    'get_loot_sets',
    'DinoDropInventoryComponent',
    'decode_item_name',
    'decode_item_entry',
    'decode_item_set',
]

logger = get_logger(__name__)

DINO_DROP_BASE_CLS = '/Game/PrimalEarth/CoreBlueprints/Inventories/DinoDropInventoryComponent_BP_Base' + \
    '.DinoDropInventoryComponent_BP_Base_C'


class DinoDropInventoryComponent(UEProxyStructure, uetype=DINO_DROP_BASE_CLS):
    ItemSets: Mapping[int, ArrayProperty]
    ItemSetsOverride: Mapping[int, ArrayProperty]
    AdditionalItemSets: Mapping[int, ArrayProperty]
    AdditionalItemSetsOverride: Mapping[int, ArrayProperty]


class ItemSetEntry(ExportModel):
    name: Optional[StringLikeProperty]
    weight: FloatProperty
    qty: MinMaxPowerRange
    quality: MinMaxPowerRange
    forceBP: BoolProperty
    items: List[Optional[str]]


class ItemSet(ExportModel):
    name: Optional[StringLikeProperty]
    weight: Union[FloatProperty, float]
    qtyScale: MinMaxPowerRange
    entries: List[ItemSetEntry]


class Drop(ExportModel):
    bp: str = Field(
        ...,
        description="Full blueprint path",
    )
    sets: Optional[List[ItemSet]] = Field(
        None,
        description="Loot sets",
    )


class DropExportModel(ExportFileModel):
    drops: List[Drop] = Field(
        ...,
        description="List of loot crates",
    )

    class Config:
        title = "Dino drop loot tables"


class DropsStage(JsonHierarchyExportStage):
    def get_format_version(self) -> str:
        return "3"

    def get_name(self) -> str:
        return "drops"

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_ue_type(self) -> str:
        return DinoDropInventoryComponent.get_ue_type()

    def get_schema_model(self):
        return DropExportModel

    def extract(self, proxy: UEProxyStructure) -> Any:
        inv: DinoDropInventoryComponent = cast(DinoDropInventoryComponent, proxy)

        item_sets = get_loot_sets(inv)
        if not item_sets:
            return None

        result: Drop = Drop(bp=proxy.get_source().fullname)
        result.sets = [d for d in (decode_item_set(item_set) for item_set in item_sets) if d.entries]

        if not result.sets:
            return None

        return result


def get_loot_sets(lootinv: Union[DinoDropInventoryComponent, PrimalStructureItemContainer_SupplyCrate]) -> List[Any]:
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
    return ItemSetEntry(
        name=d['ItemEntryName'] or None,
        weight=d['EntryWeight'],
        qty=dict(
            min=d['MinQuantity'],
            max=d['MaxQuantity'],
            pow=d['QuantityPower'],
        ),
        quality=dict(
            min=d['MinQuality'],
            max=d['MaxQuality'],
            pow=d['QualityPower'],
        ),
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


def decode_item_set(item_set) -> ItemSet:
    if isinstance(item_set, dict):
        d = item_set
        override = None
    else:
        d = item_set.as_dict()
        override = d['ItemSetOverride']

    if override:
        return decode_item_set(_gather_lootitemset_data(override))

    return ItemSet(
        name=d.get('SetName', None) or None,
        weight=d.get('SetWeight', 1.0),
        qtyScale=MinMaxPowerRange(
            min=d.get('MinNumItems', 1.0),
            max=d.get('MaxNumItems', 1.0),
            pow=d.get('NumItemsPower', 1.0),
        ),
        entries=[decode_item_entry(entry) for entry in d['ItemEntries'].values],
    )
