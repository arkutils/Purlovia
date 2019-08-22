from dataclasses import InitVar, dataclass, field
from logging import NullHandler, getLogger

from ark.export_wiki.geo import GeoData, gather_geo_data
from ark.export_wiki.types import (WORLD_SETTINGS_EXPORTED_PROPERTIES,
                                   PrimalWorldSettings)
from ark.export_wiki.utils import export_properties_from_proxy
from ue.asset import UAsset
from ue.gathering import gather_properties

logger = getLogger(__name__)
logger.addHandler(NullHandler())

@dataclass
class WorldData:
    _level: InitVar[UAsset]

    name: str = field(init=False)
    world_settings: PrimalWorldSettings = field(init=False)
    latitude: GeoData = field(init=False)
    longitude: GeoData = field(init=False)

    random_spawn_classes: list = field(default_factory=lambda: [])
    loot_crates: list = field(default_factory=lambda: [])
    biomes: list = field(default_factory=lambda: [])

    water_veins: list = field(default_factory=lambda: [])
    oil_veins: list = field(default_factory=lambda: [])

    spawns: list = field(default_factory=lambda: [])
    spawn_groups: list = field(default_factory=lambda: [])

    def __post_init__(self, _level):
        # Some maps have misnamed PrimalWorldSettings export
        # and that prevents usage of AssetLoader.load_class.
        for export in _level.exports:
            if str(export.klass.value.name) == 'PrimalWorldSettings':
                self.world_settings = gather_properties(export)
                break
        else:
            raise RuntimeError(f'PrimalWorldSettings could not have been found in "{_level.assetname}".')

        if str(self.world_settings.Title[0]):
            self.name = str(self.world_settings.Title[0])
        else:
            self.name = str(_level.default_class.name)
        self.name = self.name.rstrip('_C').rstrip('_P')
        self.latitude, self.longitude = gather_geo_data(self.world_settings)

    def format_for_json(self):
        data = {}
        data.update({f'latitude{key}': value for key, value in self.latitude.format_for_json().items()})
        data.update({f'longitude{key}': value for key, value in self.longitude.format_for_json().items()})
        data.update(export_properties_from_proxy(self.world_settings, WORLD_SETTINGS_EXPORTED_PROPERTIES))
        data.update({
            'npcRandomSpawnClassWeights': self.random_spawn_classes,
            'lootCrates': self.loot_crates,
            'biomes': self.biomes,
            'oilVeins': self.oil_veins,
            'waterVeins': self.water_veins,
            'spawns': self.spawns,
            'spawnGroups': self.spawn_groups,
        })
        return data
