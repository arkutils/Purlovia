from dataclasses import dataclass, field
from typing import Union

from ue.loader import AssetLoader
from ue.properties import FloatProperty

from .types import PrimalWorldSettings


@dataclass
class GeoData:
    origin: Union[float, FloatProperty]
    scale: Union[float, FloatProperty]
    multiplier: Union[float, FloatProperty] = field(init=False)
    shift: Union[float, FloatProperty] = field(init=False)

    def __post_init__(self):
        '''
        Origin is the location of the top left corner of the map.
        Scale is the distance from the top left corner to the opposite
        (bottom right) corner.
        '''
        self.multiplier = self.scale * 10
        self.shift = (self.scale*1000 + self.origin) / self.multiplier

    # Calculates geo coords from UE units.
    def from_units(self, units: int):
        return units / self.multiplier + self.shift

    def format_for_json(self):
        return {
            "Origin": self.origin,
            "Scale": self.scale,
            "Multi": self.multiplier,
            "Shift": self.shift
        }

    def __str__(self):
        return f'GeoData (Origin {self.origin}, Scale {self.scale})'


def gather_geo_data(world_settings: PrimalWorldSettings):
    lat_origin = world_settings.LatitudeOrigin[0]
    long_origin = world_settings.LongitudeOrigin[0]
    lat_scale = world_settings.LatitudeScale[0]
    long_scale = world_settings.LongitudeScale[0]

    latitude = GeoData(lat_origin, lat_scale)
    longitude = GeoData(long_origin, long_scale)
    return (latitude, longitude)
