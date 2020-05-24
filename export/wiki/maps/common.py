import re
from collections import namedtuple
from typing import Any, Dict, Tuple

from export.wiki.consts import CHARGE_NODE_CLS, EXPLORER_CHEST_BASE_CLS, \
    GAS_VEIN_CLS, OIL_VEIN_CLS, WATER_VEIN_CLS, WILD_PLANT_SPECIES_Z_CLS
from ue.asset import ExportTableItem
from ue.properties import Vector
from ue.proxy import UEProxyStructure

from .data_container import MapInfo
from .models import Box, Location

__all__ = [
    'convert_box_bounds_for_export',
    'get_actor_location_vector',
    'get_volume_bounds',
    'get_volume_box_count',
    'get_volume_brush_setup',
]

BIOME_REMOVE_WIND_INFO = re.compile(r', \d*% W(ind|)')


def get_actor_location_vector(actor) -> Vector:
    '''Retrieves actor's world-space location vector.'''

    if isinstance(actor, UEProxyStructure):
        scene_component = actor['RootComponent'][0].value.value
    else:
        scene_component = actor.properties.get_property("RootComponent").value.value
    actor_location = scene_component.properties.get_property("RelativeLocation").values[0]

    return actor_location


def get_actor_location_vector_m(actor) -> Location:
    vector = get_actor_location_vector(actor)
    return Location(x=vector.x, y=vector.y, z=vector.z)


def get_volume_brush_setup(volume) -> Tuple[ExportTableItem, ExportTableItem]:
    '''Retrieves the BrushComponent and BodySetup exports from a volume.'''

    if isinstance(volume, UEProxyStructure):
        brush = volume['BrushComponent'][0].value.value
    else:
        brush = volume.properties.get_property('BrushComponent').value.value

    return (brush, brush.properties.get_property('BrushBodySetup').value.value)


def get_volume_box_count(volume) -> int:
    '''Retrieves number of boxes in a single volume.'''

    _, body = get_volume_brush_setup(volume)
    geometry = body.properties.get_property('AggGeom')
    convex_elements = geometry.values[0].value
    return len(convex_elements.values)


def get_volume_bounds(volume, convex_index=0) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, float]]:
    '''Retrieves volume's world-space bounds as tuple of two vectors: min and max.'''

    brush, body = get_volume_brush_setup(volume)
    volume_location = brush.properties.get_property('RelativeLocation').values[0]

    geometry = body.properties.get_property('AggGeom')
    convex_elements = geometry.values[0].value
    box = convex_elements.values[convex_index].as_dict()['ElemBox'].values[0]

    start = dict(
        x=box.min.x + volume_location.x,
        y=box.min.y + volume_location.y,
        z=box.min.z + volume_location.z,
    )
    end = dict(
        x=box.max.x + volume_location.x,
        y=box.max.y + volume_location.y,
        z=box.max.z + volume_location.z,
    )

    center = dict(
        x=(start['x'] + end['x']) / 2,
        y=(start['y'] + end['y']) / 2,
        z=(start['z'] + end['z']) / 2,
    )
    return (start, center, end)


def get_volume_bounds_m(volume, convex_index=0) -> Box:
    start, center, end = get_volume_bounds(volume, convex_index)
    return Box(start=start, center=center, end=end)


def convert_location_for_export(map_info: MapInfo, data: Dict[str, Any]):
    data['lat'] = map_info.lat.from_units(data['y'])
    data['long'] = map_info.long.from_units(data['x'])


def convert_box_bounds_for_export(map_info: MapInfo, box_data: Dict[str, Any]):
    # Start
    box_data['start']['lat'] = map_info.lat.from_units(box_data['start']['y'])
    box_data['start']['long'] = map_info.long.from_units(box_data['start']['x'])
    # Center
    box_data['center']['lat'] = map_info.lat.from_units(box_data['center']['y'])
    box_data['center']['long'] = map_info.long.from_units(box_data['center']['x'])
    # End
    box_data['end']['lat'] = map_info.lat.from_units(box_data['end']['y'])
    box_data['end']['long'] = map_info.long.from_units(box_data['end']['x'])


def any_overriden(proxy: UEProxyStructure, props: Tuple[str, ...]) -> bool:
    return any(proxy.has_override(x) for x in props)
