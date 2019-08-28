from logging import NullHandler, getLogger
from typing import *

from ue.base import UEBase
from ue.properties import ArrayProperty

from .map import WorldData
from .types import (SUPPLY_DROP_ALWAYS_EXPORTED_PROPERTIES,
                    SUPPLY_DROP_EXPORTED_PROPERTIES, SupplyCrateSpawningVolume)
from .utils import (export_properties_from_proxy, format_location_for_export,
                    get_actor_worldspace_location)

logger = getLogger(__name__)
logger.addHandler(NullHandler())


def export_supply_crate_volume(world: WorldData, proxy: SupplyCrateSpawningVolume, log_identifier: str = 'a map') -> Optional[dict]:
    #if not proxy.MaxNumCrates[0].value:
    #    logger.debug(f'Perhaps a supply crate volume in {log_identifier} should be skipped: MaxNumCrates == 0.')
    if not getattr(proxy, 'LinkedSupplyCrateEntries', None):
        #logger.debug(f'Broken supply crate volume found in {log_identifier}: no linked crate entries.')
        return None
    if not getattr(proxy, 'LinkedSpawnPointEntries', None):
        #logger.debug(f'Broken supply crate volume found in {log_identifier}: no linked spawn points.')
        return None

    data = dict(export_properties_from_proxy(proxy, SUPPLY_DROP_ALWAYS_EXPORTED_PROPERTIES))
    data.update(export_properties_from_proxy(proxy, SUPPLY_DROP_EXPORTED_PROPERTIES, True))

    # Crate classes
    data['crateClasses'] = [ entry.as_dict()['CrateTemplate'] for entry in proxy.LinkedSupplyCrateEntries[0].values ]

    # Crate locations
    data['crateLocations'] = [
        format_location_for_export(point, world.latitude, world.longitude)
        for point in gather_crate_spawn_points(proxy.LinkedSpawnPointEntries[0], log_identifier)
    ]

    return data

def gather_crate_spawn_points(point_entries: ArrayProperty, log_identifier: str = 'a map'):
    for point_entry in point_entries.values:
        marker = point_entry.as_dict()['LinkedSpawnPoint'].value.value
        if not marker:
            #logger.debug(f'Broken supply crate volume found in {log_identifier}: spawn point marker reference does not point anywhere.')
            continue

        yield get_actor_worldspace_location(marker)
