from logging import NullHandler, getLogger

from config import get_global_config

from .biomes import export_biome_zone_volume
from .consts import (ACTOR_FIELD_MAP, ACTOR_LIST_TAG_FIELD_MAP,
                     DAMAGE_TYPE_RADIATION)
from .map import WorldData
from .nests import export_nest_locations
from .npc_spawns import export_npc_zone_manager
from .supply_drops import export_supply_crate_volume
from .types import (BiomeZoneVolume, CustomActorList, NPCZoneManager,
                    SupplyCrateSpawningVolume, TogglePainVolume, VeinBase)
from .utils import (format_location_for_export, get_actor_worldspace_location,
                    get_volume_worldspace_bounds)

logger = getLogger(__name__)
logger.addHandler(NullHandler())

__all__ = [
    'PROXY_TYPE_MAP'
]

def _export_npc_zone_manager(world: WorldData, proxy: NPCZoneManager, log_identifier: str = 'a map'):
    if not get_global_config().wiki_settings.ExportSpawnData or not proxy.bEnabled[0].value:
        return

    data = export_npc_zone_manager(world, proxy, log_identifier)
    if data:
        world.spawns.append(data)
        spawn_group = data['spawnGroup'].format_for_json()
        if spawn_group not in world.spawnGroups:
            world.spawnGroups.append(spawn_group)


def _export_biome_zone_volume(world: WorldData, proxy: BiomeZoneVolume, log_identifier: str = 'a map'):
    if not get_global_config().wiki_settings.ExportBiomeData or proxy.bHidden[0].value:
        return

    data = export_biome_zone_volume(world, proxy, log_identifier)
    if data:
        world.biomes.append(data)


def _export_supply_crate_volume(world: WorldData, proxy: SupplyCrateSpawningVolume, log_identifier: str = 'a map'):
    if not get_global_config().wiki_settings.ExportSupplyCrateData or proxy.bHidden[0].value:
        return

    data = export_supply_crate_volume(world, proxy, log_identifier)
    if data:
        world.lootCrates.append(data)


def _export_pain_volume(world: WorldData, proxy: TogglePainVolume, log_identifier: str = 'a map'):
    if not getattr(proxy, 'DamageType', None):
        return
    if str(proxy.DamageType[0].value.value.namespace.value.name) != DAMAGE_TYPE_RADIATION:
        return

    bounds = get_volume_worldspace_bounds(proxy)
    bounds = format_location_for_export(bounds, world.latitude, world.longitude)
    world.radiationVolumes.append({
        **bounds,
        'immune': proxy.ActorClassesToExclude[0]
    })

def _export_vein_location(world: WorldData, proxy: VeinBase, log_identifier: str = 'a map'):
    if not get_global_config().wiki_settings.ExportVeinLocations:
        return

    data_field_name = ACTOR_FIELD_MAP.get(proxy.get_ue_type(), None)
    if not data_field_name:
        logger.debug(f'A vein in {log_identifier} will not be exported: missing vein type mapping for "{proxy.get_ue_type()}".')
        return

    data = get_actor_worldspace_location(proxy)
    data = format_location_for_export(data, world.latitude, world.longitude)
    getattr(world, data_field_name).append(data)

def _export_nest_locations(world: WorldData, proxy: CustomActorList, log_identifier: str = 'a map'):
    if not get_global_config().wiki_settings.ExportNestLocations:
        return
    if not getattr(proxy, 'CustomTag', None):
        logger.debug(f'Skipping {log_identifier}: no tag.')
        return

    list_tag = str(proxy.CustomTag[0])
    data_field_name = ACTOR_LIST_TAG_FIELD_MAP.get(list_tag, None)
    if not data_field_name:
        logger.debug(f'A nest list in {log_identifier} will not be exported: missing tag mapping for "{list_tag}".')
        return

    data = list(export_nest_locations(world, proxy, log_identifier))
    target_field: list = getattr(world, data_field_name)
    target_field += data


PROXY_TYPE_MAP = {
    '/Script/ShooterGame.NPCZoneManager': _export_npc_zone_manager,
    '/Script/ShooterGame.BiomeZoneVolume': _export_biome_zone_volume,
    '/Script/ShooterGame.SupplyCrateSpawningVolume': _export_supply_crate_volume,
    '/Script/ShooterGame.TogglePainVolume': _export_pain_volume,
    '/Script/ShooterGame.CustomActorList': _export_nest_locations,
    '/Game/ScorchedEarth/Structures/OilPump/OilVein_Base_BP.OilVein_Base_BP_C': _export_vein_location,
    '/Game/ScorchedEarth/Structures/WaterWell/WaterVein_Base_BP.WaterVein_Base_BP_C': _export_vein_location,
}
