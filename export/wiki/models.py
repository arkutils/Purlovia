from typing import Union

from automate.hierarchy_exporter import ExportModel, Field
from ue.properties import FloatProperty, IntProperty

__all__ = [
    'MinMaxRange',
    'MinMaxPowerRange',
    'DecayTime',
]


class MinMaxRange(ExportModel):
    min: Union[FloatProperty, IntProperty, float]
    max: Union[FloatProperty, IntProperty, float]


class MinMaxPowerRange(ExportModel):
    min: Union[FloatProperty, IntProperty, float]
    max: Union[FloatProperty, IntProperty, float]
    pow: Union[FloatProperty, IntProperty, float] = Field(
        ...,
        title="Power",
        description="Affects the power curve used to select a value in the range",
    )


class DecayTime(ExportModel):
    start: FloatProperty
    interval: FloatProperty
