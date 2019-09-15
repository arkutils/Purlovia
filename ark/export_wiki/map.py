from dataclasses import InitVar, dataclass, field

from ue.asset import UAsset
from ue.gathering import gather_properties

from .common import proxy_properties_as_dict
from .geo import GeoData, gather_geo_data
from .types import WORLD_SETTINGS_EXPORTED_PROPERTIES, PrimalWorldSettings


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
    gasVeins: list = field(default_factory=lambda: [])
    chargeNodes: list = field(default_factory=lambda: [])
    plantZNodes: list = field(default_factory=lambda: [])
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
        if not self.world_settings:
            raise RuntimeError(f'PrimalWorldSettings could not have been found in "{_level.assetname}".')

        if str(self.world_settings.Title[0]):
            self.name = str(self.world_settings.Title[0])
        else:
            self.name = str(_level.default_class.name)
        self.name = self.name.rstrip('_C').rstrip('_P')

        self.latitude, self.longitude = gather_geo_data(self.world_settings)
        if getattr(self.world_settings, 'NPCRandomSpawnClassWeights', None):
            self.npcRandomSpawnClassWeights = [
                {
                    'from': data.get_property('FromClass'),
                    'to': data.get_property('ToClasses'),
                    'chances': data.get_property('Weights')
                } for data in self.world_settings.NPCRandomSpawnClassWeights[0].values
            ]

    def format_for_json(self):
        data = dict(
            **{f'lat{key}': value for key, value in self.latitude.format_for_json().items()},
            **{f'long{key}': value for key, value in self.longitude.format_for_json().items()},
            **proxy_properties_as_dict(self.world_settings, key_list=WORLD_SETTINGS_EXPORTED_PROPERTIES)
        )
        for field_name, field_type in self.__annotations__.items(): # pylint:disable=E1101
            if field_type is list and getattr(self, field_name):
                data[field_name] = getattr(self, field_name)
        return data
