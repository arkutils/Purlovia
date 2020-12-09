import re
from typing import Any, Dict, Iterable, Optional, Set, Type, Union, cast

from automate.hierarchy_exporter import ExportModel
from export.wiki.consts import DAMAGE_TYPE_RADIATION_PKG
from export.wiki.models import MinMaxRange
from export.wiki.spawn_groups.structs import convert_single_class_swap
from export.wiki.types import BiomeZoneVolume, DayCycleManager_Gen1, ExplorerNote, HexagonTradableOption, \
    MissionDispatcher_MultiUsePylon, NPCZoneManager, PrimalWorldSettings, SupplyCrateSpawningVolume, TogglePainVolume
from ue.asset import ExportTableItem
from ue.gathering import gather_properties
from ue.properties import ArrayProperty, ObjectProperty, StringProperty
from ue.proxy import UEProxyStructure
from ue.utils import get_leaf_from_assetname, sanitise_output
from utils.name_convert import uelike_prettify

from . import models
from .common import BIOME_REMOVE_WIND_INFO, any_overriden, convert_box_bounds_for_export, \
    convert_location_for_export, get_actor_location_vector, get_volume_bounds, get_volume_box_count
from .gathering_base import GatheringResult, MapGathererBase, PersistentLevel

__all__ = (
    'COMPLEX_GATHERERS',
    'WorldSettingsExport',
)


class WorldSettingsExport(MapGathererBase):
    @classmethod
    def get_export_name(cls) -> str:
        return 'worldSettings'

    @classmethod
    def get_model_type(cls) -> Optional[Type[ExportModel]]:
        return models.WorldSettings

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {PrimalWorldSettings.get_ue_type()}

    @classmethod
    def do_early_checks(cls, export: ExportTableItem) -> bool:
        return not getattr(export.asset, 'tile_info', None)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> models.WorldSettings:
        settings: PrimalWorldSettings = cast(PrimalWorldSettings, proxy)
        source: ExportTableItem = cast(ExportTableItem, proxy.get_source())

        display_name: Union[StringProperty, str]
        if settings.has_override('Title'):
            display_name = settings.Title[0]
        else:
            display_name = get_leaf_from_assetname(source.asset.assetname)
            display_name = display_name.rstrip('_P')
            display_name = uelike_prettify(display_name)

        result = models.WorldSettings(
            source=source.asset.assetname,
            name=display_name,

            # Geo
            latOrigin=settings.LatitudeOrigin[0],
            longOrigin=settings.LongitudeOrigin[0],
            latScale=settings.LatitudeScale[0],
            longScale=settings.LongitudeScale[0],

            # Gameplay Settings
            maxDifficulty=settings.OverrideDifficultyMax[0],
            mapTextures=models.InGameMapTextureSet(
                held=sanitise_output(settings.get('OverrideWeaponMapTextureFilled', 0, None)),
                emptyHeld=sanitise_output(settings.get('OverrideWeaponMapTextureEmpty', 0, None)),
                empty=sanitise_output(settings.get('OverrideUIMapTextureEmpty', 0, None)),
                big=sanitise_output(settings.get('OverrideUIMapTextureFilled', 0, None)),
                small=sanitise_output(settings.get('OverrideUIMapTextureSmall', 0, None)),
            ),
            # Spawns
            onlyEventGlobalSwaps=bool(settings.bPreventGlobalNonEventSpawnOverrides[0]),
            randomNPCClassWeights=list(cls._convert_class_swaps(settings)),
            # Uploads
            allowedDinoDownloads=sanitise_output(settings.get('AllowDownloadDinoClasses', 0, ())),
        )

        # Calculate remaining geo fields
        result.latMulti = result.latScale * 10
        result.latShift = -result.latOrigin / result.latMulti
        result.longMulti = result.longScale * 10
        result.longShift = -result.longOrigin / result.longMulti

        return result

    @classmethod
    def _convert_class_swaps(cls, settings: PrimalWorldSettings) -> Iterable[models.WeighedClassSwap]:
        if 'NPCRandomSpawnClassWeights' in settings:
            for struct in settings.NPCRandomSpawnClassWeights[0].values:
                yield convert_single_class_swap(struct.as_dict())


