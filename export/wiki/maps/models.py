from typing import List, Optional, Tuple, Union

from automate.hierarchy_exporter import ExportModel, Field
from export.wiki.models import MinMaxRange
from ue.properties import BoolProperty, FloatProperty, IntProperty, StringProperty

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

# Common Structure Models

ObjectPath = Optional[str]
FloatLike = Union[FloatProperty, float, int]


class Location(ExportModel):
    x: FloatLike
    y: FloatLike
    z: FloatLike
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
    from_class: Optional[ObjectPath] = Field(alias="from")
    exact: bool = Field(False, title="Match class exactly")
    to: List[Optional[ObjectPath]]
    weights: List[FloatProperty]
    during: str = Field('None', title="Event the rule is active in")


# Export Models


class Actor(ExportModel):
    hidden: bool = False
    x: FloatLike
    y: FloatLike
    z: FloatLike
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
    latOrigin: FloatProperty = Field(
        title="Latitude Origin",
        description="World origin of Y axis, used by the in-game map, in centimeters.",
    )
    longOrigin: FloatProperty = Field(
        title="Longitude Origin",
        description="World origin of X axis, used by the in-game map, in centimeters.",
    )
    latScale: FloatProperty = Field(
        title="Latitude Scale",
        description="Height of the map, used by the in-game map, in tens of meters.",
    )
    longScale: FloatProperty = Field(
        title="Longitude Scale",
        description="Width of the map, used by the in-game map, in tens of meters.",
    )
    latMulti: Optional[FloatLike] = Field(
        title="Latitude Multiplier",
        description="Latitude scale in meters. Divide centimeter distance from Y axis by this value.",
    )
    longMulti: Optional[FloatLike] = Field(
        title="Longitude Multiplier",
        description="Longitude scale in meters. Divide centimeter distance from X axis by this value",
    )
    latShift: Optional[FloatLike] = Field(
        title="Latitude Shift",
        description="Shift of coordinates on the Y axis.",
    )
    longShift: Optional[FloatLike] = Field(
        title="Longitude Shift",
        description="Shift of coordinates on the X axis.",
    )

    # Gameplay Settings
    maxDifficulty: FloatProperty
    mapTextures: InGameMapTextureSet = Field(
        ...,
        description="Preview textures of the map. Weapon refers to the map player can hold.",
    )
    # Spawn Settings
    onlyEventGlobalSwaps: bool = Field(
        False,
        description="Controls whether Primal Game Data's random non-event class replacements are allowed.",
    )
    randomNPCClassWeights: List[WeighedClassSwap] = []
    # Uploads
    allowedDinoDownloads: List[ObjectPath] = []


class Trade(ExportModel):
    bp: str
    item: str
    qty: IntProperty
    cost: IntProperty


class NPCManager(ExportModel):
    disabled: bool = False
    spawnGroup: ObjectPath = Field(description="Path to a container of spawning groups.")
    minDesiredNumberOfNPC: IntProperty
    neverSpawnInWater: BoolProperty
    forceUntameable: BoolProperty

    # Zones
    locations: List[Box] = Field(
        [],
        title="Counting volumes",
    )
    spawnLocations: List[WeighedBox] = Field([], title="Spawning volumes")
    spawnPoints: List[Location] = []


EnvironmentalOffset = Tuple[FloatProperty, FloatProperty, FloatProperty]
EnvironmentalOffsetRelativeDesc = 'Fields: threshold, multiplier and exponent.'
EnvironmentalOffsetAbsoluteDesc = 'Fields: multiplier, exponent, addition.'


class BiomeTempWindSettings(ExportModel):
    override: Optional[FloatProperty]
    range: Optional[MinMaxRange] = Field(
        None,
        description="Only applies to Temperature.",
    )

    initial: Optional[EnvironmentalOffset] = Field(
        None,
        description=f"Applied before other offsets. {EnvironmentalOffsetAbsoluteDesc}",
    )
    above: Optional[EnvironmentalOffset] = Field(
        None,
        description=f"Applied only if previous calculation is greater than threshold. {EnvironmentalOffsetRelativeDesc}",
    )
    below: Optional[EnvironmentalOffset] = Field(
        None,
        description=f"Applied only if previous calculation is lower than threshold. {EnvironmentalOffsetRelativeDesc}",
    )
    final: Optional[EnvironmentalOffset] = Field(
        None,
        description=f"Applied after all other calculations. {EnvironmentalOffsetAbsoluteDesc}",
    )


class Biome(ExportModel):
    name: str
    priority: IntProperty
    isOutside: BoolProperty
    preventCrops: BoolProperty
    temperature: BiomeTempWindSettings = BiomeTempWindSettings()
    wind: BiomeTempWindSettings = BiomeTempWindSettings()
    boxes: List[Box] = []


class SupplyCrateSpawn(ExportModel):
    maxCrateNumber: IntProperty
    crateClasses: List[ObjectPath]
    crateLocations: List[Location]
    minTimeBetweenSpawnsAtSamePoint: FloatProperty
    delayBeforeFirst: MinMaxRange
    intervalBetweenSpawns: MinMaxRange
    intervalBetweenMaxedSpawns: MinMaxRange
    intervalBetweenSpawnsSP: Optional[MinMaxRange] = Field(
        None,
        description="Single-player override of intervalBetweenSpawns.",
    )
    intervalBetweenMaxedSpawnsSP: Optional[MinMaxRange] = Field(
        None,
        description="Single-player override of intervalBetweenMaxedSpawns.",
    )


class PainVolume(Box):
    immune: List[ObjectPath] = Field([], title="Explicitly immune species")


class PlayerSpawn(ExportModel):
    regionId: IntProperty = Field(description="ID of an element of region definitions list located in PGD or PWS.", )

    x: FloatLike
    y: FloatLike
    z: FloatLike
    lat: Optional[float]
    long: Optional[float]


class MissionDispatcher(ExportModel):
    type_: Union[str, int] = Field(
        alias="type",
        description="Friendly mission type name, or internal ID if unknown.",
    )
    missions: List[ObjectPath]

    x: FloatProperty
    y: FloatProperty
    z: FloatProperty
    lat: Optional[float]
    long: Optional[float]


class ExplorerNote(ExportModel):
    noteIndex: IntProperty = Field(description="Index of an explorer note entry from Primal Game Data.", )
    hidden: bool = False

    x: FloatProperty
    y: FloatProperty
    z: FloatProperty
    lat: Optional[float]
    long: Optional[float]


class Glitch(ExportModel):
    noteId: Optional[IntProperty] = Field(description="Index of an explorer note entry from Primal Game Data.", )
    hidden: bool = False
    hexagons: IntProperty

    x: FloatProperty
    y: FloatProperty
    z: FloatProperty
    lat: Optional[float]
    long: Optional[float]


# Actor-based Models
class OilVein(Actor):
    ...


class WaterVein(Actor):
    ...


class WyvernNest(Actor):
    ...


class ChargeNode(Actor):
    ...


class GasVein(Actor):
    ...


class DrakeNest(Actor):
    ...


class PlantSpeciesZWild(Actor):
    ...


class IceWyvernNest(Actor):
    ...


class DeinonychusNest(Actor):
    ...


class OilVent(Actor):
    ...


class LunarOxygenVent(Actor):
    ...


class MagmasaurNest(Actor):
    ...


class PoisonTree(Actor):
    ...
