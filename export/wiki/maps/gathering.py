import re
from typing import Any, Dict, Iterable, List, Optional, Set, Type, Union, cast

from export.wiki.consts import DAMAGE_TYPE_RADIATION_PKG
from export.wiki.types import *
from ue.asset import ExportTableItem
from ue.gathering import gather_properties
from ue.hierarchy import MissingParent, find_parent_classes
from ue.properties import ArrayProperty, StringProperty, Vector
from ue.proxy import UEProxyStructure

from .base import GatheredData, GatheringResult, MapGathererBase
from .common import BIOME_REMOVE_WIND_INFO, convert_box_bounds_for_export, \
    get_actor_location_vector, get_volume_bounds, get_volume_box_count
from .data_container import MapInfo

__all__ = [
    'EXPORTS',
    'find_gatherer_for_export',
    'find_gatherer_by_category_name',
]


class GenericActorExport(MapGathererBase):
    CLASSES: Set[str]
    CATEGORY: str

    @classmethod
    def get_export_name(cls) -> str:
        return cls.CATEGORY

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return cls.CLASSES

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        data = dict(
            hidden=not proxy.get('bIsVisible', fallback=True),
            **get_actor_location_vector(proxy).format_for_json(),
        )
        # Remove the "hidden" mark if not hidden
        if not data['hidden']:
            del data['hidden']
        return data

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        data['lat'] = map_info.lat.from_units(data['y'])
        data['long'] = map_info.long.from_units(data['x'])


class GenericActorListExport(MapGathererBase):
    TAGS: Set[str]
    CATEGORY: str

    @classmethod
    def get_export_name(cls) -> str:
        return cls.CATEGORY

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {CustomActorList.get_ue_type()}

    @classmethod
    def do_early_checks(cls, export: ExportTableItem) -> bool:
        # Check the tag
        tag = export.properties.get_property('CustomTag', fallback='')
        return str(tag) in cls.TAGS

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        actors: CustomActorList = cast(CustomActorList, proxy)
        for entry in actors.ActorList[0].values:
            if not entry.value.value:
                continue

            yield cls.extract_single(entry.value.value)

    @classmethod
    def extract_single(cls, export: ExportTableItem) -> GatheredData:
        return get_actor_location_vector(export)

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        data['lat'] = map_info.lat.from_units(data['y'])
        data['long'] = map_info.long.from_units(data['x'])


class WorldSettingsExport(MapGathererBase):
    @classmethod
    def get_export_name(cls) -> str:
        return 'worldSettings'

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {PrimalWorldSettings.get_ue_type()}

    @classmethod
    def do_early_checks(cls, export: ExportTableItem) -> bool:
        return not getattr(export.asset, 'tile_info', None)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        settings: PrimalWorldSettings = cast(PrimalWorldSettings, proxy)
        source: ExportTableItem = cast(ExportTableItem, proxy.get_source())

        display_name: Union[StringProperty, str]
        if settings.has_override('Title'):
            display_name = settings.Title[0]
        else:
            display_name = source.asset.assetname.rsplit('/', 1)[1]
            display_name = display_name.rstrip('_P')
            # Insert spaces before capital letters
            display_name = re.sub(r'\B([A-Z])', r' \1', display_name)

        data = dict(
            source=source.asset.assetname,
            name=display_name,
            # Geo
            latOrigin=settings.LatitudeOrigin[0],
            longOrigin=settings.LongitudeOrigin[0],
            latScale=settings.LatitudeScale[0],
            longScale=settings.LongitudeScale[0],
            # These fields will be filled out during data conversion
            latMulti=0,
            longMulti=0,
            latShift=0,
            longShift=0,
            # Extra data
            maxDifficulty=settings.OverrideDifficultyMax[0],
            mapTextures=dict(
                held=settings.get('OverrideWeaponMapTextureFilled', 0, None),
                emptyHeld=settings.get('OverrideWeaponMapTextureEmpty', 0, None),
                empty=settings.get('OverrideUIMapTextureEmpty', 0, None),
                big=settings.get('OverrideUIMapTextureFilled', 0, None),
                small=settings.get('OverrideUIMapTextureSmall', 0, None),
            ),
            randomNPCClassWeights=[{
                'from': struct.get_property('FromClass'),
                'exact': struct.get_property('bExactMatch'),
                'to': struct.get_property('ToClasses'),
                'weights': struct.get_property('Weights'),
            } for struct in settings.NPCRandomSpawnClassWeights[0].values] if 'NPCRandomSpawnClassWeights' in proxy else [],
            allowedDinoDownloads=settings.get('AllowDownloadDinoClasses', 0, ()),
        )

        if settings.bPreventGlobalNonEventSpawnOverrides[0]:
            data['onlyEventGlobalSwaps'] = True

        return data

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        data['latMulti'] = map_info.lat.multiplier
        data['longMulti'] = map_info.long.multiplier
        data['latShift'] = map_info.lat.shift
        data['longShift'] = map_info.long.shift


