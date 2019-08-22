from logging import NullHandler, getLogger
from typing import *

from ark.export_wiki.map import WorldData
from ark.export_wiki.types import (BIOME_VOLUME_ALWAYS_EXPORTED_PROPERTIES,
                                   BIOME_VOLUME_EXPORTED_PROPERTIES,
                                   BiomeZoneVolume)
from ark.export_wiki.utils import (export_properties_from_proxy,
                                   format_location_for_export,
                                   get_volume_worldspace_bounds)
from ue.base import UEBase
from ue.properties import ArrayProperty

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
