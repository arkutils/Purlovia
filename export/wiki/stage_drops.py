from logging import NullHandler, getLogger
from pathlib import PurePosixPath
from typing import *

from ark.types import PrimalItem
from automate.hierarchy_exporter import JsonHierarchyExportStage
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
    AdditionalItemSets: Mapping[int, ArrayProperty]


class DropsStage(JsonHierarchyExportStage):
    def get_skip(self):
        return not self.manager.config.export_wiki.ExportDrops

    def get_format_version(self) -> str:
        return "1"

    def get_field(self) -> str:
        return "drops"

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_ue_type(self) -> str:
        return DinoDropInventoryComponent.get_ue_type()

    def get_pre_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:
        if modid:
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            title = mod_data['title'] or mod_data['name']
            return dict(mod=dict(id=modid, tag=mod_data['name'], title=title))

        return None

    def extract(self, proxy: UEProxyStructure) -> Any:
        item: DinoDropInventoryComponent = cast(DinoDropInventoryComponent, proxy)

        v: Dict[str, Any] = dict()

        item_sets: List[Any] = []
        if item.has_override('ItemSets', 0):
            item_sets.extend(item.ItemSets[0].values)
        if item.has_override('AdditionalItemSets', 0):
            item_sets.extend(item.AdditionalItemSets[0].values)

        if not item_sets:
            return None

        v['blueprintPath'] = str(proxy.get_source().fullname)
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
        quantity=(d['MinQuantity'], d['MaxQuantity'], d['QuantityPower']),
        quality=(d['MinQuality'], d['MaxQuality'], d['QualityPower']),
        forceBP=d['bForceBlueprint'],
        items=[decode_item_name(item) for item in d['Items'].values],
    )


def decode_item_set(item_set):
    d = item_set.as_dict()
    return dict(
        name=d['SetName'] or None,
        itemsQuantity=(d['MinNumItems'], d['MaxNumItems'], d['NumItemsPower']),
        setWeight=d['SetWeight'],
        entries=[decode_item_entry(entry) for entry in d['ItemEntries'].values],
    )
