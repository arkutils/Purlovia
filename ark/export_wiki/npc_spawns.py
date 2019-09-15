from typing import *

from ue.properties import ArrayProperty

from .common import (format_location_for_export, get_actor_worldspace_location,
                     get_volume_worldspace_bounds, proxy_properties_as_dict)
from .map import WorldData
from .types import (ZONE_MANAGER_EXPORTED_PROPERTIES, NPCZoneManager,
                    PrimalWorldSettings)


def extract_npc_zone_manager(world: WorldData, proxy: NPCZoneManager) -> Optional[dict]:
    if (not getattr(proxy, 'NPCSpawnEntriesContainerObject', None) or not proxy.NPCSpawnEntriesContainerObject[0].value.value
        or not getattr(proxy, 'LinkedZoneVolumes', None)):
        return None

    data = {
        **proxy_properties_as_dict(proxy, key_list=ZONE_MANAGER_EXPORTED_PROPERTIES),
        # Export dino counting volumes
        'locations': [
            format_location_for_export(bounds, world.latitude, world.longitude) for bounds in gather_counting_volumes(proxy.LinkedZoneVolumes[0])
        ]
    }
    if not data['locations']:
        return None

    # Export spawn points or locations
    if getattr(proxy, 'SpawnPointOverrides', None):
        data['spawnPoints'] = [
            format_location_for_export(point, world.latitude, world.longitude) for point in gather_spawn_points(proxy.SpawnPointOverrides[0])
        ]
    elif getattr(proxy, 'LinkedZoneSpawnVolumeEntries', None):
        data['spawnLocations'] = [
            {
                'weight': weight.format_for_json(),
                **format_location_for_export(bounds, world.latitude, world.longitude)
            } for weight, bounds in gather_spawn_volumes(proxy.LinkedZoneSpawnVolumeEntries[0])
        ]
    else:
        return None

    return data


def gather_counting_volumes(volumes: ArrayProperty):
    for zone_volume in volumes.values:
        zone_volume = zone_volume.value.value

        if not zone_volume:
            continue
        yield get_volume_worldspace_bounds(zone_volume)


def gather_spawn_points(points: ArrayProperty):
    for marker in points.values:
        marker = marker.value.value

        if not marker:
            continue
        yield get_actor_worldspace_location(marker)[:2]


def gather_spawn_volumes(entries: ArrayProperty):
    for entry in entries.values:
        entry_data = entry.as_dict()
        entry_weight = entry_data['EntryWeight']
        spawn_volume = entry_data["LinkedZoneSpawnVolume"].value.value

        if not spawn_volume:
            continue
        yield entry_weight, get_volume_worldspace_bounds(spawn_volume)
