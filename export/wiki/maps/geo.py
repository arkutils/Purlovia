from typing import Union

from export.wiki.types import PrimalWorldSettings
from ue.loader import AssetLoader
from ue.properties import FloatProperty


class GeoCoordCalculator:
    origin: Union[float, FloatProperty]
    scale: Union[float, FloatProperty]
    multiplier: Union[float, FloatProperty]
    shift: Union[float, FloatProperty]

    def __init__(self, origin: Union[float, FloatProperty], scale: Union[float, FloatProperty]):
        '''
        Origin is the Y (for latitude, or X for longitude coord of map's
        corner in the second quadrant.
        Scale is the width (longitude) or height (latitude) of the map.

        Calculated shift value is equal to the shift required (on a given
        axis) to reposition the landscape origin to world origin (point 0, 0).
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