class NPCZoneManagerExport(MapGathererBase):
    @classmethod
    def get_export_name(cls) -> str:
        return 'spawns'

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {NPCZoneManager.get_ue_type()}

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        manager: NPCZoneManager = cast(NPCZoneManager, proxy)

        # Sanity checks
        spawn_group = manager.get('NPCSpawnEntriesContainerObject', 0, None)
        count_volumes = manager.get('LinkedZoneVolumes', 0, None)
        if not spawn_group or not spawn_group.value.value or not count_volumes:
            return None

        # Export properties
        data: Dict[str, Any] = dict(
            disabled=not manager.bEnabled[0],
            spawnGroup=spawn_group,
            minDesiredNumberOfNPC=manager.MinDesiredNumberOfNPC[0],
            neverSpawnInWater=manager.bNeverSpawnInWater[0],
            forceUntameable=manager.bForceUntameable[0],
        )
        # Remove "disabled" entirely if enabled
        if not data['disabled']:
            del data['disabled']

        # Export dino counting regions
        data['locations'] = list(cls._extract_counting_volumes(count_volumes))
        # Export spawn points if present
        spawn_points = manager.get('SpawnPointOverrides', 0, None)
        spawn_volumes = manager.get('LinkedZoneSpawnVolumeEntries', 0, None)
        if spawn_points:
            data['spawnPoints'] = list(cls._extract_spawn_points(spawn_points))
        # Export spawn regions if present
        # Behaviour verified in DevKit. Dinos don't spawn in spawning volumes if
        # points were manually specified.
        elif spawn_volumes:
            data['spawnLocations'] = list(cls._extract_spawn_volumes(spawn_volumes))

        # Check if we extracted any spawn data at all, otherwise we can skip it.
        if not data.get('spawnPoints', None) and not data.get('spawnLocations', None):
            return None

        return data

    @classmethod
    def _extract_counting_volumes(cls, volumes: ArrayProperty) -> Iterable[Dict[str, Dict[str, float]]]:
        for zone_volume in volumes.values:
            zone_volume = zone_volume.value.value
            if not zone_volume:
                continue
            bounds = get_volume_bounds(zone_volume)
            yield dict(start=bounds[0], center=bounds[1], end=bounds[2])

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
            yield dict(weight=entry_weight, start=bounds[0], center=bounds[1], end=bounds[2])

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


