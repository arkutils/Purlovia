from itertools import chain, repeat
from typing import Any, List, Optional, Tuple, Union, cast

from automate.hierarchy_exporter import ExportFileModel, ExportModel, Field, JsonHierarchyExportStage
from export.wiki.types import PrimalInventoryComponent, PrimalStructureItemContainer_SupplyCrate
from ue.hierarchy import find_parent_classes
from ue.properties import BoolProperty, FloatProperty, IntProperty, StringLikeProperty
from ue.proxy import UEProxyStructure
from utils.log import get_logger

from .models import MinMaxPowerRange, MinMaxRange

__all__ = [
    'DropsStage',
    'get_loot_sets',
    'decode_item_name',
    'decode_item_entry',
    'decode_item_set',
]

logger = get_logger(__name__)


class ItemSetEntry(ExportModel):
    name: Optional[StringLikeProperty]
    weight: FloatProperty
    qty: MinMaxPowerRange
    quality: MinMaxPowerRange
    forceBP: BoolProperty
    items: List[Tuple[Union[FloatProperty, float], Optional[str]]] = Field(
        ...,
        description="Pairs of (weighted chance, item class name)",
    )


class ItemSet(ExportModel):
    name: Optional[StringLikeProperty]
    weight: Union[FloatProperty, float]
    qtyScale: MinMaxPowerRange
    qualityScale: MinMaxPowerRange
    entries: List[ItemSetEntry]


class Drop(ExportModel):
    bp: str = Field(
        ...,
        description="Full blueprint path",
    )

    name: StringLikeProperty = Field('')
    description: StringLikeProperty = Field('')
    maxItems: IntProperty = Field(0)
    maxWeight: FloatProperty = Field(25)

    randomSetsWithNoReplacement: Optional[BoolProperty] = Field(
        None,
        description="Unknown meaning",
    )
    qualityMult: Optional[MinMaxRange] = Field(
        MinMaxRange(min=1, max=1),
        title="Quality range",
    )
    qtyMult: Optional[MinMaxPowerRange] = Field(
        MinMaxPowerRange(min=1, max=1, pow=1),
        title="Quantity range",
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
        return "5"

    def get_name(self) -> str:
        return "drops"

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_ue_type(self) -> str:
        return PrimalInventoryComponent.get_ue_type()

    def get_schema_model(self):
        return DropExportModel

    def extract(self, proxy: UEProxyStructure) -> Any:
        inv: PrimalInventoryComponent = cast(PrimalInventoryComponent, proxy)

        item_sets = get_loot_sets(inv)
        if not item_sets:
            return None

        result: Drop = Drop(bp=proxy.get_source().fullname)
        result.name = inv.InventoryNameOverride[0]
        result.description = inv.RemoteInventoryDescriptionString[0]
        result.maxItems = inv.MaxInventoryItems[0]
        result.maxWeight = inv.MaxInventoryWeight[0]

        result.randomSetsWithNoReplacement = inv.bSetsRandomWithoutReplacement[0]
        result.qualityMult = MinMaxRange(min=inv.MinQualityMultiplier[0], max=inv.MaxQualityMultiplier[0])
        result.qtyMult = MinMaxPowerRange(min=inv.MinItemSets[0], max=inv.MaxItemSets[0], pow=inv.NumItemSetsPower[0])

        result.sets = [d for d in (decode_item_set(item_set) for item_set in item_sets) if d.entries]

        if not result.sets:
            return None

        return result


def get_loot_sets(lootinv: Union[PrimalInventoryComponent, PrimalStructureItemContainer_SupplyCrate]) -> List[Any]:
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
        qualityScale=MinMaxPowerRange(
            min=d.get('MinQuality', 1.0),
            max=d.get('MaxQuality', 1.0),
            pow=d.get('QualityPower', 1.0),
        ),
        entries=[decode_item_entry(entry) for entry in d['ItemEntries'].values],
    )
