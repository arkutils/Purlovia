from pathlib import PurePosixPath
from typing import Any, Dict, List, Optional, Tuple, cast

from pydantic import BaseModel, Field

from automate.hierarchy_exporter import JsonHierarchyExportStage
from export.wiki.types import PrimalStructureItemContainer_SupplyCrate
from ue.proxy import UEProxyStructure
from utils.log import get_logger

from .stage_drops import _get_item_sets_override, decode_item_set, get_loot_sets

__all__ = [
    'LootCratesStage',
]

logger = get_logger(__name__)


class MinMaxRange(BaseModel):
    min: float
    max: float

    def __init__(self, min, max):
        super().__init__(min=min, max=max)


class MinMaxPowerRange(BaseModel):
    min: float
    max: float
    pow: float = Field(..., title="Power", description="Affects the power curve used to select a value in the range")

    def __init__(self, min, max, pow):
        super().__init__(min=min, max=max, pow=pow)


class DecayTime(BaseModel):
    start: float
    interval: float


class LootCrate(BaseModel):
    bp: str = Field(
        ...,
        title="Full blueprint path",
    )
    levelReq: Optional[MinMaxRange] = Field(
        None,
        title="Level requirements",
        description="This is a really long description that would mess up the nice structure above",
    )
    decayTime: Optional[DecayTime] = Field(
        None,
        title="Decay timing",
    )
    randomSetsWithNoReplacement: Optional[bool]
    qualityMult: Optional[MinMaxRange] = Field(
        None,
        title="Quality range",
    )
    setQty: Optional[MinMaxPowerRange] = Field(
        None,
        title="Quantity range",
    )
    sets: Optional[List[Any]]


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

        item_sets = get_loot_sets(crate)
        if not item_sets:
            return None

        out = LootCrate(bp=crate.get_source().fullname)
        out.levelReq = MinMaxRange(min=crate.RequiredLevelToAccess[0], max=crate.MaxLevelToAccess[0])
        out.decayTime = DecayTime(start=crate.InitialTimeToLoseHealth[0], interval=crate.IntervalTimeToLoseHealth[0])
        out.randomSetsWithNoReplacement = bool(crate.bSetsRandomWithoutReplacement[0])
        out.qualityMult = MinMaxRange(min=crate.MinQualityMultiplier[0], max=crate.MaxQualityMultiplier[0])
        out.setQty = MinMaxPowerRange(min=crate.MinItemSets[0], max=crate.MaxItemSets[0], pow=crate.NumItemSetsPower[0])
        out.sets = [d for d in (decode_item_set(item_set) for item_set in item_sets) if d['entries']]

        return out
