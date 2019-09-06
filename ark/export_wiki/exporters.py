from logging import NullHandler, getLogger

from config import get_global_config

from .actor_lists import extract_actor_list
from .biomes import extract_biome_zone_volume
from .common import (ACTOR_FIELD_MAP, ACTOR_LIST_TAG_FIELD_MAP,
                     DAMAGE_TYPE_RADIATION, format_location_for_export,
                     get_actor_worldspace_location,
                     get_volume_worldspace_bounds)
from .map import WorldData
from .npc_spawns import extract_npc_zone_manager
from .supply_drops import extract_supply_crate_volume
from .types import (BiomeZoneVolume, CustomActorList, NPCZoneManager,
                    SupplyCrateSpawningVolume, TogglePainVolume, VeinBase)

logger = getLogger(__name__)
logger.addHandler(NullHandler())

def _export_npc_zone_manager(world: WorldData, proxy: NPCZoneManager):
    if not get_global_config().export_wiki.ExportSpawnData or not proxy.bEnabled[0].value:
        return

    data = extract_npc_zone_manager(world, proxy)
    if not data:
        return

    world.spawns.append(data)
    spawn_group = data['spawnGroup'].format_for_json()
    if spawn_group not in world.spawnGroups:
        world.spawnGroups.append(spawn_group)


def _export_biome_zone_volume(world: WorldData, proxy: BiomeZoneVolume):
    if not get_global_config().export_wiki.ExportBiomeData or proxy.bHidden[0].value:
        return

    data = extract_biome_zone_volume(world, proxy)
    if data:
        world.biomes.append(data)


def _export_supply_crate_volume(world: WorldData, proxy: SupplyCrateSpawningVolume):
    if not get_global_config().export_wiki.ExportSupplyCrateData or proxy.bHidden[0].value:
        return

    data = extract_supply_crate_volume(world, proxy)
    if data:
        world.lootCrates.append(data)


def _export_pain_volume(world: WorldData, proxy: TogglePainVolume):
    if not getattr(proxy, 'DamageType', None) or str(proxy.DamageType[0].value.value.namespace.value.name) != DAMAGE_TYPE_RADIATION:
        return
    bounds = get_volume_worldspace_bounds(proxy)
    world.radiationVolumes.append({
        **format_location_for_export(bounds, world.latitude, world.longitude),
        'immune': proxy.ActorClassesToExclude[0]
    })

def _export_vein_location(world: WorldData, proxy: VeinBase):
    if not get_global_config().export_wiki.ExportVeinLocations:
        return

    data_field_name = ACTOR_FIELD_MAP.get(proxy.get_ue_type(), None)
    if not data_field_name:
        logger.debug(f'Won\'t export a vein: missing type mapping for "{proxy.get_ue_type()}".')
        return

    data = get_actor_worldspace_location(proxy)
    getattr(world, data_field_name).append(format_location_for_export(data, world.latitude, world.longitude))

def _export_actor_list(world: WorldData, proxy: CustomActorList):
    if not get_global_config().export_wiki.ExportNestLocations or not getattr(proxy, 'CustomTag', None):
        return

    list_tag = str(proxy.CustomTag[0])
    data_field_name = ACTOR_LIST_TAG_FIELD_MAP.get(list_tag, None)
    if not data_field_name:
        logger.debug(f'Won\'t export an actor list: missing tag mapping for "{list_tag}".')
        return
    getattr(world, data_field_name).extend(extract_actor_list(world, proxy))


PROXY_TYPE_MAP = {
    '/Script/ShooterGame.NPCZoneManager': _export_npc_zone_manager,
    '/Script/ShooterGame.BiomeZoneVolume': _export_biome_zone_volume,
    '/Script/ShooterGame.SupplyCrateSpawningVolume': _export_supply_crate_volume,
    '/Script/ShooterGame.TogglePainVolume': _export_pain_volume,
    '/Script/ShooterGame.CustomActorList': _export_actor_list,
    '/Game/ScorchedEarth/Structures/OilPump/OilVein_Base_BP.OilVein_Base_BP_C': _export_vein_location,
    '/Game/ScorchedEarth/Structures/WaterWell/WaterVein_Base_BP.WaterVein_Base_BP_C': _export_vein_location,
}

__all__ = [
    'PROXY_TYPE_MAP'
]
