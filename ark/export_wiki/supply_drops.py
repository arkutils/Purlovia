from logging import NullHandler, getLogger
from typing import *

from ark.export_wiki.map import WorldData
from ark.export_wiki.types import (SUPPLY_DROP_ALWAYS_EXPORTED_PROPERTIES,
                                   SUPPLY_DROP_EXPORTED_PROPERTIES,
                                   SupplyCrateSpawningVolume)
from ark.export_wiki.utils import (export_properties_from_proxy,
                                   format_location_for_export,
                                   get_volume_worldspace_bounds,
                                   struct_entries_array_to_dict)
from ue.base import UEBase
from ue.properties import ArrayProperty

logger = getLogger(__name__)
logger.addHandler(NullHandler())


def export_supply_crate_volume(world: WorldData, proxy: SupplyCrateSpawningVolume, log_identifier: str = 'a map') -> Optional[dict]:
    if not proxy.MaxNumCrates[0].value:
        logger.warning(
            f'TODO:Perhaps a supply crate volume in {log_identifier} should be skipped: MaxNumCrates == 0.'
        )
    if not getattr(proxy, 'LinkedSupplyCrateEntries', None):
        logger.warning(f'Broken supply crate volume found in {log_identifier}: no linked crate entries.')
        return None
    if not getattr(proxy, 'LinkedSpawnPointEntries', None):
        logger.warning(f'Broken supply crate volume found in {log_identifier}: no linked spawn points.')
        return None

    data = dict(export_properties_from_proxy(proxy, SUPPLY_DROP_ALWAYS_EXPORTED_PROPERTIES))
    data.update(export_properties_from_proxy(proxy, SUPPLY_DROP_EXPORTED_PROPERTIES, True))

    # Crate classes
    data['crateClasses'] = [
        struct_entries_array_to_dict(entry.values)['CrateTemplate']
        for entry in proxy.LinkedSupplyCrateEntries[0].values
    ]

    # Crate locations
    data['crateLocations'] = [
        format_location_for_export(point, world.latitude, world.longitude)
        for point in gather_crate_spawn_points(proxy.LinkedSpawnPointEntries[0], log_identifier)
    ]

    return data

def gather_crate_spawn_points(point_entries: ArrayProperty, log_identifier: str = 'a map'):
    for point_entry in point_entries.values:
        entry_data = struct_entries_array_to_dict(point_entry.values)
        marker = entry_data['LinkedSpawnPoint'].value.value
        if not marker:
            logger.warning(
                f'Broken supply crate volume found in {log_identifier}: spawn point marker reference does not point anywhere.'
            )
            continue

        scene_component = marker.properties.get_property("RootComponent").value.value
        marker_location = scene_component.properties.get_property("RelativeLocation").values[0]
        yield marker_location.x.value, marker_location.y.value
