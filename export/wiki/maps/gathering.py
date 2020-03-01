import re
from typing import Any, Dict, Iterable, List, Optional, Tuple, Type, Union, cast

from export.wiki.consts import *
from export.wiki.types import BiomeZoneVolume, CustomActorList, ExplorerNote, \
    NPCZoneManager, PrimalWorldSettings, SupplyCrateSpawningVolume, TogglePainVolume
from ue.asset import ExportTableItem
from ue.base import UEBase
from ue.hierarchy import MissingParent, inherits_from
from ue.loader import AssetLoadException
from ue.properties import ArrayProperty, StringProperty, Vector
from ue.proxy import UEProxyStructure

from .base import MapGathererBase
from .common import BIOME_REMOVE_WIND_INFO, convert_box_bounds_for_export, \
    get_actor_location_vector, get_volume_bounds, get_volume_box_count
from .data_container import MapInfo


class GenericActorExport(MapGathererBase):
    CLASSES: Tuple[str, ...]
    CATEGORY: str

    @classmethod
    def get_category_name(cls) -> str:
        return cls.CATEGORY

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        for klass in cls.CLASSES:
            if inherits_from(export, klass):
                return True
        return False

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Iterable[Union[UEBase, Dict[str, Any]]]:
        data = dict(
            hidden=not proxy.get('bIsVisible', fallback=True),
            **get_actor_location_vector(proxy).format_for_json(),
        )
        # Remove the "hidden" mark if not hidden
        if not data['hidden']:
            del data['hidden']
        yield data

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        data['lat'] = map_info.lat.from_units(data['y'])
        data['long'] = map_info.long.from_units(data['x'])


class GenericActorListExport(MapGathererBase):
    TAGS: Tuple[str, ...]
    CATEGORY: str

    @classmethod
    def get_category_name(cls) -> str:
        return cls.CATEGORY

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        if not inherits_from(export, CUSTOM_ACTOR_LIST_CLS):
            return False
        # Check the tag
        tag = export.properties.get_property('CustomTag', fallback='')
        return str(tag) in cls.TAGS

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Iterable[Union[UEBase, Dict[str, Any]]]:
        actors: CustomActorList = cast(CustomActorList, proxy)
        for entry in actors.ActorList[0].values:
            if not entry.value.value:
                continue

            yield cls.extract_single(entry.value.value)

    @classmethod
    def extract_single(cls, export: ExportTableItem) -> Union[UEBase, Dict[str, Any]]:
        return get_actor_location_vector(export)

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        data['lat'] = map_info.lat.from_units(data['y'])
        data['long'] = map_info.long.from_units(data['x'])


class WorldSettingsExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'worldSettings'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, PRIMAL_WORLD_SETTINGS_CLS) and not getattr(export.asset, 'tile_info', None)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Iterable[Dict[str, Any]]:
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

        yield data

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        data['latMulti'] = map_info.lat.multiplier
        data['longMulti'] = map_info.long.multiplier
        data['latShift'] = map_info.lat.shift
        data['longShift'] = map_info.long.shift


class NPCZoneManagerExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'spawns'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, NPC_ZONE_MANAGER_CLS)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Iterable[Dict[str, Any]]:
        manager: NPCZoneManager = cast(NPCZoneManager, proxy)

        # Sanity checks
        spawn_group = manager.get('NPCSpawnEntriesContainerObject', 0, None)
        count_volumes = manager.get('LinkedZoneVolumes', 0, None)
        if not spawn_group or not spawn_group.value.value or not count_volumes:
            yield from ()
            return

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
    def get_category_name(cls) -> str:
        return 'biomes'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, BIOME_ZONE_VOLUME_CLS)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Iterable[Dict[str, Any]]:
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
        yield data

    @classmethod
    def _extract_temperature_data(cls, proxy: BiomeZoneVolume, data: Dict[str, Any]):
        ## Absolute
        if proxy.has_override('AbsoluteTemperatureOverride'):
            data['temperature']['override'] = proxy.AbsoluteTemperatureOverride[0]
        if proxy.has_override('AbsoluteMaxTemperature') or proxy.has_override('AbsoluteMinTemperature'):
            data['temperature']['range'] = (proxy.AbsoluteMinTemperature[0], proxy.AbsoluteMaxTemperature[0])
        ## Pre-offset
        if proxy.has_override('PreOffsetTemperatureMultiplier') or proxy.has_override(
                'PreOffsetTemperatureExponent') or proxy.has_override('PreOffsetTemperatureAddition'):
            data['temperature']['preOffset'] = (None, proxy.PreOffsetTemperatureMultiplier[0],
                                                proxy.PreOffsetTemperatureExponent[0], proxy.PreOffsetTemperatureAddition[0])
        ## Above offset
        if proxy.has_override('AboveTemperatureOffsetThreshold') or proxy.has_override(
                'AboveTemperatureOffsetMultiplier') or proxy.has_override('AboveTemperatureOffsetExponent'):
            data['temperature']['aboveOffset'] = (
                proxy.AboveTemperatureOffsetThreshold[0],
                proxy.AboveTemperatureOffsetMultiplier[0],
                proxy.AboveTemperatureOffsetExponent[0],
                None,
            )
        ## Below offset
        if proxy.has_override('BelowTemperatureOffsetThreshold') or proxy.has_override(
                'BelowTemperatureOffsetMultiplier') or proxy.has_override('BelowTemperatureOffsetExponent'):
            data['temperature']['belowOffset'] = (
                proxy.BelowTemperatureOffsetThreshold[0],
                proxy.BelowTemperatureOffsetMultiplier[0],
                proxy.BelowTemperatureOffsetExponent[0],
                None,
            )
        ## Final
        if proxy.has_override('FinalTemperatureMultiplier') or proxy.has_override(
                'FinalTemperatureExponent') or proxy.has_override('FinalTemperatureAddition'):
            data['temperature']['final'] = (None, proxy.FinalTemperatureMultiplier[0], proxy.FinalTemperatureExponent[0],
                                            proxy.FinalTemperatureAddition[0])

    @classmethod
    def _extract_wind_data(cls, proxy: BiomeZoneVolume, data: Dict[str, Any]):
        ## Absolute
        if proxy.has_override('AbsoluteWindOverride'):
            data['wind']['override'] = proxy.AbsoluteWindOverride[0]
        ## Pre-offset
        if proxy.has_override('PreOffsetWindMultiplier') or proxy.has_override('PreOffsetWindExponent') or proxy.has_override(
                'PreOffsetWindAddition'):
            data['wind']['preOffset'] = (
                None,
                proxy.PreOffsetWindMultiplier[0],
                proxy.PreOffsetWindExponent[0],
                proxy.PreOffsetWindAddition[0],
            )
        ## Above offset
        if proxy.has_override('AboveWindOffsetThreshold') or proxy.has_override(
                'AboveWindOffsetMultiplier') or proxy.has_override('AboveWindOffsetExponent'):
            data['wind']['aboveOffset'] = (
                proxy.AboveWindOffsetThreshold[0],
                proxy.AboveWindOffsetMultiplier[0],
                proxy.AboveWindOffsetExponent[0],
                None,
            )
        ## Below offset
        if proxy.has_override('BelowWindOffsetThreshold') or proxy.has_override(
                'BelowWindOffsetMultiplier') or proxy.has_override('BelowWindOffsetExponent'):
            data['wind']['belowOffset'] = (
                proxy.BelowWindOffsetThreshold[0],
                proxy.BelowWindOffsetMultiplier[0],
                proxy.BelowWindOffsetExponent[0],
                None,
            )
        ## Final
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
    def get_category_name(cls) -> str:
        return 'lootCrates'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        if not inherits_from(export, SUPPLY_CRATE_SPAWN_VOLUME_CLS):
            return False
        return bool(export.properties.get_property('bIsEnabled', fallback=True))

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Iterable[Dict[str, Any]]:
        spawner: SupplyCrateSpawningVolume = cast(SupplyCrateSpawningVolume, proxy)

        # Sanity checks
        class_entries = spawner.get('LinkedSupplyCrateEntries', 0, None)
        spawn_points = spawner.get('LinkedSpawnPointEntries', 0, None)
        if not class_entries or not spawn_points:
            yield from ()
            return

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
        yield dict(
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
    def get_category_name(cls) -> str:
        return 'radiationVolumes'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        if not inherits_from(export, TOGGLE_PAIN_VOLUME_CLS):
            return False
        # Check if disabled
        is_enabled = bool(export.properties.get_property('bPainCausing', fallback=True))
        if not is_enabled:
            return False
        # Check if this is a radiation volume
        damage_type = export.properties.get_property('DamageType', fallback=None)
        if damage_type and damage_type.value.value.fullname == DAMAGE_TYPE_RADIATION_PKG:
            return True
        return False

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Iterable[Dict[str, Any]]:
        volume: TogglePainVolume = cast(TogglePainVolume, proxy)
        volume_bounds = get_volume_bounds(volume)
        yield dict(
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
    def get_category_name(cls) -> str:
        return 'notes'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, EXPLORER_CHEST_BASE_CLS)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Iterable[Dict[str, Any]]:
        note: ExplorerNote = cast(ExplorerNote, proxy)
        data = dict(
            noteIndex=note.ExplorerNoteIndex[0],
            hidden=not note.bIsVisible[0],
            **get_actor_location_vector(proxy).format_for_json(),
        )
        # Remove the "hidden" mark if not hidden
        if not data['hidden']:
            del data['hidden']
        yield data

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        data['lat'] = map_info.lat.from_units(data['y'])
        data['long'] = map_info.long.from_units(data['x'])


class HLNAGlitchExport(GenericActorListExport):
    @classmethod
    def get_category_name(cls) -> str:
        return 'glitches'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, '/Script/ShooterGame.PointOfInterestManagerList')

    @classmethod
    def extract_single(cls, export: ExportTableItem) -> Union[UEBase, Dict[str, Any]]:
        # TODO: Unverified value below:
        index = export.properties.get_property('Specific Unlocked Explorer Note Index', fallback=-1)
        return dict(
            noteIndex=index,
            **get_actor_location_vector(export.value.value).format_for_json(),
        )