class TradeListExport(MapGathererBase):
    @classmethod
    def get_model_type(cls) -> Optional[Type[ExportModel]]:
        return models.Trade

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {DayCycleManager_Gen1.get_ue_type()}

    @classmethod
    def do_early_checks(cls, export: ExportTableItem) -> bool:
        return not getattr(export.asset, 'tile_info', None)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        manager: DayCycleManager_Gen1 = cast(DayCycleManager_Gen1, proxy)
        option_list = manager.get('GenesisTradableOptions', fallback=None)
        if option_list:
            for option in option_list.values:
                if bool(option):
                    yield cls._extract_single(option)

    @classmethod
    def _extract_single(cls, option: ObjectProperty) -> Optional[models.Trade]:
        export = option.asset.loader.load_class(option.value.value.fullname)
        trade: HexagonTradableOption = gather_properties(export)

        item = trade.get('ItemClass', fallback=None)
        if not bool(item):
            return None

        return models.Trade(
            bp=trade.get_source().fullname,
            item=str(trade.ItemClass[0].value.value.name),
            qty=trade.Quantity[0],
            cost=trade.ItemCost[0],
        )


class NPCZoneManagerExport(MapGathererBase):
    @classmethod
    def get_export_name(cls) -> str:
        return 'spawns'

    @classmethod
    def get_model_type(cls) -> Optional[Type[ExportModel]]:
        return models.NPCManager

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
        result = models.NPCManager(
            disabled=not manager.bEnabled[0],
            spawnGroup=sanitise_output(spawn_group),
            minDesiredNumberOfNPC=manager.MinDesiredNumberOfNPC[0],
            neverSpawnInWater=manager.bNeverSpawnInWater[0],
            forceUntameable=manager.bForceUntameable[0],
        )

        # Export dino counting regions
        result.locations = list(cls._extract_counting_volumes(count_volumes))
        # Export spawn points if present
        spawn_points = manager.get('SpawnPointOverrides', 0, None)
        spawn_volumes = manager.get('LinkedZoneSpawnVolumeEntries', 0, None)
        if spawn_points:
            result.spawnPoints = list(cls._extract_spawn_points(spawn_points))
        # Export spawn regions if present
        # Behaviour verified in DevKit. Dinos don't spawn in spawning volumes if
        # points were manually specified.
        elif spawn_volumes:
            result.spawnLocations = list(cls._extract_spawn_volumes(spawn_volumes))

        # Check if we extracted any spawn data at all, otherwise we can skip it.
        if not result.spawnPoints and not result.spawnLocations:
            return None

        return result

    @classmethod
    def _extract_counting_volumes(cls, volumes: ArrayProperty) -> Iterable[models.Box]:
        for zone_volume in volumes.values:
            zone_volume = zone_volume.value.value
            if zone_volume:
                yield get_volume_bounds(zone_volume)

    @classmethod
    def _extract_spawn_points(cls, markers: ArrayProperty) -> Iterable[models.Location]:
        for marker in markers.values:
            marker = marker.value.value
            if marker:
                yield get_actor_location_vector(marker)

    @classmethod
    def _extract_spawn_volumes(cls, entries: ArrayProperty) -> Iterable[models.WeighedBox]:
        for entry in entries.values:
            d = entry.as_dict()
            volume = d["LinkedZoneSpawnVolume"].value.value

            if volume:
                box = get_volume_bounds(volume)
                yield models.WeighedBox(weight=d['EntryWeight'], start=box.start, center=box.center, end=box.end)

    @classmethod
    def before_saving(cls, world: PersistentLevel, data: Dict[str, Any]):
        # Counting regions
        if 'locations' in data:
            for location in data['locations']:
                convert_box_bounds_for_export(world, location)
        # Spawn regions
        if 'spawnLocations' in data:
            for location in data['spawnLocations']:
                convert_box_bounds_for_export(world, location)
        # Spawn points
        if 'spawnPoints' in data:
            for point in data['spawnPoints']:
                convert_location_for_export(world, point)


