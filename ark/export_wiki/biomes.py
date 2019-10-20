from ue.properties import ArrayProperty

from .common import (format_location_for_export, get_volume_worldspace_bounds,
                     proxy_properties_as_dict)
from .map import WorldData
from .types import (BIOME_VOLUME_ALWAYS_EXPORTED_PROPERTIES,
                    BIOME_VOLUME_EXPORTED_PROPERTIES, BiomeZoneVolume)


def extract_biome_zone_volume(world: WorldData, proxy: BiomeZoneVolume) -> dict:
    bounds = get_volume_worldspace_bounds(proxy, include_altitude=True)
    return {
        **proxy_properties_as_dict(proxy, key_list=BIOME_VOLUME_ALWAYS_EXPORTED_PROPERTIES, only_overriden=False),
        **proxy_properties_as_dict(proxy, key_list=BIOME_VOLUME_EXPORTED_PROPERTIES, only_overriden=True),
        'boxes': {
            'min': format_location_for_export(bounds[:3], world.latitude, world.longitude),
            'max': format_location_for_export(bounds[3:], world.latitude, world.longitude)
        }
    }