class BiomeZoneExport(MapGathererBase):
    @classmethod
    def get_export_name(cls) -> str:
        return 'biomes'

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {BiomeZoneVolume.get_ue_type()}

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        biome: BiomeZoneVolume = cast(BiomeZoneVolume, proxy)
        volume_bounds = get_volume_bounds(biome)

        biome_name = str(biome.BiomeZoneName[0])
        biome_name = re.sub(BIOME_REMOVE_WIND_INFO, '', biome_name)
        biome_name = biome_name.strip()
        data: Dict[str, Any] = dict(
            name=biome_name,
            priority=biome.BiomeZonePriority[0],
            isOutside=biome.bIsOutside[0],
            preventCrops=biome.bPreventCrops[0],
            temperature=dict(),
            wind=dict(),
        )

        # Add overriden temperature and wind data
        cls._extract_temperature_data(biome, data)
        cls._extract_wind_data(biome, data)

        # Remove extra dicts in case they haven't been filled
        if not data['temperature']:
            del data['temperature']
        if not data['wind']:
            del data['wind']

        # Extract bounds
        box_count = get_volume_box_count(biome)
        boxes = list()
        for box_index in range(box_count):
            volume_bounds = get_volume_bounds(biome, box_index)
            boxes.append(dict(start=volume_bounds[0], center=volume_bounds[1], end=volume_bounds[2]))
        data['boxes'] = boxes
        return data

    @classmethod
    def _extract_temperature_data(cls, proxy: BiomeZoneVolume, data: Dict[str, Any]):
        # Absolute
        if proxy.has_override('AbsoluteTemperatureOverride'):
            data['temperature']['override'] = proxy.AbsoluteTemperatureOverride[0]
        if proxy.has_override('AbsoluteMaxTemperature') or proxy.has_override('AbsoluteMinTemperature'):
            data['temperature']['range'] = (proxy.AbsoluteMinTemperature[0], proxy.AbsoluteMaxTemperature[0])
        # Pre-offset
        if proxy.has_override('PreOffsetTemperatureMultiplier') or proxy.has_override(
                'PreOffsetTemperatureExponent') or proxy.has_override('PreOffsetTemperatureAddition'):
            data['temperature']['preOffset'] = (None, proxy.PreOffsetTemperatureMultiplier[0],
                                                proxy.PreOffsetTemperatureExponent[0], proxy.PreOffsetTemperatureAddition[0])
        # Above offset
        if proxy.has_override('AboveTemperatureOffsetThreshold') or proxy.has_override(
                'AboveTemperatureOffsetMultiplier') or proxy.has_override('AboveTemperatureOffsetExponent'):
            data['temperature']['aboveOffset'] = (
                proxy.AboveTemperatureOffsetThreshold[0],
                proxy.AboveTemperatureOffsetMultiplier[0],
                proxy.AboveTemperatureOffsetExponent[0],
                None,
            )
        # Below offset
        if proxy.has_override('BelowTemperatureOffsetThreshold') or proxy.has_override(
                'BelowTemperatureOffsetMultiplier') or proxy.has_override('BelowTemperatureOffsetExponent'):
            data['temperature']['belowOffset'] = (
                proxy.BelowTemperatureOffsetThreshold[0],
                proxy.BelowTemperatureOffsetMultiplier[0],
                proxy.BelowTemperatureOffsetExponent[0],
                None,
            )
        # Final
        if proxy.has_override('FinalTemperatureMultiplier') or proxy.has_override(
                'FinalTemperatureExponent') or proxy.has_override('FinalTemperatureAddition'):
            data['temperature']['final'] = (None, proxy.FinalTemperatureMultiplier[0], proxy.FinalTemperatureExponent[0],
                                            proxy.FinalTemperatureAddition[0])

    @classmethod
    def _extract_wind_data(cls, proxy: BiomeZoneVolume, data: Dict[str, Any]):
        # Absolute
        if proxy.has_override('AbsoluteWindOverride'):
            data['wind']['override'] = proxy.AbsoluteWindOverride[0]
        # Pre-offset
        if proxy.has_override('PreOffsetWindMultiplier') or proxy.has_override('PreOffsetWindExponent') or proxy.has_override(
                'PreOffsetWindAddition'):
            data['wind']['preOffset'] = (
                None,
                proxy.PreOffsetWindMultiplier[0],
                proxy.PreOffsetWindExponent[0],
                proxy.PreOffsetWindAddition[0],
            )
        # Above offset
        if proxy.has_override('AboveWindOffsetThreshold') or proxy.has_override(
                'AboveWindOffsetMultiplier') or proxy.has_override('AboveWindOffsetExponent'):
            data['wind']['aboveOffset'] = (
                proxy.AboveWindOffsetThreshold[0],
                proxy.AboveWindOffsetMultiplier[0],
                proxy.AboveWindOffsetExponent[0],
                None,
            )
        # Below offset
        if proxy.has_override('BelowWindOffsetThreshold') or proxy.has_override(
                'BelowWindOffsetMultiplier') or proxy.has_override('BelowWindOffsetExponent'):
            data['wind']['belowOffset'] = (
                proxy.BelowWindOffsetThreshold[0],
                proxy.BelowWindOffsetMultiplier[0],
                proxy.BelowWindOffsetExponent[0],
                None,
            )
        # Final
        if proxy.has_override('FinalWindMultiplier') or proxy.has_override('FinalWindExponent') or proxy.has_override(
                'FinalWindAddition'):
            data['wind']['final'] = (
                None,
                proxy.FinalWindMultiplier[0],
                proxy.FinalWindExponent[0],
                proxy.FinalWindAddition[0],
            )

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        for box in data['boxes']:
            convert_box_bounds_for_export(map_info, box)


