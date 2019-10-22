from typing import Optional

from ue.properties import ArrayProperty

from .common import format_location_for_export, get_actor_worldspace_location, proxy_properties_as_dict
from .map import WorldData
from .types import SUPPLY_DROP_ALWAYS_EXPORTED_PROPERTIES, SUPPLY_DROP_EXPORTED_PROPERTIES, SupplyCrateSpawningVolume


def extract_supply_crate_volume(world: WorldData, proxy: SupplyCrateSpawningVolume) -> Optional[dict]:
    if not getattr(proxy, 'LinkedSupplyCrateEntries', None) or not getattr(proxy, 'LinkedSpawnPointEntries', None):
        return None

    return {
        **proxy_properties_as_dict(proxy, key_list=SUPPLY_DROP_ALWAYS_EXPORTED_PROPERTIES),
        **proxy_properties_as_dict(proxy, key_list=SUPPLY_DROP_EXPORTED_PROPERTIES, only_overriden=True),
        # Crate classes
        'crateClasses':
        [entry.as_dict()['CrateTemplate'].format_for_json() for entry in proxy.LinkedSupplyCrateEntries[0].values],
        # Crate locations
        'crateLocations': [
            format_location_for_export(point, world.latitude, world.longitude)
            for point in gather_spawn_points(proxy.LinkedSpawnPointEntries[0])
        ]
    }


def gather_spawn_points(point_entries: ArrayProperty):
    for point_entry in point_entries.values:
        marker = point_entry.as_dict()['LinkedSpawnPoint'].value.value
        if not marker:
            continue
        yield get_actor_worldspace_location(marker)
