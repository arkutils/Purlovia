from ue.proxy import UEProxyStructure

from .consts import CHARGE_NODE_CLS, EXPLORER_CHEST_BASE_CLS, \
    GAS_VEIN_CLS, OIL_VEIN_CLS, WATER_VEIN_CLS, WILD_PLANT_SPECIES_Z_CLS
from .map import MapInfo

ACTOR_LIST_TAG_FIELD_MAP = {
    'DragonNestSpawns': 'wyvernNests',
    'IceNestSpawns': 'iceWyvernNests',
    'DrakeNestSpawns': 'drakeNests',
    'DeinonychusNestSpawns': 'deinonychusNests',
    'AB_DeinonychusNestSpawns': 'deinonychusNests'
}


def unpack_defaultdict_value(obj):
    return obj[0] if obj else None


def proxy_properties_as_dict(proxy: UEProxyStructure, key_list, only_overriden=False):
    data = {}
    for key in key_list:
        if only_overriden and not proxy.has_override(key):
            continue

        value = unpack_defaultdict_value(getattr(proxy, key, None))
        if hasattr(value, 'format_for_json'):
            value = value.format_for_json()
        data[key_list[key]] = value
    return data


#def format_location_for_export(ue_coords: tuple, lat: GeoData, long: GeoData):
#    if len(ue_coords) == 2:
#        # XY pair
#        return {"lat": lat.from_units(ue_coords[1]), "long": long.from_units(ue_coords[0])}
#
#    if len(ue_coords) == 3:
#        # Resources (XYZ) and veins
#        return {
#            "x": ue_coords[0],
#            "y": ue_coords[1],
#            "z": ue_coords[2],
#            "lat": lat.from_units(ue_coords[1]),
#            "long": long.from_units(ue_coords[0])
#        }
#
#    # 2D bounds (min[XY]max[XY])
#    long_start = long.from_units(ue_coords[0])
#    lat_start = lat.from_units(ue_coords[1])
#    long_end = long.from_units(ue_coords[2])
#    lat_end = lat.from_units(ue_coords[3])
#    return {
#        "latStart": lat_start,
#        "longStart": long_start,
#        "latEnd": lat_end,
#        "longEnd": long_end,
#        "latCenter": (lat_end+lat_start) / 2,
#        "longCenter": (long_end+long_start) / 2,
#    }


def get_actor_location_vector(actor):
    '''Retrieves actor's world-space location vector.'''

    if isinstance(actor, UEProxyStructure):
        scene_component = actor.RootComponent[0].value.value
    else:
        scene_component = actor.properties.get_property("RootComponent").value.value
    actor_location = scene_component.properties.get_property("RelativeLocation").values[0]

    return actor_location

def get_volume_bounds(volume):
    '''Retrieves volume's world-space bounds as tuple of two vectors: min and max.'''

    if isinstance(volume, UEProxyStructure):
        brush_component = volume.BrushComponent[0].value.value
    else:
        brush_component = volume.properties.get_property("BrushComponent").value.value

    body_setup = brush_component.properties.get_property("BrushBodySetup").value.value
    agg_geom = body_setup.properties.get_property("AggGeom").values[0].value
    convex_elems = agg_geom.values[0]
    volume_location = brush_component.properties.get_property("RelativeLocation").values[0]
    volume_box = convex_elems.as_dict()["ElemBox"].values[0]
    return (
        dict(
            x=volume_box.min.x + volume_location.x,
            y=volume_box.min.y + volume_location.y,
            z=volume_box.min.z + volume_location.z
        ),
        dict(
            x=volume_box.max.x + volume_location.x,
            y=volume_box.max.y + volume_location.y,
            z=volume_box.max.z + volume_location.z
        )
    )

def convert_box_bounds_for_export(map_info: MapInfo, box_data: dict):
    # Start
    box_data['start']['lat'] = map_info.lat.from_units(box_data['start']['y'])
    box_data['start']['long'] = map_info.long.from_units(box_data['start']['x'])
    # Center
    box_data['center'] = dict(
        x=(box_data['start']['x'] + box_data['end']['x']) / 2,
        y=(box_data['start']['y'] + box_data['end']['y']) / 2,
        z=(box_data['start']['z'] + box_data['end']['z']) / 2
    )
    box_data['center']['lat'] = map_info.lat.from_units(box_data['center']['y'])
    box_data['center']['long'] = map_info.lat.from_units(box_data['center']['x'])
    # End
    box_data['end']['lat'] = map_info.lat.from_units(box_data['end']['y'])
    box_data['end']['long'] = map_info.long.from_units(box_data['end']['x'])