class LootCrateSpawnExport(MapGathererBase):
    @classmethod
    def get_export_name(cls) -> str:
        return 'lootCrates'

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {SupplyCrateSpawningVolume.get_ue_type()}

    @classmethod
    def do_early_checks(cls, export: ExportTableItem) -> bool:
        return bool(export.properties.get_property('bIsEnabled', fallback=True))

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        spawner: SupplyCrateSpawningVolume = cast(SupplyCrateSpawningVolume, proxy)

        # Sanity checks
        class_entries = spawner.get('LinkedSupplyCrateEntries', 0, None)
        spawn_points = spawner.get('LinkedSpawnPointEntries', 0, None)
        if not class_entries or not spawn_points:
            return None

        # Make range tuples of numerical properties.
        ranges = dict(
            delayBeforeFirst=(spawner.DelayBeforeFirstCrate[0], spawner.MaxDelayBeforeFirstCrate[0]),
            intervalBetweenSpawns=(spawner.IntervalBetweenCrateSpawns[0], spawner.MaxIntervalBetweenCrateSpawns[0]),
            intervalBetweenMaxedSpawns=(spawner.IntervalBetweenMaxedCrateSpawns[0],
                                        spawner.MaxIntervalBetweenMaxedCrateSpawns[0]),
        )

        # Single-player overrides. Export only if changed.
        if spawner.has_override('SP_IntervalBetweenCrateSpawns') or spawner.has_override('SP_MaxIntervalBetweenCrateSpawns'):
            ranges['intervalBetweenSpawnsSP'] = (
                spawner.SP_IntervalBetweenCrateSpawns[0],
                spawner.SP_MaxIntervalBetweenCrateSpawns[0],
            )
        if spawner.has_override('SP_IntervalBetweenMaxedCrateSpawns') or spawner.has_override(
                'SP_MaxIntervalBetweenMaxedCrateSpawns'):
            ranges['intervalBetweenMaxedSpawnsSP'] = (
                spawner.SP_IntervalBetweenMaxedCrateSpawns[0],
                spawner.SP_MaxIntervalBetweenMaxedCrateSpawns[0],
            )

        # Combine all properties into a single dict
        return dict(
            maxCrateNumber=spawner.MaxNumCrates[0],
            crateClasses=sorted(cls._convert_crate_classes(class_entries)),
            crateLocations=list(cls._extract_spawn_points(spawn_points)),
            minTimeBetweenSpawnsAtSamePoint=spawner.MinTimeBetweenCrateSpawnsAtSamePoint[0],
            **ranges,
        )

    @classmethod
    def _convert_crate_classes(cls, entries):
        for entry in entries.values:
            klass = entry.as_dict()['CrateTemplate']
            if not klass or not klass.value.value:
                continue
            yield str(klass.value.value.fullname)

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


class RadiationZoneExport(MapGathererBase):
    @classmethod
    def get_export_name(cls) -> str:
        return 'radiationVolumes'

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {TogglePainVolume.get_ue_type()}

    @classmethod
    def do_early_checks(cls, export: ExportTableItem) -> bool:
        # Check if disabled
        is_enabled = bool(export.properties.get_property('bPainCausing', fallback=True))
        if not is_enabled:
            return False
        # Check if this is a radiation volume
        damage_type = export.properties.get_property('DamageType', fallback=None)
        return bool(damage_type and damage_type.value.value.fullname == DAMAGE_TYPE_RADIATION_PKG)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        volume: TogglePainVolume = cast(TogglePainVolume, proxy)
        volume_bounds = get_volume_bounds(volume)
        return dict(
            start=volume_bounds[0],
            center=volume_bounds[1],
            end=volume_bounds[2],
            immune=volume.ActorClassesToExclude[0],
        )

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        convert_box_bounds_for_export(map_info, data)


class ExplorerNoteExport(MapGathererBase):
    @classmethod
    def get_export_name(cls) -> str:
        return 'notes'

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {ExplorerNote.get_ue_type()}

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        note: ExplorerNote = cast(ExplorerNote, proxy)
        data = dict(
            noteIndex=note.ExplorerNoteIndex[0],
            hidden=not note.bIsVisible[0],
            **get_actor_location_vector(proxy).format_for_json(),
        )
        # Remove the "hidden" mark if not hidden
        if not data['hidden']:
            del data['hidden']
        return data

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        data['lat'] = map_info.lat.from_units(data['y'])
        data['long'] = map_info.long.from_units(data['x'])


class HLNAGlitchExport(GenericActorListExport):
    @classmethod
    def get_export_name(cls) -> str:
        return 'glitches'

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {PointOfInterestListGen1.get_ue_type()}

    @classmethod
    def do_early_checks(cls, _: ExportTableItem) -> bool:
        return True

    @classmethod
    def extract_single(cls, export: ExportTableItem) -> GatheredData:
        poi: PointOfInterestBP = gather_properties(export)

        d: Dict[str, Any] = dict()
        noteid = poi.get('Specific_Unlocked_Explorer_Note_Index', fallback=-1)
        if noteid != -1:
            d['noteId'] = noteid

        #poi_info = poi.get('MyPointOfInterestData', fallback=None)
        #if poi_info:
        #    tag = poi_info.as_dict().get('PointTag', None)
        #    d['poiTag'] = tag

        d['hexagons'] = poi.get('number_of_hexagons_to_reward_upon_fixing', fallback=1000)
        d.update(get_actor_location_vector(export).format_for_json())
        return d


