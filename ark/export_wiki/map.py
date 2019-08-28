from dataclasses import InitVar, dataclass, field
from logging import NullHandler, getLogger

from ue.asset import UAsset
from ue.gathering import gather_properties

from .geo import GeoData, gather_geo_data
from .types import WORLD_SETTINGS_EXPORTED_PROPERTIES, PrimalWorldSettings
from .utils import export_properties_from_proxy

logger = getLogger(__name__)
logger.addHandler(NullHandler())

@dataclass
class WorldData:
    _level: InitVar[UAsset]

    name: str = field(init=False)
    world_settings: PrimalWorldSettings = field(init=False)
    latitude: GeoData = field(init=False)
    longitude: GeoData = field(init=False)

    npcRandomSpawnClassWeights: list = field(default_factory=lambda: [])
    radiationVolumes: list = field(default_factory=lambda: [])
    lootCrates: list = field(default_factory=lambda: [])
    biomes: list = field(default_factory=lambda: [])
    spawns: list = field(default_factory=lambda: [])
    spawnGroups: list = field(default_factory=lambda: [])
    # Veins & Nests
    waterVeins: list = field(default_factory=lambda: [])
    oilVeins: list = field(default_factory=lambda: [])
    wyvernNests: list = field(default_factory=lambda: [])
    iceWyvernNests: list = field(default_factory=lambda: [])
    drakeNests: list = field(default_factory=lambda: [])
    deinonychusNests: list = field(default_factory=lambda: [])

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
        for field_name, field_type in self.__annotations__.items(): # pylint:disable=E1101
            if field_type is list and getattr(self, field_name):
                data[field_name] = getattr(self, field_name)
        return data
