from logging import NullHandler, getLogger
from typing import *

from ark.export_wiki.map import MapData
from ark.export_wiki.types import (ZONE_MANAGER_EXPORTED_PROPERTIES,
                                   NPCZoneManager)
from ark.export_wiki.utils import (export_properties_from_proxy,
                                   format_location_for_export,
                                   get_volume_worldspace_bounds)
from ue.properties import ArrayProperty

logger = getLogger(__name__)
logger.addHandler(NullHandler())


def export_npc_zone_manager(world: MapData, proxy: NPCZoneManager, log_identifier: str = 'a map') -> Optional[dict]:
    if not getattr(proxy, 'NPCSpawnEntriesContainerObject', None):
        logger.warning(
            f'Broken NPC zone manager found in {log_identifier}: no spawn entries container reference.'
        )
        return None
    if not proxy.NPCSpawnEntriesContainerObject[0].value.value:
        logger.warning(
            f'Broken NPC zone manager found in {log_identifier}: spawn entries container reference points to nothing.'
        )
        return None
    if not getattr(proxy, 'LinkedZoneVolumes', None):
        logger.warning(
            f'Broken NPC zone manager found in {log_identifier}: no zone volumes linked.'
        )
        return None

    data = export_properties_from_proxy(proxy, ZONE_MANAGER_EXPORTED_PROPERTIES)
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
        logger.warning(
            f'Broken NPC zone manager found in {log_identifier}: no spawn zone entries nor spawn points linked.'
        )
        return None

    return data

        
def gather_zone_volumes_bounds(volumes: ArrayProperty, log_identifier: str = 'a map'):
    for zone_volume in volumes.values:
        zone_volume = zone_volume.value.value
        if not zone_volume:
            logger.warning(
                f'Broken NPC zone manager found in {log_identifier}: zone volume reference does not point anywhere.'
            )
            continue
            
        yield get_volume_worldspace_bounds(zone_volume)


def gather_zone_spawn_points(points: ArrayProperty, log_identifier: str = 'a map'):
    for marker in points.values:
        marker = marker.value.value
        if not marker:
            logger.warning(
                f'Broken NPC zone manager found in {log_identifier}: spawn marker reference does not point anywhere.'
            )
            continue

        scene_component = marker.properties.get_property("RootComponent").value.value
        marker_location = scene_component.properties.get_property("RelativeLocation").values[0]
        yield marker_location.x.value, marker_location.y.value


def gather_zone_spawn_volumes_bounds(entries: ArrayProperty, log_identifier: str = 'a map'):
    for entry in entries.values:
        entry_data = entry.as_dict()
        entry_weight = entry_data['EntryWeight'].value
        spawn_volume = entry_data["LinkedZoneSpawnVolume"].value.value
        if not spawn_volume:
            logger.warning(
                f'Broken NPC zone manager found in {log_identifier}: spawn zone volume reference does not point anywhere.'
            )
            continue

        yield entry_weight, get_volume_worldspace_bounds(spawn_volume)
