from typing import List, Optional, Tuple, Union

from automate.hierarchy_exporter import ExportModel, Field
from ue.properties import BoolProperty, FloatProperty, IntProperty

__all__ = [
    'MinMaxRange',
    'MinMaxPowerRange',
    'DecayTime',
    'ItemChancePair',
]

BoolLike = Union[BoolProperty, bool]
IntLike = Union[IntProperty, int]
FloatLike = Union[FloatProperty, IntProperty, float, int]


class ClassRemap(ExportModel):
    from_bp: str = Field(alias="from")
    to: Optional[str] = None


class Vector(ExportModel):
    x: FloatLike
    y: FloatLike
    z: FloatLike


class WeighedClassSwap(ExportModel):
    from_class: Optional[str] = Field(alias="from")
    exact: bool = Field(False, title="Match class exactly")
    to: List[Tuple[float, Optional[str]]]
    during: str = Field('None', title="Event the rule is active in")


class MinMaxRange(ExportModel):
    min: FloatLike
    max: FloatLike


class MinMaxChanceRange(ExportModel):
    chance: float
    min: FloatLike
    max: FloatLike


class MinMaxPowerRange(ExportModel):
    min: FloatLike
    max: FloatLike
    pow: FloatLike = Field(
        ...,
        title="Power",
        description="Affects the power curve used to select a value in the range",
    )


class DecayTime(ExportModel):
    start: FloatProperty
    interval: FloatProperty


class ItemChancePair(ExportModel):
    chance: float = Field(..., description="Chance this item will be selected, in an inclusive range from 0 to 1")
    item: str
