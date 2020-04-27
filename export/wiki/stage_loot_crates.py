from logging import NullHandler, getLogger
from pathlib import PurePosixPath
from typing import *

from automate.hierarchy_exporter import JsonHierarchyExportStage
from export.wiki.types import PrimalStructureItemContainer_SupplyCrate
from ue.proxy import UEProxyStructure

from .stage_drops import _get_item_sets_override, decode_item_set, get_loot_sets

__all__ = [
    'LootCratesStage',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class LootCratesStage(JsonHierarchyExportStage):
    def get_format_version(self) -> str:
        return "3"

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
        v['levelReq'] = (crate.RequiredLevelToAccess[0], crate.MaxLevelToAccess[0])
        v['decayTime'] = dict(start=crate.InitialTimeToLoseHealth[0], interval=crate.IntervalTimeToLoseHealth[0])
        v['randomSetsWithNoReplacement'] = crate.bSetsRandomWithoutReplacement[0]
        v['qualityMult'] = (crate.MinQualityMultiplier[0], crate.MaxQualityMultiplier[0])
        v['setQty'] = (crate.MinItemSets[0], crate.MaxItemSets[0], crate.NumItemSetsPower[0])

        item_sets = get_loot_sets(crate)
        if not item_sets:
            return None

        v['sets'] = [d for d in (decode_item_set(item_set) for item_set in item_sets) if d['entries']]

        return v
