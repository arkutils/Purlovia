from typing import Any, Dict, Iterable, List, Optional, Tuple, Type, Union

from ue.asset import ExportTableItem
from ue.base import UEBase
from ue.hierarchy import MissingParent, inherits_from
from ue.loader import AssetLoadException
from ue.properties import ArrayProperty, Vector
from ue.proxy import UEProxyStructure

from .base import MapGathererBase
from .common import convert_box_bounds_for_export, get_actor_location_vector, get_volume_bounds, get_volume_box_count
from .consts import ACTOR_CLS, BIOME_ZONE_VOLUME_CLS, CHARGE_NODE_CLS, CUSTOM_ACTOR_LIST_CLS, DAMAGE_TYPE_RADIATION_PKG, \
    EXPLORER_CHEST_BASE_CLS, GAS_VEIN_CLS, NPC_ZONE_MANAGER_CLS, OIL_VEIN_CLS, PRIMAL_WORLD_SETTINGS_CLS, \
    SUPPLY_CRATE_SPAWN_VOLUME_CLS, TOGGLE_PAIN_VOLUME_CLS, WATER_VEIN_CLS, WILD_PLANT_SPECIES_Z_CLS
from .map import MapInfo
from .types import BiomeZoneVolume, CustomActorList, ExplorerNote, NPCZoneManager, \
    PrimalWorldSettings, SupplyCrateSpawningVolume, TogglePainVolume


class GenericActorExport(MapGathererBase):
    KLASS: str
    CATEGORY: str

    @classmethod
    def get_category_name(cls) -> str:
        return cls.CATEGORY

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, cls.KLASS)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Iterable[Union[UEBase, Dict[str, Any]]]:
        yield get_actor_location_vector(proxy)

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        data['lat'] = map_info.lat.from_units(data['y'])
        data['long'] = map_info.long.from_units(data['x'])

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Tuple[Any, ...]:
        return (data['x'], data['y'], data['z'])


class GenericActorListExport(MapGathererBase):
    TAGS: Tuple[str, ...]
    CATEGORY: str

    @classmethod
    def get_category_name(cls) -> str:
        return cls.CATEGORY

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        if inherits_from(export, CUSTOM_ACTOR_LIST_CLS):
            # Check the tag
            tag = export.properties.get_property('CustomTag', fallback='')
            if str(tag) in cls.TAGS:
                return True
        return False

    @classmethod
    def extract(cls, proxy: CustomActorList) -> Iterable[Union[UEBase, Dict[str, Any]]]: # type:ignore
        for actor in proxy.ActorList[0].values:
            if not actor.value.value:
                continue
            
            yield get_actor_location_vector(actor.value.value)


    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        data['lat'] = map_info.lat.from_units(data['y'])
        data['long'] = map_info.long.from_units(data['x'])

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Tuple[Any, ...]:
        return (data['x'], data['y'], data['z'])

class WorldSettingsExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'worldSettings'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, PRIMAL_WORLD_SETTINGS_CLS) and not getattr(export.asset, 'tile_info', None)

    @classmethod
    def extract(cls, proxy: PrimalWorldSettings) -> Iterable[Dict[str, Any]]: # type:ignore
        yield dict(
            name=proxy.Title[0],
            # Geo
            latOrigin=proxy.LatitudeOrigin[0],
            longOrigin=proxy.LongitudeOrigin[0],
            latScale=proxy.LatitudeScale[0],
            longScale=proxy.LongitudeScale[0],
            # These fields will be filled out during data conversion
            latMulti=0,
            longMulti=0,
            latShift=0,
            longShift=0,
            # Extra data
            maxDifficulty=proxy.OverrideDifficultyMax[0],
            mapTextures=dict(
                held=proxy.OverrideWeaponMapTextureFilled[0] if 'OverrideWeaponMapTextureFilled' in proxy else None,
                emptyHeld=proxy.OverrideWeaponMapTextureEmpty[0] if 'OverrideWeaponMapTextureEmpty' in proxy else None,
                empty=proxy.OverrideUIMapTextureEmpty[0] if 'OverrideUIMapTextureEmpty' in proxy else None,
                big=proxy.OverrideUIMapTextureFilled[0] if 'OverrideUIMapTextureFilled' in proxy else None,
                small=proxy.OverrideUIMapTextureSmall[0] if 'OverrideUIMapTextureSmall' in proxy else None,
            ),
            allowedDinoDownloads=proxy.AllowDownloadDinoClasses[0] if 'AllowDownloadDinoClasses' in proxy else None
        )

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        pass

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Tuple[Any, ...]:
        return (1, )

class NPCZoneManagerExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'spawns'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, NPC_ZONE_MANAGER_CLS)

    @classmethod
    def extract(cls, proxy: NPCZoneManager) -> Iterable[Dict[str, Any]]: # type:ignore
        # Sanity checks
        if not getattr(proxy, 'NPCSpawnEntriesContainerObject', None) or not proxy.NPCSpawnEntriesContainerObject[0].value.value or not getattr(proxy, 'LinkedZoneVolumes', None):
            yield from ()
            return

        # Export properties
        data: Dict[str, Union[UEBase, List]] = dict(
            spawnGroup=proxy.NPCSpawnEntriesContainerObject[0],
            minDesiredNumberOfNPC=proxy.MinDesiredNumberOfNPC[0],
            neverSpawnInWater=proxy.bNeverSpawnInWater[0],
            forceUntameable=proxy.bForceUntameable[0]
        )
        # Export dino counting regions
        data['locations'] = list(cls._extract_counting_volumes(proxy.LinkedZoneVolumes[0]))
        # Export spawn points if present
        if getattr(proxy, 'SpawnPointOverrides', None):
            data['spawnPoints'] = list(cls._extract_spawn_points(proxy.SpawnPointOverrides[0]))
        # Export spawn regions if present
        if getattr(proxy, 'LinkedZoneSpawnVolumeEntries', None):
            data['spawnLocations'] = list(cls._extract_spawn_volumes(proxy.LinkedZoneSpawnVolumeEntries[0]))
        # Check if we extracted any spawn data at all, otherwise we can skip it.
        if 'spawnPoints' not in data and 'spawnLocations' not in data:
            yield from ()
            return

        yield data
    
    @classmethod
    def _extract_counting_volumes(cls, volumes: ArrayProperty) -> Iterable[Dict[str, Dict[str, float]]]:
        for zone_volume in volumes.values:
            zone_volume = zone_volume.value.value
            if not zone_volume:
                continue
            bounds = get_volume_bounds(zone_volume)
            yield dict(start=bounds[0], end=bounds[1])
    
    @classmethod
    def _extract_spawn_points(cls, markers: ArrayProperty) -> Iterable[Vector]:
        for marker in markers.values:
            marker = marker.value.value
            if not marker:
                continue
            yield get_actor_location_vector(marker)
    
    @classmethod
    def _extract_spawn_volumes(cls, entries: ArrayProperty) -> Iterable[Dict[str, Any]]:
        for entry in entries.values:
            entry_data = entry.as_dict()
            entry_weight = entry_data['EntryWeight']
            spawn_volume = entry_data["LinkedZoneSpawnVolume"].value.value

            if not spawn_volume:
                continue
            bounds = get_volume_bounds(spawn_volume)
            yield dict(weight=entry_weight, start=bounds[0], end=bounds[1])

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        # Counting regions
        for location in data['locations']:
            convert_box_bounds_for_export(map_info, location)
        # Spawn regions
        if 'spawnLocations' in data:
            for location in data['spawnLocations']:
                convert_box_bounds_for_export(map_info, location)
        # Spawn points
        if 'spawnPoints' in data:
            for point in data['spawnPoints']:
                point['lat'] = map_info.lat.from_units(point['y'])
                point['long'] = map_info.long.from_units(point['x'])

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Tuple[Any, ...]:
        return (data['spawnGroup'], len(data['locations']))


class BiomeZoneExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'biomes'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, BIOME_ZONE_VOLUME_CLS)

    @classmethod
    def extract(cls, proxy: BiomeZoneVolume) -> Iterable[Dict[str, Any]]: # type:ignore
        volume_bounds = get_volume_bounds(proxy)

        data: Dict[str, Union[UEBase, List, Dict]] = dict(
            name=proxy.BiomeZoneName[0],
            priority=proxy.BiomeZonePriority[0],
            isOutside=proxy.bIsOutside[0],
            preventCrops=proxy.bPreventCrops[0],
            temperature=dict(),
            wind=dict()
        )

        # Add overriden temperature and wind data
        cls._extract_temperature_data(proxy, data)
        cls._extract_wind_data(proxy, data)

        # Remove extra dicts in case they haven't been filled
        if not data['temperature']:
            del data['temperature']
        if not data['wind']:
            del data['wind']
        
        # Extract bounds
        box_count = get_volume_box_count(proxy)
        boxes = list()
        for box_index in range(box_count):
            volume_bounds = get_volume_bounds(proxy, box_index)
            boxes.append(dict(
                start=volume_bounds[0],
                end=volume_bounds[1]
            ))
        data['boxes'] = boxes
        yield data

    @classmethod
    def _extract_temperature_data(cls, proxy: BiomeZoneVolume, data: Dict[str, Any]):
        ## Absolute
        if proxy.has_override('AbsoluteTemperatureOverride'):
            data['temperature']['override'] = proxy.AbsoluteTemperatureOverride[0]
        if proxy.has_override('AbsoluteMaxTemperature') or proxy.has_override('AbsoluteMinTemperature'):
            data['temperature']['range'] = (proxy.AbsoluteMinTemperature[0], proxy.AbsoluteMaxTemperature[0])
        ## Pre-offset
        if proxy.has_override('PreOffsetTemperatureMultiplier') or proxy.has_override('PreOffsetTemperatureExponent') or proxy.has_override('PreOffsetTemperatureAddition'):
            data['temperature']['preOffset'] = (
                None,
                proxy.PreOffsetTemperatureMultiplier[0],
                proxy.PreOffsetTemperatureExponent[0],
                proxy.PreOffsetTemperatureAddition[0]
            )
        ## Above offset
        if proxy.has_override('AboveTemperatureOffsetThreshold') or proxy.has_override('AboveTemperatureOffsetMultiplier') or proxy.has_override('AboveTemperatureOffsetExponent'):
            data['temperature']['aboveOffset'] = (
                proxy.AboveTemperatureOffsetThreshold[0],
                proxy.AboveTemperatureOffsetMultiplier[0],
                proxy.AboveTemperatureOffsetExponent[0],
                None
            )
        ## Below offset
        if proxy.has_override('BelowTemperatureOffsetThreshold') or proxy.has_override('BelowTemperatureOffsetMultiplier') or proxy.has_override('BelowTemperatureOffsetExponent'):
            data['temperature']['belowOffset'] = (
                proxy.BelowTemperatureOffsetThreshold[0],
                proxy.BelowTemperatureOffsetMultiplier[0],
                proxy.BelowTemperatureOffsetExponent[0],
                None
            )
        ## Final
        if proxy.has_override('FinalTemperatureMultiplier') or proxy.has_override('FinalTemperatureExponent') or proxy.has_override('FinalTemperatureAddition'):
            data['temperature']['final'] = (
                None,
                proxy.FinalTemperatureMultiplier[0],
                proxy.FinalTemperatureExponent[0],
                proxy.FinalTemperatureAddition[0]
            )
    
    @classmethod
    def _extract_wind_data(cls, proxy: BiomeZoneVolume, data: Dict[str, Any]):
        ## Absolute
        if proxy.has_override('AbsoluteWindOverride'):
            data['wind']['override'] = proxy.AbsoluteWindOverride[0]
        ## Pre-offset
        if proxy.has_override('PreOffsetWindMultiplier') or proxy.has_override('PreOffsetWindExponent') or proxy.has_override('PreOffsetWindAddition'):
            data['wind']['preOffset'] = (
                None,
                proxy.PreOffsetWindMultiplier[0],
                proxy.PreOffsetWindExponent[0],
                proxy.PreOffsetWindAddition[0]
            )
        ## Above offset
        if proxy.has_override('AboveWindOffsetThreshold') or proxy.has_override('AboveWindOffsetMultiplier') or proxy.has_override('AboveWindOffsetExponent'):
            data['wind']['aboveOffset'] = (
                proxy.AboveWindOffsetThreshold[0],
                proxy.AboveWindOffsetMultiplier[0],
                proxy.AboveWindOffsetExponent[0],
                None
            )
        ## Below offset
        if proxy.has_override('BelowWindOffsetThreshold') or proxy.has_override('BelowWindOffsetMultiplier') or proxy.has_override('BelowWindOffsetExponent'):
            data['wind']['belowOffset'] = (
                proxy.BelowWindOffsetThreshold[0],
                proxy.BelowWindOffsetMultiplier[0],
                proxy.BelowWindOffsetExponent[0],
                None
            )
        ## Final
        if proxy.has_override('FinalWindMultiplier') or proxy.has_override('FinalWindExponent') or proxy.has_override('FinalWindAddition'):
            data['wind']['final'] = (
                None,
                proxy.FinalWindMultiplier[0],
                proxy.FinalWindExponent[0],
                proxy.FinalWindAddition[0]
            )

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        for box in data['boxes']:
            convert_box_bounds_for_export(map_info, box)

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Tuple[Any, ...]:
        return (data['name'], len(data['boxes']))


class LootCrateSpawnExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'lootCrates'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, SUPPLY_CRATE_SPAWN_VOLUME_CLS)

    @classmethod
    def extract(cls, proxy: SupplyCrateSpawningVolume) -> Iterable[Dict[str, Any]]: # type:ignore
        # Sanity checks
        if not getattr(proxy, 'LinkedSupplyCrateEntries', None) or not getattr(proxy, 'LinkedSpawnPointEntries', None):
            yield from ()
            return

        # Make range tuples of numerical properties.
        ranges = dict(
            delayBeforeFirst=(
                proxy.DelayBeforeFirstCrate[0], proxy.MaxDelayBeforeFirstCrate[0]
            ),
            intervalBetweenSpawns=(
                proxy.IntervalBetweenCrateSpawns[0], proxy.MaxIntervalBetweenCrateSpawns[0]
            ),
            intervalBetweenMaxedSpawns=(
                proxy.IntervalBetweenMaxedCrateSpawns[0], proxy.MaxIntervalBetweenMaxedCrateSpawns[0]
            )
        )

        # Single-player overrides. Export only if changed.
        if proxy.has_override('SP_IntervalBetweenCrateSpawns') or proxy.has_override('SP_MaxIntervalBetweenCrateSpawns'):
            ranges['intervalBetweenSpawnsSP'] = (
                proxy.SP_IntervalBetweenCrateSpawns[0], proxy.SP_MaxIntervalBetweenCrateSpawns[0]
            )
        if proxy.has_override('SP_IntervalBetweenMaxedCrateSpawns') or proxy.has_override('SP_MaxIntervalBetweenMaxedCrateSpawns'):
            ranges['intervalBetweenMaxedSpawnsSP'] = (
                proxy.SP_IntervalBetweenMaxedCrateSpawns[0], proxy.SP_MaxIntervalBetweenMaxedCrateSpawns[0]
            )

        # Combine all properties into a single dict
        yield dict(
            maxCrateNumber=proxy.MaxNumCrates[0],
            crateClasses=sorted(cls._convert_crate_classes(proxy.LinkedSupplyCrateEntries[0])),
            crateLocations=list(cls._extract_spawn_points(proxy.LinkedSpawnPointEntries[0])),
            minTimeBetweenSpawnsAtSamePoint=proxy.MinTimeBetweenCrateSpawnsAtSamePoint[0],
            **ranges
        )
    
    @classmethod
    def _convert_crate_classes(cls, entries):
        for entry in entries.values:
            klass = entry.as_dict()['CrateTemplate']
            if not klass or not klass.value.value:
                continue
            yield klass.format_for_json()
    
    @classmethod
    def _extract_spawn_points(cls, entries):
        for entry in entries.values:
            marker = entry.as_dict()['LinkedSpawnPoint'].value.value
            if not marker:
                continue
            yield get_actor_location_vector(marker)

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        for location in data['crateLocations']:
            location['lat'] = map_info.lat.from_units(location['y'])
            location['long'] = map_info.long.from_units(location['x'])

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Tuple[Any, ...]:
        return (data['crateClasses'], data['maxCrateNumber'])


class RadiationZoneExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'radiationVolumes'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        if not inherits_from(export, TOGGLE_PAIN_VOLUME_CLS):
            return False
        # Check if this is a radiation volume
        damage_type = export.properties.get_property('DamageType', fallback=None)
        if damage_type and damage_type.value.value.fullname == DAMAGE_TYPE_RADIATION_PKG:
            return True
        return False

    @classmethod
    def extract(cls, proxy: TogglePainVolume) -> Iterable[Dict[str, Any]]: # type:ignore
        volume_bounds = get_volume_bounds(proxy)
        yield dict(
            start=volume_bounds[0],
            end=volume_bounds[1],
            immune=proxy.ActorClassesToExclude[0],
        )

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        convert_box_bounds_for_export(map_info, data)

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Tuple[Any, ...]:
        return (data['start']['x'], data['start']['y'], data['start']['z'])


class ExplorerNoteExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'notes'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, EXPLORER_CHEST_BASE_CLS)

    @classmethod
    def extract(cls, proxy: ExplorerNote) -> Iterable[Dict[str, Any]]: # type:ignore
        yield dict(noteIndex=proxy.ExplorerNoteIndex[0], **get_actor_location_vector(proxy).format_for_json())

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        data['lat'] = map_info.lat.from_units(data['y'])
        data['long'] = map_info.long.from_units(data['x'])

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Tuple[Any, ...]:
        return (data['noteIndex'], data['x'], data['y'], data['z'])


class OilVeinExport(GenericActorExport):
    KLASS = OIL_VEIN_CLS
    CATEGORY = 'oilVeins'


class WaterVeinExport(GenericActorExport):
    KLASS = WATER_VEIN_CLS
    CATEGORY = 'waterVeins'


class GasVeinExport(GenericActorExport):
    KLASS = GAS_VEIN_CLS
    CATEGORY = 'gasVeins'


class ChargeNodeExport(GenericActorExport):
    KLASS = CHARGE_NODE_CLS
    CATEGORY = 'chargeNodes'


class WildPlantSpeciesZExport(GenericActorExport):
    KLASS = WILD_PLANT_SPECIES_Z_CLS
    CATEGORY = 'plantZNodes'


class WyvernNests(GenericActorListExport):
    TAGS = ('DragonNestSpawns', )
    CATEGORY = 'wyvernNests'

class IceWyvernNests(GenericActorListExport):
    TAGS = ('IceNestSpawns', )
    CATEGORY = 'iceWyvernNests'

class RockDrakeNests(GenericActorListExport):
    TAGS = ('DrakeNestSpawns', )
    CATEGORY = 'drakeNests'

class DeinonychusNests(GenericActorListExport):
    TAGS = ('DeinonychusNestSpawns', 'AB_DeinonychusNestSpawns')
    CATEGORY = 'deinonychusNests'



EXPORTS = [
    # Core
    WorldSettingsExport,
    RadiationZoneExport,
    NPCZoneManagerExport,
    BiomeZoneExport,
    LootCrateSpawnExport,
    ExplorerNoteExport,
    # Scorched Earth
    OilVeinExport,
    WaterVeinExport,
    WyvernNests,
    # Ragnarok
    IceWyvernNests,
    # Aberration
    GasVeinExport,
    ChargeNodeExport,
    WildPlantSpeciesZExport,
    RockDrakeNests,
    # Valguero
    DeinonychusNests,
]


def find_gatherer_for_export(export: ExportTableItem) -> Optional[Type[MapGathererBase]]:
    for helper in EXPORTS:
        try:
            if helper.is_export_eligible(export):
                return helper
        except (MissingParent, AssetLoadException):
            continue

    return None


def find_gatherer_by_category_name(category: str) -> Optional[Type[MapGathererBase]]:
    for helper in EXPORTS:
        if helper.get_category_name() == category:
            return helper

    return None
