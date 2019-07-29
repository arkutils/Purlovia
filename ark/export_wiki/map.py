from dataclasses import dataclass, field

from ark.export_wiki.geo import GeoData, gather_geo_data
from ue.asset import UAsset


@dataclass
class MapData:
    name: str
    latitude: GeoData
    longitude: GeoData
    held_map_empty: str = ''
    held_map: str = ''
    map_empty: str = ''
    big_map: str = ''
    small_map: str = ''
    max_difficulty: float = 5.0  # Needs default value verification

    npc_random_spawn_class_weights: list = field(default_factory=lambda: [])
    loot_crates: list = field(default_factory=lambda: [])
    biomes: list = field(default_factory=lambda: [])
    spawns: list = field(default_factory=lambda: [])
    spawn_groups: dict = field(default_factory=lambda: {})

    def as_dict(self):
        return {
            'latitudeOrigin': self.latitude.origin,
            'longitudeOrigin': self.longitude.origin,
            'latitudeScale': self.latitude.scale,
            'longitudeScale': self.longitude.scale,
            'latitudeShift': self.latitude.shift,
            'longitudeShift': self.longitude.shift,
            'latitudeMulti': self.latitude.multiplier,
            'longitudeMulti': self.longitude.multiplier,
            'heldMapEmpty': self.held_map_empty,
            'heldMap': self.held_map,
            'mapEmpty': self.map_empty,
            'bigMap': self.big_map,
            'smallMap': self.small_map,
            'difficultyMax': self.max_difficulty,
            'npcRandomSpawnClassWeights': self.npc_random_spawn_class_weights,
            'lootCrates': self.loot_crates,
            'biomes': self.biomes,
            'spawns': self.spawns,
            'spawnGroups': list(self.spawn_groups.values()),
        }


def find_world_settings(level: UAsset) -> dict:
    # Some maps have misnamed PrimalWorldSettings export
    # and that prevents usage of AssetLoader.load_class.
    for export in level.exports:
        print(str(export.name))
        if str(export.klass.value.name) == 'PrimalWorldSettings':
            return export.properties.as_dict()
    #return level.loader.load_class(level.assetname + '.PrimalWorldSettings').properties.as_dict()


def get_settings_from_map(asset: UAsset):
    world_settings = find_world_settings(asset)
    latitude, longitude = gather_geo_data(asset, world_settings=world_settings)
    map_data = MapData(str(asset.default_class.name), latitude, longitude)
    if world_settings['Title']:
        map_data.name = str(world_settings['Title'][0].value)
    if world_settings['OverrideDifficultyMax']:
        map_data.max_difficulty = world_settings['OverrideDifficultyMax'][0].value

    if world_settings['OverrideWeaponMapTextureEmpty']:
        map_data.held_map_empty = str(world_settings['OverrideWeaponMapTextureEmpty'][0].value.value.name)
    if world_settings['OverrideWeaponMapTextureFilled']:
        map_data.held_map = str(world_settings['OverrideWeaponMapTextureFilled'][0].value.value.name)
    if world_settings['OverrideUIMapTextureEmpty']:
        map_data.map_empty = str(world_settings['OverrideUIMapTextureEmpty'][0].value.value.name)
    if world_settings['OverrideUIMapTextureFilled']:
        map_data.big_map = str(world_settings['OverrideUIMapTextureFilled'][0].value.value.name)
    if world_settings['OverrideUIMapTextureSmall']:
        map_data.small_map = str(world_settings['OverrideUIMapTextureSmall'][0].value.value.name)

    return map_data
