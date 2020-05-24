from typing import List, Optional, Tuple, Union

from automate.hierarchy_exporter import ExportModel, Field, ModelConfig
from export.wiki.models import MinMaxRange
from ue.properties import BoolProperty, FloatProperty, IntProperty, NameProperty, ObjectProperty, StringProperty

__all__ = [
    # Common
    'ObjectPath',
    'Location',
    'Box',
    'WeighedBox',
    'WeighedClassSwap',
    # Export Models
    'Actor',
    'InGameMapTextureSet',
    'WorldSettings',
    'NPCManager',
    'BiomeTempWindSettings',
    'Biome',
    'SupplyCrateSpawn',
    'PainVolume',
    'PlayerSpawn',
    'MissionDispatcher',
    'ExplorerNote',
    'Glitch'
]

## Common Structure Models

ObjectPath = Optional[str]


class Location(ExportModel):
    x: Union[float, FloatProperty]
    y: Union[float, FloatProperty]
    z: Union[float, FloatProperty]
    lat: Optional[float]
    long: Optional[float]


class Box(ExportModel):
    start: Location
    center: Location
    end: Location


class WeighedBox(ExportModel):
    weight: FloatProperty
    start: Location
    center: Location
    end: Location


class WeighedClassSwap(ExportModel):
    # TODO: Possibly move into export.wiki.models after spawn_groups are moved
    from_: ObjectPath = Field(alias='from')
    exact: BoolProperty
    to: List[Optional[ObjectPath]]
    weights: List[FloatProperty]
    during: str = 'None'


## Export Models


class Actor(ExportModel):
    hidden: bool = False
    x: FloatProperty
    y: FloatProperty
    z: FloatProperty
    lat: Optional[float]
    long: Optional[float]


class InGameMapTextureSet(ExportModel):
    held: Optional[ObjectPath]
    emptyHeld: Optional[ObjectPath]
    empty: Optional[ObjectPath]
    big: Optional[ObjectPath]
    small: Optional[ObjectPath]


class WorldSettings(ExportModel):
    source: Optional[str]
    name: Union[StringProperty, str]

    # Geo
    latOrigin: FloatProperty
    longOrigin: FloatProperty
    latScale: FloatProperty
    longScale: FloatProperty
    # Not filled in during gathering
    latMulti: Optional[float]
    longMulti: Optional[float]
    latShift: Optional[float]
    longShift: Optional[float]

    # Gameplay Settings
    maxDifficulty: FloatProperty
    mapTextures: InGameMapTextureSet
    ## Spawn Settings
    onlyEventGlobalSwaps: bool = False
    randomNPCClassWeights: List[WeighedClassSwap]
    ## Uploads
    allowedDinoDownloads: List[ObjectPath]


class NPCManager(ExportModel):
    disabled: bool = False
    spawnGroup: ObjectPath
    minDesiredNumberOfNPC: IntProperty
    neverSpawnInWater: BoolProperty
    forceUntameable: BoolProperty

    # Zones
    locations: List[Box] = []
    spawnLocations: List[WeighedBox] = []
    spawnPoints: List[Location] = []


class BiomeTempWindSettings(ExportModel):
    override: Optional[FloatProperty]
    range: Optional[MinMaxRange] = Field(description="Only applies to Temperature.")
    preOffset: Optional[Tuple[None, FloatProperty, FloatProperty, FloatProperty]] = Field(
        description="Applied before other offsets. No threshold, only multiplier, exponent, and addition (order of fields).")
    aboveOffset: Optional[Tuple[FloatProperty, FloatProperty, FloatProperty, None]] = Field(
        description=
        "Applied only if previous calculation is greater than threshold. Only threshold, multiplier, and exponent (order of fields)."
    )
    belowOffset: Optional[Tuple[FloatProperty, FloatProperty, FloatProperty, None]] = Field(
        description=
        "Applied only if previous calculation is lower than threshold. Only threshold, multiplier, and exponent (order of fields)."
    )
    final: Optional[Tuple[None, FloatProperty, FloatProperty, FloatProperty]] = Field(
        description=
        "Applied after all other calculations. No threshold, only multiplier, exponent, and addition (order of fields).")

    class Config(ModelConfig):
        arbitrary_types_allowed = True


class Biome(ExportModel):
    name: str
    priority: IntProperty
    isOutside: BoolProperty
    preventCrops: BoolProperty
    temperature: Optional[BiomeTempWindSettings] = None
    wind: Optional[BiomeTempWindSettings] = None
    boxes: List[Box] = []


class SupplyCrateSpawn(ExportModel):
    maxCrateNumber: IntProperty
    crateClasses: List[ObjectPath]
    crateLocations: List[Location]
    minTimeBetweenSpawnsAtSamePoint: FloatProperty
    delayBeforeFirst: MinMaxRange
    intervalBetweenSpawns: MinMaxRange
    intervalBetweenMaxedSpawns: MinMaxRange
    intervalBetweenSpawnsSP: Optional[MinMaxRange] = None
    intervalBetweenMaxedSpawnsSP: Optional[MinMaxRange] = None


class PainVolume(Box):
    immune: List[ObjectPath]


class PlayerSpawn(ExportModel):
    regionId: IntProperty

    x: FloatProperty
    y: FloatProperty
    z: FloatProperty
    lat: Optional[float]
    long: Optional[float]


class MissionDispatcher(ExportModel):
    type_: str = Field(alias="type")
    missions: List[ObjectPath]

    x: FloatProperty
    y: FloatProperty
    z: FloatProperty
    lat: Optional[float]
    long: Optional[float]


class ExplorerNote(ExportModel):
    noteIndex: IntProperty
    hidden: bool = False

    x: FloatProperty
    y: FloatProperty
    z: FloatProperty
    lat: Optional[float]
    long: Optional[float]


class Glitch(ExportModel):
    noteId: Optional[IntProperty]
    hidden: bool = False
    hexagons: IntProperty

    x: FloatProperty
    y: FloatProperty
    z: FloatProperty
    lat: Optional[float]
    long: Optional[float]
