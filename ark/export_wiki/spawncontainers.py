from dataclasses import dataclass, field
from logging import NullHandler, getLogger
from typing import Any, Dict, List, Optional

from ue.asset import UAsset
from ue.loader import AssetLoader, AssetNotFound
from ue.properties import ArrayProperty, StringProperty

logger = getLogger(__name__)
logger.addHandler(NullHandler())


@dataclass
class SpawnGroupEntry:
    name: StringProperty
    chance: float = 0.0
    weight: float = 1.0
    npcsToSpawn: List[str] = field(default_factory=lambda: [])
    npcsSpawnOffsets: List[Dict[str,Any]] = field(default_factory=lambda: [])
    npcsToSpawnPercentageChance: List[float] = field(default_factory=lambda: [])
    npcMinLevelOffset: List[float] = field(default_factory=lambda: [])
    npcMaxLevelOffset: List[float] = field(default_factory=lambda: [])

    def format_for_json(self):
        data = {}
        for field_name in self.__annotations__: # pylint:disable=E1101
            field_value = getattr(self, field_name)
            if not field_value or isinstance(field_value, ArrayProperty) and not field_value.values:
                continue
            data[field_name] = field_value
        return data


@dataclass
class SpawnGroupLimitEntry:
    npcClass: str
    maxPercentageOfDesiredNumToAllow: float = 1.0

    def format_for_json(self):
        return {'path': self.npcClass, 'maxPercentageOfDesiredNumToAllow': self.maxPercentageOfDesiredNumToAllow}


@dataclass
class SpawnGroupObject:
    blueprintPath: str
    maxDesiredNumEnemiesMultiplier: float = 1.0
    entries: List[SpawnGroupEntry] = field(default_factory=lambda: [])
    limits: List[SpawnGroupLimitEntry] = field(default_factory=lambda: [])

    def as_dict(self):
        return {
            "path": self.blueprintPath,
            "maxDesiredNumEnemiesMultiplier": self.maxDesiredNumEnemiesMultiplier,
            "entries": self.entries,
            "limits": self.limits
        }


def gather_spawn_entries(asset: UAsset):
    properties = asset.properties.as_dict()
    entries = properties["NPCSpawnEntries"]
    if not entries:
        # TODO: Support inherited NPCSpawnEntries
        logger.debug(f'TODO: {asset.name} does not have any spawn entries. They are probably inherited.')
        return

    for entry in entries[0].values:
        entry_data = entry.as_dict()
        entry_object = SpawnGroupEntry(entry_data['AnEntryName'])
        entry_object.weight = entry_data['EntryWeight']
        entry_object.npcsToSpawn = entry_data['NPCsToSpawn']
        entry_object.npcsSpawnOffsets = [{'x': offset.x.value, 'y': offset.y.value, 'z': offset.z.value}
                                           for offset in entry_data['NPCsSpawnOffsets'].values]
        entry_object.npcsToSpawnPercentageChance = entry_data['NPCsToSpawnPercentageChance']
        entry_object.npcMinLevelOffset = entry_data['NPCMinLevelOffset']
        entry_object.npcMaxLevelOffset = entry_data['NPCMaxLevelOffset']
        yield entry_object


def gather_limit_entries(asset: UAsset):
    properties = asset.properties.as_dict()
    entries = properties["NPCSpawnLimits"]
    if not entries:
        if not properties["NPCSpawnEntries"]:
            logger.debug(f'TODO:{asset.name} does not have any limit entries. They are probably inherited.')
        return

    for entry in entries[0].values:
        entry_data = entry.as_dict()
        entry_object = SpawnGroupLimitEntry(entry_data['NPCClass'])
        if 'MaxDesiredNumEnemiesMultiplier' in entry_data:
            entry_object.maxPercentageOfDesiredNumToAllow = entry_data['MaxDesiredNumEnemiesMultiplier'].value
        yield entry_object


def get_spawn_entry_container_data(loader: AssetLoader, full_asset_name: str) -> Optional[SpawnGroupObject]:
    asset_name = full_asset_name
    if '.' in asset_name:
        asset_name = asset_name[:asset_name.index('.')]
    try:
        asset = loader[asset_name]
    except AssetNotFound:
        #logger.debug(f'Spawn entry container {full_asset_name} is referenced but missing.')
        return None

    container_data = asset.default_export
    properties = container_data.properties.as_dict()
    max_desired_enemy_num_mult = 1.0
    if "MaxDesiredNumEnemiesMultiplier" in properties:
        max_desired_enemy_num_mult = properties["MaxDesiredNumEnemiesMultiplier"][0].value

    entries = list(gather_spawn_entries(container_data))
    limits = list(gather_limit_entries(container_data))
    #del loader[asset_name]

    weight_sum = sum([entry.weight for entry in entries])
    for entry in entries:
        entry.chance = entry.weight / weight_sum
    entries.sort(key=lambda entry: entry.chance, reverse=True)

    return SpawnGroupObject(full_asset_name, max_desired_enemy_num_mult, entries, limits)
