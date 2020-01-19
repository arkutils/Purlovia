from dataclasses import dataclass, field

from .geo import GeoCoordCalculator


@dataclass
class MapInfo:
    data: dict
    # Persistent level data
    persistent_level: str = field(init=False)
    lat: GeoCoordCalculator = field(init=False)
    long: GeoCoordCalculator = field(init=False)
