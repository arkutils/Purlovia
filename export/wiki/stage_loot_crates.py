from logging import NullHandler, getLogger
from pathlib import PurePosixPath
from typing import *

from automate.hierarchy_exporter import JsonHierarchyExportStage
from export.wiki.types import PrimalStructureItemContainer_SupplyCrate
from ue.proxy import UEProxyStructure

from .stage_drops import decode_item_set

__all__ = [
    'ItemsStage',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class LootCratesStage(JsonHierarchyExportStage):
    def get_format_version(self) -> str:
        return "2"

    def get_name(self) -> str:
        return "loot_crates"

    def get_field(self) -> str:
        return "lootCrates"

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_ue_type(self) -> str:
        return PrimalStructureItemContainer_SupplyCrate.get_ue_type()

    def extract(self, proxy: UEProxyStructure) -> Any:
        crate: PrimalStructureItemContainer_SupplyCrate = cast(PrimalStructureItemContainer_SupplyCrate, proxy)

        v: Dict[str, Any] = dict()
        v['bp'] = crate.get_source().fullname
        v['requiredLevel'] = crate.RequiredLevelToAccess[0]
        v['maxLevel'] = crate.MaxLevelToAccess[0]
        v['healthLoss'] = dict(initialTime=crate.InitialTimeToLoseHealth[0], interval=crate.IntervalTimeToLoseHealth[0])
        v['randomSetsWithNoReplacement'] = crate.bSetsRandomWithoutReplacement[0]
        v['qualityMult'] = (crate.MinQualityMultiplier[0], crate.MaxQualityMultiplier[0])
        v['setCount'] = (crate.MinItemSets[0], crate.MaxItemSets[0], crate.NumItemSetsPower[0])

        item_sets: List[Any] = []
        if crate.has_override('ItemSets', 0):
            item_sets.extend(crate.ItemSets[0].values)
        if crate.has_override('AdditionalItemSets', 0):
            item_sets.extend(crate.AdditionalItemSets[0].values)

        if not item_sets:
            return None

        v['sets'] = [d for d in (decode_item_set(item_set) for item_set in item_sets) if d['entries']]

        return v
