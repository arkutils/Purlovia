from logging import NullHandler, getLogger
from typing import *

from ue.base import UEBase
from ue.properties import ArrayProperty

from .map import WorldData
from .types import (BIOME_VOLUME_ALWAYS_EXPORTED_PROPERTIES,
                    BIOME_VOLUME_EXPORTED_PROPERTIES, BiomeZoneVolume)
from .utils import (export_properties_from_proxy, format_location_for_export,
                    get_volume_worldspace_bounds)

logger = getLogger(__name__)
logger.addHandler(NullHandler())


def export_biome_zone_volume(world: WorldData, proxy: BiomeZoneVolume, _log_identifier: str = 'a map') -> Optional[dict]:
    data = dict(export_properties_from_proxy(proxy, BIOME_VOLUME_ALWAYS_EXPORTED_PROPERTIES, False))
    data.update(export_properties_from_proxy(proxy, BIOME_VOLUME_EXPORTED_PROPERTIES, True))

    bounds = get_volume_worldspace_bounds(proxy, True)
    data['boxes'] = {
        'min': format_location_for_export(bounds[:3], world.latitude, world.longitude),
        'max': format_location_for_export(bounds[3:], world.latitude, world.longitude)
    }

    return data
