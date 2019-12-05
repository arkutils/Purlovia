from typing import Any, Dict, Optional, Type

from ue.asset import ExportTableItem
from ue.hierarchy import MissingParent, inherits_from
from ue.loader import AssetLoadException
from ue.proxy import UEProxyStructure

from .base import MapGathererBase
from .common import get_actor_location_vector, get_volume_bounds, proxy_properties_as_dict
from .consts import ACTOR_CLS, BIOME_ZONE_VOLUME_CLS, CHARGE_NODE_CLS, EXPLORER_CHEST_BASE_CLS, \
    GAS_VEIN_CLS, NPC_ZONE_MANAGER_CLS, OIL_VEIN_CLS, SUPPLY_CRATE_SPAWN_VOLUME_CLS, \
    TOGGLE_PAIN_VOLUME_CLS, WATER_VEIN_CLS, WILD_PLANT_SPECIES_Z_CLS
from .types import BIOME_VOLUME_ALWAYS_EXPORTED_PROPERTIES, BIOME_VOLUME_EXPORTED_PROPERTIES, \
    SUPPLY_DROP_ALWAYS_EXPORTED_PROPERTIES, SUPPLY_DROP_EXPORTED_PROPERTIES, ZONE_MANAGER_EXPORTED_PROPERTIES


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
    def sorting_key(cls, data: Dict[str, Any]) -> Any:
        return data['x']


# TODO: actor lists (nests) are missing


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
        elif getattr(proxy, 'LinkedZoneSpawnVolumeEntries', None):
            data['spawnLocations'] = list(cls._extract_spawn_volumes(proxy.LinkedZoneSpawnVolumeEntries[0]))
        # No spawning data, broken.
        else:
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
    def sorting_key(cls, data: Dict[str, Any]) -> Any:
        return data['spawnGroup']


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

        return {
            **always_present,
            **may_be_present, 'boxes': dict(min=volume_bounds[0], max=volume_bounds[1])
        }

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Any:
        return (data['BiomeZoneName'], data['boxes']['min']['x'])


class LootCrateSpawnExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'lootCrates'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        return inherits_from(export, SUPPLY_CRATE_SPAWN_VOLUME_CLS)

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Optional[Dict[str, Any]]:
        # Sanity checks
        if not getattr(proxy, 'LinkedSupplyCrateEntries', None):
            return None
        if not getattr(proxy, 'LinkedSpawnPointEntries', None):
            return None

        # Export properties
        return dict(
            crateClasses=sorted(cls._convert_crate_classes(proxy.LinkedSupplyCrateEntries[0])),
            crateLocations=list(cls._extract_spawn_points(proxy.LinkedSpawnPointEntries[0])),
            **proxy_properties_as_dict(proxy, key_list=SUPPLY_DROP_ALWAYS_EXPORTED_PROPERTIES),
            **proxy_properties_as_dict(proxy, key_list=SUPPLY_DROP_EXPORTED_PROPERTIES, only_overriden=True)
        )
    
    @classmethod
    def _convert_crate_classes(cls, entries):
        for entry in entries.values:
            yield entry.as_dict()['CrateTemplate'].format_for_json()
    
    @classmethod
    def _extract_spawn_points(cls, entries):
        for entry in entries.values:
            marker = entry.as_dict()['LinkedSpawnPoint'].value.value
            if not marker:
                continue
            yield get_actor_location_vector(marker).format_for_json()

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Any:
        return (len(data['crateClasses']), data['crateClasses'])


class RadiationZoneExport(MapGathererBase):
    @classmethod
    def get_category_name(cls) -> str:
        return 'radiationVolumes'

    @classmethod
    def is_export_eligible(cls, export: ExportTableItem) -> bool:
        if not inherits_from(export, TOGGLE_PAIN_VOLUME_CLS):
            return False
        # Check if this is a radiation volume
        if export.properties.get_property('DamageType').format_for_json() == DAMAGE_TYPE_RADIATION_PKG:
            return True
        return False

    @classmethod
    def extract(cls, proxy: UEProxyStructure) -> Optional[Dict[str, Any]]:
        volume_bounds = get_volume_bounds(proxy)
        return dict(
            bounds=dict(min=volume_bounds[0], max=volume_bounds[1]),
            immune=[ref.format_for_json() for ref in proxy.ActorClassesToExclude[0].values],
        )

    @classmethod
    def sorting_key(cls, data: Dict[str, Any]) -> Any:
        return data['bounds']['min']['x']


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
    def sorting_key(cls, data: Dict[str, Any]) -> Any:
        return data['noteIndex']


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
