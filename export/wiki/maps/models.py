from typing import List, Optional, Union

from automate.hierarchy_exporter import ExportModel, Field
from ue.properties import FloatProperty, NameProperty, ObjectProperty, StringProperty

__all__ = [
    'Location',
]

## Common Structure Models

ObjectPath = Optional[str]


class Location(ExportModel):
    x: FloatProperty
    y: FloatProperty
    z: FloatProperty
    lat: Optional[float]
    long: Optional[float]


class Box(ExportModel):
    start: Location
    center: Location
    end: Location


class WeighedClassSwap(ExportModel):
    # TODO: Possibly move into export.wiki.models after spawn_groups are moved
    from_: ObjectPath = Field(alias='from')
    exact: bool
    to: List[Optional[ObjectPath]]
    weights: List[FloatProperty]
    during: Optional[NameProperty]


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
