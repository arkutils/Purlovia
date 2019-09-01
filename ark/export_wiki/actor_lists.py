from .map import WorldData
from .types import CustomActorList
from .utils import format_location_for_export, get_actor_worldspace_location


def extract_actor_list(world: WorldData, proxy: CustomActorList):
    for actor in proxy.ActorList[0].values:
        if not actor.value.value:
            continue
        location = get_actor_worldspace_location(actor.value.value)
        yield format_location_for_export(location, world.latitude, world.longitude)
