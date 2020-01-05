from typing import Any, Dict, Optional, Type

from ue.asset import ExportTableItem
from ue.hierarchy import MissingParent, inherits_from
from ue.loader import AssetLoadException
from ue.proxy import UEProxyStructure

from .base import MapGathererBase
from .common import convert_box_bounds_for_export, get_actor_location_vector, get_volume_bounds, proxy_properties_as_dict
from .consts import ACTOR_CLS, BIOME_ZONE_VOLUME_CLS, CHARGE_NODE_CLS, DAMAGE_TYPE_RADIATION_PKG, \
    EXPLORER_CHEST_BASE_CLS, GAS_VEIN_CLS, NPC_ZONE_MANAGER_CLS, OIL_VEIN_CLS, PRIMAL_WORLD_SETTINGS_CLS, \
    SUPPLY_CRATE_SPAWN_VOLUME_CLS, TOGGLE_PAIN_VOLUME_CLS, WATER_VEIN_CLS, WILD_PLANT_SPECIES_Z_CLS
from .map import MapInfo
from .types import BIOME_VOLUME_ALWAYS_EXPORTED_PROPERTIES, BIOME_VOLUME_EXPORTED_PROPERTIES, \
    WORLD_SETTINGS_EXPORTED_PROPERTIES, ZONE_MANAGER_EXPORTED_PROPERTIES, SupplyCrateSpawningVolume


class GenericActorExport(MapGathererBase):
    KLASS = ACTOR_CLS

    @classmethod
    def get_category_name(cls) -> str:
        return 'otherLocations'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, cls.KLASS)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Optional[Dict[str, Any]]:
        return get_actor_location_vector(proxy).format_for_json()

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        data['lat'] = map_info.lat.from_units(data['y'])
        data['long'] = map_info.lat.from_units(data['x'])

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Any:
        return (data['x'], data['y'], data['z'])


# TODO: actor lists (nests) are missing

class WorldSettingsExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'worldSettings'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, PRIMAL_WORLD_SETTINGS_CLS) and not getattr(export.asset, 'tile_info', None)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Optional[Dict[str, Any]]:
        return dict(
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
            **proxy_properties_as_dict(proxy, WORLD_SETTINGS_EXPORTED_PROPERTIES)
        )

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        pass

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Any:
        return 1

class NPCZoneManagerExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'spawns'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, NPC_ZONE_MANAGER_CLS)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Optional[Dict[str, Any]]:
        # Sanity checks
        if not getattr(proxy, 'NPCSpawnEntriesContainerObject', None):
            return None
        if not getattr(proxy, 'LinkedZoneVolumes', None):
            return None
        if not proxy.NPCSpawnEntriesContainerObject[0].value.value:
            return None

        # Export properties
        data = proxy_properties_as_dict(proxy, key_list=ZONE_MANAGER_EXPORTED_PROPERTIES)
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
            return None

        return data
    
    @classmethod
    def _extract_counting_volumes(cls, volumes):
        for zone_volume in volumes.values:
            zone_volume = zone_volume.value.value
            if not zone_volume:
                continue
            bounds = get_volume_bounds(zone_volume)
            yield dict(start=bounds[0], end=bounds[1])
    
    @classmethod
    def _extract_spawn_points(cls, markers):
        for marker in markers.values:
            marker = marker.value.value
            if not marker:
                continue
            yield get_actor_location_vector(marker).format_for_json()
    
    @classmethod
    def _extract_spawn_volumes(cls, entries):
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
                point['long'] = map_info.lat.from_units(point['x'])

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Any:
        return (data['spawnGroup'], len(data['locations']))


class BiomeZoneExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'biomes'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, BIOME_ZONE_VOLUME_CLS)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Optional[Dict[str, Any]]:
        always_present = proxy_properties_as_dict(proxy, key_list=BIOME_VOLUME_ALWAYS_EXPORTED_PROPERTIES, only_overriden=False)
        may_be_present = proxy_properties_as_dict(proxy, key_list=BIOME_VOLUME_EXPORTED_PROPERTIES, only_overriden=True)
        volume_bounds = get_volume_bounds(proxy)

        data = dict(**always_present, **may_be_present)
        data['start'] = volume_bounds[0]
        data['end'] = volume_bounds[1]
        return data

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        convert_box_bounds_for_export(map_info, data)

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Any:
        return (data['BiomeZoneName'], data['start']['x'], data['start']['y'], data['start']['z'])


class LootCrateSpawnExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'lootCrates'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, SUPPLY_CRATE_SPAWN_VOLUME_CLS)

    @classmethod
    def extract(cls, proxy: SupplyCrateSpawningVolume) -> Optional[Dict[str, Any]]:
        # Sanity checks
        if not getattr(proxy, 'LinkedSupplyCrateEntries', None):
            return None
        if not getattr(proxy, 'LinkedSpawnPointEntries', None):
            return None

        # Make range tuples of numerical properties.
        ranges = dict(
            delayBeforeFirst=(
                proxy.DelayBeforeFirstCrate[0].format_for_json(), proxy.MaxDelayBeforeFirstCrate[0].format_for_json()
            ),
            intervalBetweenSpawns=(
                proxy.IntervalBetweenCrateSpawns[0].format_for_json(), proxy.MaxIntervalBetweenCrateSpawns[0].format_for_json()
            ),
            intervalBetweenMaxedSpawns=(
                proxy.IntervalBetweenMaxedCrateSpawns[0].format_for_json(), proxy.MaxIntervalBetweenMaxedCrateSpawns[0].format_for_json()
            )
        )

        # Single-player overrides. Export only if changed.
        if proxy.has_override('SP_IntervalBetweenCrateSpawns') or proxy.has_override('SP_MaxIntervalBetweenCrateSpawns'):
            ranges['intervalBetweenSpawnsSP'] = (
                proxy.SP_IntervalBetweenCrateSpawns[0].format_for_json(), proxy.SP_MaxIntervalBetweenCrateSpawns[0].format_for_json()
            )
        if proxy.has_override('SP_IntervalBetweenMaxedCrateSpawns') or proxy.has_override('SP_MaxIntervalBetweenMaxedCrateSpawns'):
            ranges['intervalBetweenMaxedSpawnsSP'] = (
                proxy.SP_IntervalBetweenMaxedCrateSpawns[0].format_for_json(), proxy.SP_MaxIntervalBetweenMaxedCrateSpawns[0].format_for_json()
            )

        # Combine all properties into a single dict
        return dict(
            maxCrateNumber=proxy.MaxNumCrates[0].format_for_json(),
            crateClasses=sorted(cls._convert_crate_classes(proxy.LinkedSupplyCrateEntries[0])),
            crateLocations=list(cls._extract_spawn_points(proxy.LinkedSpawnPointEntries[0])),
            minTimeBetweenSpawnsAtSamePoint=proxy.MinTimeBetweenCrateSpawnsAtSamePoint[0].format_for_json(),
            **ranges
        )
    
    @classmethod
    def _convert_crate_classes(cls, entries):
        for entry in entries.values:
            klass = entry.as_dict()['CrateTemplate'].format_for_json()
            if not klass:
                continue
            yield klass
    
    @classmethod
    def _extract_spawn_points(cls, entries):
        for entry in entries.values:
            marker = entry.as_dict()['LinkedSpawnPoint'].value.value
            if not marker:
                continue
            yield get_actor_location_vector(marker).format_for_json()

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        for location in data['crateLocations']:
            location['lat'] = map_info.lat.from_units(location['y'])
            location['long'] = map_info.long.from_units(location['x'])

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Any:
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
        if hasattr(export.properties, 'DamageType') and export.properties.get_property('DamageType').format_for_json() == DAMAGE_TYPE_RADIATION_PKG:
            return True
        return False

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Optional[Dict[str, Any]]:
        volume_bounds = get_volume_bounds(proxy)
        return dict(
            start=volume_bounds[0],
            end=volume_bounds[1],
            immune=[ref.format_for_json() for ref in proxy.ActorClassesToExclude[0].values],
        )

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        convert_box_bounds_for_export(map_info, data)

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Any:
        return (data['start']['x'], data['start']['y'], data['start']['z'])


class ExplorerNoteExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'notes'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, EXPLORER_CHEST_BASE_CLS)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Optional[Dict[str, Any]]:
        return dict(noteIndex=proxy.ExplorerNoteIndex[0].format_for_json(), **get_actor_location_vector(proxy).format_for_json())

    @classmethod
    def before_saving(cls, map_info: MapInfo, data: Dict[str, Any]):
        data['lat'] = map_info.lat.from_units(data['y'])
        data['long'] = map_info.lat.from_units(data['x'])

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Any:
        return (data['noteIndex'], data['x'], data['y'], data['z'])


class OilVeinExport(GenericActorExport):
    KLASS = OIL_VEIN_CLS

    @classmethod
    def get_category_name(cls) -> str:
        return 'oilVeins'


class WaterVeinExport(GenericActorExport):
    KLASS = WATER_VEIN_CLS

    @classmethod
    def get_category_name(cls) -> str:
        return 'waterVeins'


class GasVeinExport(GenericActorExport):
    KLASS = GAS_VEIN_CLS

    @classmethod
    def get_category_name(cls) -> str:
        return 'gasVeins'


class ChargeNodeExport(GenericActorExport):
    KLASS = CHARGE_NODE_CLS

    @classmethod
    def get_category_name(cls) -> str:
        return 'chargeNodes'


class WildPlantSpeciesZExport(GenericActorExport):
    KLASS = WILD_PLANT_SPECIES_Z_CLS

    @classmethod
    def get_category_name(cls) -> str:
        return 'plantZNodes'


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
    # Aberration
    GasVeinExport,
    ChargeNodeExport,
    WildPlantSpeciesZExport,
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
