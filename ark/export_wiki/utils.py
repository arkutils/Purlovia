from ue.proxy import UEProxyStructure

from .geo import GeoData


def unpack_defaultdict_value(obj):
    return obj[0] if obj else None

def proxy_properties_as_dict(proxy: UEProxyStructure, key_list, only_overriden=False):
    data = {}
    for key in key_list:
        if only_overriden and not proxy.has_override(key):
            continue

        data[key_list[key]] = unpack_defaultdict_value(getattr(proxy, key, None))
    return data

def format_location_for_export(ue_coords: tuple, lat: GeoData, long: GeoData):
    if len(ue_coords) == 2:
        # XY pair
        return {"lat": lat.from_units(ue_coords[1]), "long": long.from_units(ue_coords[0])}

    if len(ue_coords) == 3:
        # Resources (XYZ) and veins
        return {
            "x": ue_coords[0],
            "y": ue_coords[1],
            "z": ue_coords[2],
            "lat": lat.from_units(ue_coords[1]),
            "long": long.from_units(ue_coords[0])
        }

    # 2D bounds (min[XY]max[XY])
    long_start = long.from_units(ue_coords[0])
    lat_start = lat.from_units(ue_coords[1])
    long_end = long.from_units(ue_coords[2])
    lat_end = lat.from_units(ue_coords[3])
    return {
        "latStart": lat_start,
        "longStart": long_start,
        "latEnd": lat_end,
        "longEnd": long_end,
        "latCenter": (lat_end+lat_start) / 2,
        "longCenter": (long_end+long_start) / 2,
    }

def get_actor_worldspace_location(actor):
    '''Retrieves actor's world-space location in a form of (x,y,z) tuple.'''

    if isinstance(actor, UEProxyStructure):
        scene_component = actor.RootComponent[0].value.value
    else:
        scene_component = actor.properties.get_property("RootComponent").value.value
    actor_location = scene_component.properties.get_property("RelativeLocation").values[0]

    return (
        actor_location.x.value,
        actor_location.y.value,
        actor_location.z.value
    )


def get_volume_worldspace_bounds(volume, include_altitude=False):
    '''Retrieves volume's world-space bounds in a form of (min_x,max_y,max_x,max_y) tuple.'''

    if isinstance(volume, UEProxyStructure):
        brush_component = volume.BrushComponent[0].value.value
    else:
        brush_component = volume.properties.get_property("BrushComponent").value.value

    body_setup = brush_component.properties.get_property("BrushBodySetup").value.value
    agg_geom = body_setup.properties.get_property("AggGeom").values[0].value
    convex_elems = agg_geom.values[0]
    volume_location = brush_component.properties.get_property("RelativeLocation").values[0]
    volume_box = convex_elems.as_dict()["ElemBox"].values[0]

    if include_altitude:
        # min[XYZ]max[XYZ] format
        return (
            # Min
            volume_box.min.x.value + volume_location.x.value,
            volume_box.min.y.value + volume_location.y.value,
            volume_box.min.z.value + volume_location.z.value,
            # Max
            volume_box.max.x.value + volume_location.x.value,
            volume_box.max.y.value + volume_location.y.value,
            volume_box.max.z.value + volume_location.z.value
        )

    # min[XY]max[XY] format
    return (
        # Min
        volume_box.min.x.value + volume_location.x.value,
        volume_box.min.y.value + volume_location.y.value,
        # Max
        volume_box.max.x.value + volume_location.x.value,
        volume_box.max.y.value + volume_location.y.value
    )
