from typing import Optional, Union

from ue.loader import AssetLoader
from ue.properties import FloatProperty

from .types import PrimalWorldSettings


class GeoData:
    origin: Union[float, FloatProperty]
    scale: Union[float, FloatProperty]
    multiplier: Union[float, FloatProperty]
    shift: Union[float, FloatProperty]

    def __init__(self, origin: Union[float, FloatProperty], scale: Union[float, FloatProperty]):
        self.origin = origin
        self.scale = scale
        self.multiplier = scale * 10
        self.shift = (scale*1000 - abs(origin)) / self.multiplier

    # Offsets a coordinate in UE units by the map origin.
    # Lets us skip the shift completely during the calculations.
    def offset(self, centimeters: Union[float, FloatProperty]):
        return abs(self.origin) + centimeters

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
