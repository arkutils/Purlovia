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

    def __init__(self, min, max):  # pylint: disable=redefined-builtin
        super().__init__(min=min, max=max)


class MinMaxPowerRange(ExportModel):
    min: Union[FloatProperty, IntProperty, float]
    max: Union[FloatProperty, IntProperty, float]
    pow: Union[FloatProperty, IntProperty, float] = Field(
        ...,
        title="Power",
        description="Affects the power curve used to select a value in the range",
    )

    def __init__(self, min, max, pow):  # pylint: disable=redefined-builtin
        super().__init__(min=min, max=max, pow=pow)


class DecayTime(ExportModel):
    start: FloatProperty
    interval: FloatProperty
