from typing import Any, List, Optional, cast

from automate.hierarchy_exporter import ExportFileModel, ExportModel, Field, JsonHierarchyExportStage
from export.wiki.types import PrimalInventoryComponent
from ue.properties import BoolProperty, FloatProperty, IntProperty, StringLikeProperty
from ue.proxy import UEProxyStructure
from utils.log import get_logger

from .loot.gathering import decode_item_set, get_loot_sets
from .loot.models import ItemSet
from .models import MinMaxPowerRange, MinMaxRange

__all__ = [
    'DropsStage',
]

logger = get_logger(__name__)


class Drop(ExportModel):
    bp: str = Field(
        ...,
        description="Full blueprint path",
    )

    name: StringLikeProperty = Field('')
    description: StringLikeProperty = Field('')
    maxItems: IntProperty = Field(0)
    maxWeight: FloatProperty = Field(25)

    noRepeatsInSets: Optional[BoolProperty] = Field(
        None,
        title="No repeats in sets",
        description="Entries cannot be picked more than once per set",
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
        return "7"

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

        result.noRepeatsInSets = inv.bSetsRandomWithoutReplacement[0]
        result.qualityMult = MinMaxRange(min=inv.MinQualityMultiplier[0], max=inv.MaxQualityMultiplier[0])
        result.qtyMult = MinMaxPowerRange(min=inv.MinItemSets[0], max=inv.MaxItemSets[0], pow=inv.NumItemSetsPower[0])

        result.sets = [d for d in (decode_item_set(item_set) for item_set in item_sets) if d.entries]

        if not result.sets:
            return None

        return result
