from dataclasses import InitVar, dataclass, field
from logging import NullHandler, getLogger
from typing import Any, Dict, List, Optional, Union

from ue.asset import UAsset
from ue.loader import AssetLoader, AssetNotFound
from ue.properties import (ArrayProperty, FloatProperty, StringProperty,
                           StructProperty)

logger = getLogger(__name__)
logger.addHandler(NullHandler())


@dataclass
class SpawnGroupEntry:
    _struct: InitVar[StructProperty]

    name: StringProperty = field(init=False)
    chance: Union[float, FloatProperty] = 0.0
    weight: Union[float, FloatProperty] = 1.0
    npcsToSpawn: List[str] = field(default_factory=lambda: [])
    npcsSpawnOffsets: List[Dict[str,Any]] = field(default_factory=lambda: [])
    npcsToSpawnPercentageChance: List[float] = field(default_factory=lambda: [])
    npcMinLevelOffset: List[float] = field(default_factory=lambda: [])
    npcMaxLevelOffset: List[float] = field(default_factory=lambda: [])

    def __post_init__(self, _struct):
        data = _struct.as_dict()
        self.name = data['AnEntryName']
        self.weight = data['EntryWeight']
        self.npcsToSpawn = data['NPCsToSpawn']
        self.npcsSpawnOffsets = [{'x': offset.x.value, 'y': offset.y.value, 'z': offset.z.value} for offset in data['NPCsSpawnOffsets'].values]
        self.npcsToSpawnPercentageChance = data['NPCsToSpawnPercentageChance']
        self.npcMinLevelOffset = data['NPCMinLevelOffset']
        self.npcMaxLevelOffset = data['NPCMaxLevelOffset']

    def format_for_json(self):
        data = {}
        for field_name in self.__annotations__: # pylint:disable=E1101
            field_value = getattr(self, field_name, None)
            if not field_value:
                continue
            data[field_name] = field_value
        return data


@dataclass
class SpawnGroupLimitEntry:
    _struct: InitVar[StructProperty]

    npcClass: str = field(init=False)
    maxPercentageOfDesiredNumToAllow: float = 1.0

    def __post_init__(self, _struct):
        data = _struct.as_dict()
        self.npcClass = data['NPCClass']
        self.maxPercentageOfDesiredNumToAllow = getattr(data, 'MaxDesiredNumEnemiesMultiplier', 1.0)

    def format_for_json(self):
        return {'path': self.npcClass, 'maxPercentageOfDesiredNumToAllow': self.maxPercentageOfDesiredNumToAllow}


@dataclass
class SpawnGroupObject:
    blueprintPath: str
    maxDesiredNumEnemiesMultiplier: float = 1.0
    entries: List[SpawnGroupEntry] = field(default_factory=lambda: [])
    limits: List[SpawnGroupLimitEntry] = field(default_factory=lambda: [])

    def calculate_chances(self):
        weight_sum = sum([entry.weight for entry in self.entries])
        
        if not weight_sum:
            #logger.debug(f'Sum of entry weights in {self.blueprintPath} is zero.')
            return

        for entry in self.entries:
            entry.chance = entry.weight / weight_sum
        self.entries.sort(key=lambda entry: entry.chance, reverse=True)

    def as_dict(self):
        return {
            "path": self.blueprintPath,
            "maxDesiredNumEnemiesMultiplier": self.maxDesiredNumEnemiesMultiplier,
            "entries": self.entries,
            "limits": self.limits
        }
    
    def format_for_json(self):
        return self.as_dict()


def gather_spawn_entries(asset: UAsset):
    properties = asset.properties.as_dict()
    entries = properties["NPCSpawnEntries"]
    if not entries:
        # TODO: Support inherited NPCSpawnEntries
        logger.debug(f'TODO: {asset.name} does not have any spawn entries. They are probably inherited.')
        return

    for entry in entries[0].values:
        yield SpawnGroupEntry(entry)


def gather_limit_entries(asset: UAsset):
    properties = asset.properties.as_dict()
    entries = properties["NPCSpawnLimits"]
    if not entries:
        if not properties["NPCSpawnEntries"]:
            logger.debug(f'TODO:{asset.name} does not have any limit entries. They are probably inherited.')
        return

    for entry in entries[0].values:
        yield SpawnGroupLimitEntry(entry)


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

    group_object = SpawnGroupObject(full_asset_name, max_desired_enemy_num_mult, entries, limits)
    group_object.calculate_chances()
    return group_object
