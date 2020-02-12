from dataclasses import dataclass, field
from typing import Union

from export.wiki.types import PrimalWorldSettings
from ue.loader import AssetLoader
from ue.properties import FloatProperty


class GeoCoordCalculator:
    origin: Union[float, FloatProperty]
    scale: Union[float, FloatProperty]
    multiplier: Union[float, FloatProperty] = field(init=False)
    shift: Union[float, FloatProperty] = field(init=False)

    def __init__(self, origin: float, scale: float):
        '''
        Origin is the location of the top left corner of the map.
        Scale is the distance from a corner to the opposite corner.
        Shift is the offset of landscape origin to world origin (0, 0 point).
        '''
        self.origin = origin
        self.scale = scale
        self.multiplier = self.scale * 10
        self.shift = -self.origin / self.multiplier

    def from_units(self, units: Union[int, float]) -> float:
        '''
        Calculates a coordinate from UE's units (centimeters).
        '''
        return units / self.multiplier + self.shift

    def __str__(self):
        return f'GeoCoordCalculator (origin={self.origin}, scale={self.scale})'
