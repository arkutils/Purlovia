from typing import Optional

from ue.asset import UAsset
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

    # Offsets a coordinate in UE units by the map origin.
    # Lets us skip the shift completely during the calculations.
    def offset(self, centimeters: float):
        return abs(self.origin) + centimeters

    # Calculates geo coords from UE units.
    def from_units(self, units: int):
        return self.offset(units) / self.multiplier

    def __str__(self):
        return f'GeoData (Origin {self.origin}, Scale {self.scale})'


def gather_geo_data(level: UAsset, world_settings: dict):
    def _get(properties, key, default):
        if key in properties:
            return properties[key][0].value
        return default

    lat_origin = _get(world_settings, "LatitudeOrigin", -400000.0)
    long_origin = _get(world_settings, "LongitudeOrigin", -400000.0)
    lat_scale = _get(world_settings, "LatitudeScale", 800.0)
    long_scale = _get(world_settings, "LongitudeScale", 800.0)

    latitude = GeoData(lat_origin, lat_scale)
    longitude = GeoData(long_origin, long_scale)
    return (latitude, longitude)


def qowyn_format_location(ue_coords: tuple, lat: GeoData, long: GeoData):
    if len(ue_coords) is 2:
        # XY pair
        return {"lat": lat.from_units(ue_coords[1]), "long": long.from_units(ue_coords[0])}

    if len(ue_coords) is 3:
        # XYZ pair, common for resources
        return {
            "x": ue_coords[0],
            "y": ue_coords[1],
            "z": ue_coords[2],
            "lat": lat.from_units(ue_coords[1]),
            "long": long.from_units(ue_coords[0])
        }

    # min[XY]max[XY] flat pair
    long_start = long.from_units(ue_coords[0])
    lat_start = lat.from_units(ue_coords[1])
    long_end = long.from_units(ue_coords[2])
    lat_end = lat.from_units(ue_coords[3])
    return {
        "latStart": lat_start,
        "longStart": long_start,
        "latEnd": lat_end,
        "longEnd": long_end,
        "latCenter": (lat_end+lat_start) / 2,
        "longCenter": (long_end+long_start) / 2,
    }
