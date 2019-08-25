from typing import Optional

from ark.export_wiki.types import PrimalWorldSettings
from ue.loader import AssetLoader


class GeoData:
    origin: float
    scale: float
    multiplier: float
    shift: float

    def __init__(self, origin: float, scale: float):
        self.origin = origin
        self.scale = scale
        self.multiplier = scale * 10
        self.shift = (scale*1000 - abs(origin)) / self.multiplier

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
    lat_origin = world_settings.LatitudeOrigin[0].value
    long_origin = world_settings.LongitudeOrigin[0].value
    lat_scale = world_settings.LatitudeScale[0].value
    long_scale = world_settings.LongitudeScale[0].value

    latitude = GeoData(lat_origin, lat_scale)
    longitude = GeoData(long_origin, long_scale)
    return (latitude, longitude)
