from logging import NullHandler, getLogger

from config import get_global_config
from ue.asset import ExportTableItem
from ue.hierarchy import MissingParent, inherits_from
from ue.loader import AssetNotFound

from .actor_lists import extract_actor_list
from .biomes import extract_biome_zone_volume
from .common import ACTOR_FIELD_MAP, ACTOR_LIST_TAG_FIELD_MAP, format_location_for_export, \
    get_actor_worldspace_location, get_volume_worldspace_bounds
from .consts import CHARGE_NODE_CLS, DAMAGE_TYPE_RADIATION_PKG, EXPLORER_CHEST_BASE_CLS, \
    GAS_VEIN_CLS, OIL_VEIN_CLS, WATER_VEIN_CLS, WILD_PLANT_SPECIES_Z_CLS
from .map import WorldData
from .npc_spawns import extract_npc_zone_manager
from .supply_drops import extract_supply_crate_volume
from .types import BiomeZoneVolume, CustomActorList, ExplorerNote, NPCZoneManager, SupplyCrateSpawningVolume, TogglePainVolume

logger = getLogger(__name__)
logger.addHandler(NullHandler())


def is_export_extractable(export: ExportTableItem) -> bool:
    for exportable_klass in PROXY_TYPE_MAP.keys():
        try:
            if inherits_from(export, exportable_klass):
                return True
        except (MissingParent, AssetNotFound):
            continue
    return False


def _export_npc_zone_manager(world: WorldData, proxy: NPCZoneManager):
    if not get_global_config().export_wiki.ExportSpawnData or not proxy.bEnabled[0].value:
        return

    data = extract_npc_zone_manager(world, proxy)
    if not data:
        return

    world.spawns.append(data)
    if data['spawnGroup'] not in world.spawnGroups:
        world.spawnGroups.append(data['spawnGroup'])


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
    if not getattr(proxy, 'DamageType',
                   None) or str(proxy.DamageType[0].value.value.namespace.value.name) != DAMAGE_TYPE_RADIATION_PKG:
        return
    bounds = get_volume_worldspace_bounds(proxy)
    world.radiationVolumes.append({
        **format_location_for_export(bounds, world.latitude, world.longitude), 'immune':
        proxy.ActorClassesToExclude[0]
    })


def _export_actor_location(world: WorldData, proxy):
    if not get_global_config().export_wiki.ExportVeinLocations:
        return

    data_field_name = ACTOR_FIELD_MAP.get(proxy.get_ue_type(), None)
    if not data_field_name:
        logger.debug(f'Won\'t export a vein: missing type mapping for "{proxy.get_ue_type()}".')
        return

    data = get_actor_worldspace_location(proxy)
    data = format_location_for_export(data, world.latitude, world.longitude)
    if isinstance(proxy, ExplorerNote):
        data = {**data, 'noteIndex': proxy.ExplorerNoteIndex[0]}

    getattr(world, data_field_name).append(data)


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
    NPCZoneManager.get_ue_type(): _export_npc_zone_manager,
    BiomeZoneVolume.get_ue_type(): _export_biome_zone_volume,
    SupplyCrateSpawningVolume.get_ue_type(): _export_supply_crate_volume,
    TogglePainVolume.get_ue_type(): _export_pain_volume,
    CustomActorList.get_ue_type(): _export_actor_list,
    ExplorerNote.get_ue_type(): _export_actor_location,
    OIL_VEIN_CLS: _export_actor_location,
    WATER_VEIN_CLS: _export_actor_location,
    GAS_VEIN_CLS: _export_actor_location,
    CHARGE_NODE_CLS: _export_actor_location,
    WILD_PLANT_SPECIES_Z_CLS: _export_actor_location,
}

__all__ = ['PROXY_TYPE_MAP']