class PlayerSpawnPointExport(GenericActorExport):
    CLASSES = {PlayerStart.get_ue_type()}
    CATEGORY = 'playerSpawns'

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        point: PlayerStart = cast(PlayerStart, proxy)
        return dict(
            regionId=point.SpawnPointRegion[0],
            **get_actor_location_vector(proxy).format_for_json(),
        )


class OilVeinExport(GenericActorExport):
    CLASSES = {OilVein.get_ue_type()}
    CATEGORY = 'oilVeins'


class WaterVeinExport(GenericActorExport):
    CLASSES = {WaterVein.get_ue_type()}
    CATEGORY = 'waterVeins'


class LunarOxygenVentExport(GenericActorExport):
    CLASSES = {LunarOxygenVentGen1.get_ue_type()}
    CATEGORY = 'lunarOxygenVents'


class OilVentExport(GenericActorExport):
    CLASSES = {OilVentGen1.get_ue_type()}
    CATEGORY = 'oilVents'


class GasVeinExport(GenericActorExport):
    CLASSES = {GasVein.get_ue_type(), GasVeinGen1.get_ue_type()}
    CATEGORY = 'gasVeins'


class ChargeNodeExport(GenericActorExport):
    CLASSES = {PrimalStructurePowerNode.get_ue_type()}
    CATEGORY = 'chargeNodes'


class WildPlantSpeciesZExport(GenericActorExport):
    CLASSES = {WildPlantSpeciesZ.get_ue_type()}
    CATEGORY = 'plantZNodes'


class WyvernNests(GenericActorListExport):
    TAGS = {'DragonNestSpawns'}
    CATEGORY = 'wyvernNests'


class IceWyvernNests(GenericActorListExport):
    TAGS = {'IceNestSpawns'}
    CATEGORY = 'iceWyvernNests'


class RockDrakeNests(GenericActorListExport):
    TAGS = {'DrakeNestSpawns'}
    CATEGORY = 'drakeNests'


class DeinonychusNests(GenericActorListExport):
    TAGS = {'DeinonychusNestSpawns', 'AB_DeinonychusNestSpawns'}
    CATEGORY = 'deinonychusNests'


class MagmasaurNests(GenericActorListExport):
    TAGS = {'MagmasaurNestSpawns'}
    CATEGORY = 'magmasaurNests'


EXPORTS: Dict[str, List[Type[MapGathererBase]]] = {
    'world_settings': [
        # Core
        WorldSettingsExport,
        PlayerSpawnPointExport,
    ],
    'radiation_zones': [
        # Core
        RadiationZoneExport,
    ],
    'npc_spawns': [
        # Core
        NPCZoneManagerExport,
    ],
    'biomes': [
        # Core
        BiomeZoneExport,
    ],
    'loot_crates': [
        # Core
        LootCrateSpawnExport,
    ],
    'actors': [
        # Core
        ExplorerNoteExport,
        # Scorched Earth
        OilVeinExport,
        WaterVeinExport,
        WyvernNests,
        # Ragnarok
        IceWyvernNests,
        # Genesis and Aberration
        OilVentExport,
        LunarOxygenVentExport,
        GasVeinExport,
        # Aberration
        ChargeNodeExport,
        WildPlantSpeciesZExport,
        RockDrakeNests,
        # Valguero
        DeinonychusNests,
        # Genesis
        HLNAGlitchExport,
        MagmasaurNests,
    ],
}


def find_gatherer_for_export(export: ExportTableItem) -> Optional[Type[MapGathererBase]]:
    try:
        parents = set(find_parent_classes(export, include_self=True))
    except MissingParent:
        return None

    for _, helpers in EXPORTS.items():
        for helper in helpers:
            if parents & helper.get_ue_types():
                if helper.do_early_checks(export):
                    return helper

    return None


def find_gatherer_by_category_name(category: str) -> Optional[Type[MapGathererBase]]:
    for _, helpers in EXPORTS.items():
        for helper in helpers:
            if helper.get_export_name() == category:
                return helper

    return None