class BiomeZoneExport(MapGathererBase):
    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {BiomeZoneVolume.get_ue_type()}

    @classmethod
    def get_model_type(cls) -> Optional[Type[ExportModel]]:
        return models.Biome

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        biome: BiomeZoneVolume = cast(BiomeZoneVolume, proxy)
        biome_name = str(biome.BiomeZoneName[0])
        biome_name = re.sub(BIOME_REMOVE_WIND_INFO, '', biome_name)
        biome_name = biome_name.strip()

        result = models.Biome(
            name=biome_name,
            priority=biome.BiomeZonePriority[0],
            isOutside=biome.bIsOutside[0],
            preventCrops=biome.bPreventCrops[0],
        )

        # Add overriden temperature and wind data
        cls._extract_temperature_data(biome, result.temperature)
        cls._extract_wind_data(biome, result.wind)

        # Extract bounds
        box_count = get_volume_box_count(biome)
        for box_index in range(box_count):
            box = get_volume_bounds(biome, box_index)
            result.boxes.append(box)
        return result

    @classmethod
    def _extract_temperature_data(cls, biome: BiomeZoneVolume, result: models.BiomeTempWindSettings):
        # Absolute
        if biome.has_override('AbsoluteTemperatureOverride'):
            result.override = biome.AbsoluteTemperatureOverride[0]
        if biome.has_override('AbsoluteMaxTemperature') or biome.has_override('AbsoluteMinTemperature'):
            result.range = MinMaxRange(min=biome.AbsoluteMinTemperature[0], max=biome.AbsoluteMaxTemperature[0])
        # Pre-offset
        if any_overriden(biome,
                         ('PreOffsetTemperatureMultiplier', 'PreOffsetTemperatureExponent', 'PreOffsetTemperatureAddition')):
            result.initial = (biome.PreOffsetTemperatureMultiplier[0], biome.PreOffsetTemperatureExponent[0],
                              biome.PreOffsetTemperatureAddition[0])
        # Above offset
        if any_overriden(
                biome,
            ('AboveTemperatureOffsetThreshold', 'AboveTemperatureOffsetMultiplier', 'AboveTemperatureOffsetExponent')):
            result.above = (biome.AboveTemperatureOffsetThreshold[0], biome.AboveTemperatureOffsetMultiplier[0],
                            biome.AboveTemperatureOffsetExponent[0])
        # Below offset
        if any_overriden(
                biome,
            ('BelowTemperatureOffsetThreshold', 'BelowTemperatureOffsetMultiplier', 'BelowTemperatureOffsetExponent')):
            result.below = (biome.BelowTemperatureOffsetThreshold[0], biome.BelowTemperatureOffsetMultiplier[0],
                            biome.BelowTemperatureOffsetExponent[0])
        # Final
        if any_overriden(biome, ('FinalTemperatureMultiplier', 'FinalTemperatureExponent', 'FinalTemperatureAddition')):
            result.final = (biome.FinalTemperatureMultiplier[0], biome.FinalTemperatureExponent[0],
                            biome.FinalTemperatureAddition[0])

    @classmethod
    def _extract_wind_data(cls, biome: BiomeZoneVolume, result: models.BiomeTempWindSettings):
        # Absolute
        if biome.has_override('AbsoluteWindOverride'):
            result.override = biome.AbsoluteWindOverride[0]
        # Pre-offset
        if any_overriden(biome, ('PreOffsetWindMultiplier', 'PreOffsetWindExponent', 'PreOffsetWindAddition')):
            result.initial = (biome.PreOffsetWindMultiplier[0], biome.PreOffsetWindExponent[0], biome.PreOffsetWindAddition[0])
        # Above offset
        if any_overriden(biome, ('AboveWindOffsetThreshold', 'AboveWindOffsetMultiplier', 'AboveWindOffsetExponent')):
            result.above = (biome.AboveWindOffsetThreshold[0], biome.AboveWindOffsetMultiplier[0],
                            biome.AboveWindOffsetExponent[0])
        # Below offset
        if any_overriden(biome, ('BelowWindOffsetThreshold', 'BelowWindOffsetMultiplier', 'BelowWindOffsetExponent')):
            result.below = (biome.BelowWindOffsetThreshold[0], biome.BelowWindOffsetMultiplier[0],
                            biome.BelowWindOffsetExponent[0])
        # Final
        if any_overriden(biome, ('FinalWindMultiplier', 'FinalWindExponent', 'FinalWindAddition')):
            result.final = (biome.FinalWindMultiplier[0], biome.FinalWindExponent[0], biome.FinalWindAddition[0])

    @classmethod
    def before_saving(cls, world: PersistentLevel, data: Dict[str, Any]):
        for box in data['boxes']:
            convert_box_bounds_for_export(world, box)