class OilVeinExport(GenericActorExport):
    CLASSES = (OIL_VEIN_CLS, )
    CATEGORY = 'oilVeins'


class WaterVeinExport(GenericActorExport):
    CLASSES = (WATER_VEIN_CLS, )
    CATEGORY = 'waterVeins'


class LunarOxygenVentExport(GenericActorExport):
    CLASSES = (LUNAR_OXYGEN_VENT_GEN1_CLS, )
    CATEGORY = 'lunarOxygenVents'


class OilVentExport(GenericActorExport):
    CLASSES = (OIL_VENT_GEN1_CLS, )
    CATEGORY = 'oilVents'


class GasVeinExport(GenericActorExport):
    CLASSES = (GAS_VEIN_CLS, GAS_VEIN_GEN1_CLS)
    CATEGORY = 'gasVeins'


class ChargeNodeExport(GenericActorExport):
    CLASSES = (CHARGE_NODE_CLS, )
    CATEGORY = 'chargeNodes'


class WildPlantSpeciesZExport(GenericActorExport):
    CLASSES = (WILD_PLANT_SPECIES_Z_CLS, )
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


class MagmasaurNests(GenericActorListExport):
    TAGS = ('MagmasaurNestSpawns', )
    CATEGORY = 'magmasaurNests'


EXPORTS: Dict[str, List[Type[MapGathererBase]]] = {
    'world_settings': [
        # Core
        WorldSettingsExport,
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
    for _, helpers in EXPORTS.items():
        for helper in helpers:
            try:
                if helper.is_export_eligible(export):
                    return helper
            except (MissingParent, AssetLoadException):
                continue

    return None


def find_gatherer_by_category_name(category: str) -> Optional[Type[MapGathererBase]]:
    for _, helpers in EXPORTS.items():
        for helper in helpers:
            if helper.get_category_name() == category:
                return helper

    return None
