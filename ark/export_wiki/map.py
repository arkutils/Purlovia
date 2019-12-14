from dataclasses import dataclass, field

from .geo import GeoCoordCalculator


@dataclass
class MapInfo:
    name: str
    world_settings: dict = field(init=False)
    data: dict
    # Persistent level data
    persistent_level: str = field(init=False)
    lat: GeoCoordCalculator = field(init=False)
    long: GeoCoordCalculator = field(init=False)


@dataclass
class WorldData:
    npcRandomSpawnClassWeights: list = field(default_factory=lambda: [])
    spawnGroups: list = field(default_factory=lambda: [])
    wyvernNests: list = field(default_factory=lambda: [])
    iceWyvernNests: list = field(default_factory=lambda: [])
    drakeNests: list = field(default_factory=lambda: [])
    deinonychusNests: list = field(default_factory=lambda: [])
        #if getattr(self.world_settings, 'NPCRandomSpawnClassWeights', None):
        #    self.npcRandomSpawnClassWeights = [{
        #        'from': data.get_property('FromClass'),
        #        'to': data.get_property('ToClasses'),
        #        'chances': data.get_property('Weights')
        #    } for data in self.world_settings.NPCRandomSpawnClassWeights[0].values]
