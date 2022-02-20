from typing import Optional

from automate.hierarchy_exporter import ExportModel, Field
from export.wiki.models import BoolLike, FloatLike, MinMaxPowerRange
from ue.properties import FloatProperty, StringLikeProperty


class ItemSetEntry(ExportModel):
    name: Optional[StringLikeProperty]
    weight: FloatProperty
    rollOneItemOnly: BoolLike = False
    qty: MinMaxPowerRange
    quality: MinMaxPowerRange
    bpChance: FloatLike = 0
    grindable: BoolLike = False
    statMaxMult: FloatLike = 1

    items: list[tuple[FloatProperty | float, Optional[str]]] = Field(
        ...,
        description="Pairs of (weighted chance, item class name)",
    )


class ItemSet(ExportModel):
    bp: Optional[str] = None
    name: Optional[StringLikeProperty]
    weight: FloatProperty | float
    canRepeatItems: BoolLike = Field(
        True,
        description="Each item entry can be picked more than once",
    )
    qtyScale: MinMaxPowerRange
    entries: list[ItemSetEntry]