class LootCrateSpawnExport(MapGathererBase):
    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {SupplyCrateSpawningVolume.get_ue_type()}

    @classmethod
    def get_model_type(cls) -> Optional[Type[ExportModel]]:
        return models.SupplyCrateSpawn

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

        # Construct model with data.
        result = models.SupplyCrateSpawn(
            maxCrateNumber=spawner.MaxNumCrates[0],
            crateClasses=sorted(cls._convert_crate_classes(class_entries)),
            crateLocations=list(cls._extract_spawn_points(spawn_points)),
            minTimeBetweenSpawnsAtSamePoint=spawner.MinTimeBetweenCrateSpawnsAtSamePoint[0],
            delayBeforeFirst=MinMaxRange(min=spawner.DelayBeforeFirstCrate[0], max=spawner.MaxDelayBeforeFirstCrate[0]),
            intervalBetweenSpawns=MinMaxRange(min=spawner.IntervalBetweenCrateSpawns[0],
                                              max=spawner.MaxIntervalBetweenCrateSpawns[0]),
            intervalBetweenMaxedSpawns=MinMaxRange(min=spawner.IntervalBetweenMaxedCrateSpawns[0],
                                                   max=spawner.MaxIntervalBetweenMaxedCrateSpawns[0]),
        )

        # Single-player overrides. Export only if changed.
        if spawner.has_override('SP_IntervalBetweenCrateSpawns') or spawner.has_override('SP_MaxIntervalBetweenCrateSpawns'):
            result.intervalBetweenSpawnsSP = MinMaxRange(min=spawner.SP_IntervalBetweenCrateSpawns[0],
                                                         max=spawner.SP_MaxIntervalBetweenCrateSpawns[0])
        if spawner.has_override('SP_IntervalBetweenMaxedCrateSpawns') or spawner.has_override(
                'SP_MaxIntervalBetweenMaxedCrateSpawns'):
            result.intervalBetweenMaxedSpawnsSP = MinMaxRange(min=spawner.SP_IntervalBetweenMaxedCrateSpawns[0],
                                                              max=spawner.SP_MaxIntervalBetweenMaxedCrateSpawns[0])

        return result

    @classmethod
    def _convert_crate_classes(cls, entries) -> Iterable[models.ObjectPath]:
        for entry in entries.values:
            klass = entry.as_dict()['CrateTemplate']
            if klass:
                yield sanitise_output(klass)

    @classmethod
    def _extract_spawn_points(cls, entries) -> Iterable[models.Location]:
        for entry in entries.values:
            marker = entry.as_dict()['LinkedSpawnPoint'].value.value
            if marker:
                yield get_actor_location_vector(marker)

    @classmethod
    def before_saving(cls, world: PersistentLevel, data: Dict[str, Any]):
        for location in data['crateLocations']:
            convert_location_for_export(world, location)


class RadiationZoneExport(MapGathererBase):
    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {TogglePainVolume.get_ue_type()}

    @classmethod
    def get_model_type(cls) -> Optional[Type[ExportModel]]:
        return models.PainVolume

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
        box = get_volume_bounds(volume)
        return models.PainVolume(
            start=box.start,
            center=box.center,
            end=box.end,
            immune=sanitise_output(volume.get('ActorClassesToExclude', fallback=[])),
        )

    @classmethod
    def before_saving(cls, world: PersistentLevel, data: Dict[str, Any]):
        convert_box_bounds_for_export(world, data)


class MissionDispatcher(MapGathererBase):
    MISSION_TYPE_MAP = {
        0: 'BossFight',
        1: 'Escort',
        2: 'Fishing',
        3: 'GatherNodes',
        4: 'Gauntlet',
        5: 'Hunt',
        6: 'Race',
        7: 'Retrieve',
        8: 'Basketball',
    }

    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {MissionDispatcher_MultiUsePylon.get_ue_type()}

    @classmethod
    def get_model_type(cls) -> Optional[Type[ExportModel]]:
        return models.MissionDispatcher

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        dispatcher: MissionDispatcher_MultiUsePylon = cast(MissionDispatcher_MultiUsePylon, proxy)
        type_id = dispatcher.MissionTypeIndex[0].value
        location = get_actor_location_vector(dispatcher)

        return models.MissionDispatcher(type_=cls.MISSION_TYPE_MAP.get(type_id, type_id),
                                        missions=sanitise_output(dispatcher.MissionTypes[0].values),
                                        x=location.x,
                                        y=location.y,
                                        z=location.z)

    @classmethod
    def before_saving(cls, world: PersistentLevel, data: Dict[str, Any]):
        convert_location_for_export(world, data)


class ExplorerNoteExport(MapGathererBase):
    @classmethod
    def get_ue_types(cls) -> Set[str]:
        return {ExplorerNote.get_ue_type()}

    @classmethod
    def get_model_type(cls) -> Optional[Type[ExportModel]]:
        return models.ExplorerNote

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> GatheringResult:
        note: ExplorerNote = cast(ExplorerNote, proxy)
        location = get_actor_location_vector(proxy)

        return models.ExplorerNote(noteIndex=note.ExplorerNoteIndex[0],
                                   hidden=not note.bIsVisible[0],
                                   x=location.x,
                                   y=location.y,
                                   z=location.z)

    @classmethod
    def before_saving(cls, world: PersistentLevel, data: Dict[str, Any]):
        convert_location_for_export(world, data)


COMPLEX_GATHERERS = [
    # Core
    WorldSettingsExport,
    ExplorerNoteExport,
    NPCZoneManagerExport,
    BiomeZoneExport,
    LootCrateSpawnExport,
    # Aberration
    RadiationZoneExport,
    # Genesis
    TradeListExport,
    MissionDispatcher,
]
