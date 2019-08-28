from logging import NullHandler, getLogger
from typing import *

from ue.properties import ArrayProperty

from .map import WorldData
from .types import (ZONE_MANAGER_EXPORTED_PROPERTIES, NPCZoneManager,
                    PrimalWorldSettings)
from .utils import (export_properties_from_proxy, format_location_for_export,
                    get_actor_worldspace_location,
                    get_volume_worldspace_bounds)

logger = getLogger(__name__)
logger.addHandler(NullHandler())


def export_npc_zone_manager(world: WorldData, proxy: NPCZoneManager, log_identifier: str = 'a map') -> Optional[dict]:
    if not getattr(proxy, 'NPCSpawnEntriesContainerObject', None):
        logger.debug(
            f'Broken NPC zone manager found in {log_identifier}: no spawn entries container reference.'
        )
        return None
    if not proxy.NPCSpawnEntriesContainerObject[0].value.value:
        logger.debug(
            f'Broken NPC zone manager found in {log_identifier}: spawn entries container reference points to nothing.'
        )
        return None
    if not getattr(proxy, 'LinkedZoneVolumes', None):
        logger.debug(
            f'Broken NPC zone manager found in {log_identifier}: no zone volumes linked.'
        )
        return None

    data = dict(export_properties_from_proxy(proxy, ZONE_MANAGER_EXPORTED_PROPERTIES))
    # Export zone volumes and check again if there's at least one linked
    data['locations'] = [
        format_location_for_export(bounds, world.latitude, world.longitude)
        for bounds in gather_zone_volumes_bounds(proxy.LinkedZoneVolumes[0], log_identifier)
    ]
    if not data['locations']:
        # We have probably already printed a warning.
        return None

    # Export spawn points or locations
    if getattr(proxy, 'SpawnPointOverrides', None):
        data['spawnPoints'] = [
            format_location_for_export(point, world.latitude, world.longitude)
            for point in gather_zone_spawn_points(proxy.SpawnPointOverrides[0], log_identifier)
        ]
    elif getattr(proxy, 'LinkedZoneSpawnVolumeEntries', None):
        data['spawnLocations'] = [
            {
                'weight': weight,
                **format_location_for_export(bounds, world.latitude, world.longitude)
            }
            for weight, bounds in gather_zone_spawn_volumes_bounds(proxy.LinkedZoneSpawnVolumeEntries[0], log_identifier)
        ]
    else:
        logger.debug(
            f'Broken NPC zone manager found in {log_identifier}: no spawn zone entries nor spawn points linked.'
        )
        return None

    return data


def gather_zone_volumes_bounds(volumes: ArrayProperty, log_identifier: str = 'a map'):
    for zone_volume in volumes.values:
        zone_volume = zone_volume.value.value
        if not zone_volume:
            logger.debug(
                f'Broken NPC zone manager found in {log_identifier}: zone volume reference does not point anywhere.'
            )
            continue

        yield get_volume_worldspace_bounds(zone_volume)


def gather_zone_spawn_points(points: ArrayProperty, log_identifier: str = 'a map'):
    for marker in points.values:
        marker = marker.value.value
        if not marker:
            logger.debug(
                f'Broken NPC zone manager found in {log_identifier}: spawn marker reference does not point anywhere.'
            )
            continue

        yield get_actor_worldspace_location(marker)[:2]


def gather_zone_spawn_volumes_bounds(entries: ArrayProperty, log_identifier: str = 'a map'):
    for entry in entries.values:
        entry_data = entry.as_dict()
        entry_weight = entry_data['EntryWeight'].value
        spawn_volume = entry_data["LinkedZoneSpawnVolume"].value.value
        if not spawn_volume:
            logger.debug(
                f'Broken NPC zone manager found in {log_identifier}: spawn zone volume reference does not point anywhere.'
            )
            continue

        yield entry_weight, get_volume_worldspace_bounds(spawn_volume)

def gather_random_npc_class_weights(world_settings: PrimalWorldSettings):
    if not getattr(world_settings, 'NPCRandomSpawnClassWeights', None):
        return

    for random_class_weight in world_settings.NPCRandomSpawnClassWeights[0].values:
        data = random_class_weight.as_dict()
        yield {
            'from': data['FromClass'],
            'to': data['ToClasses'],
            'chances': data['Weights']
        }
