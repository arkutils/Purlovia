from dataclasses import dataclass, field
from logging import NullHandler, getLogger
from typing import *

from ue.asset import UAsset
from ue.base import UEBase

from .map import WorldData
from .types import CustomActorList
from .utils import format_location_for_export, get_actor_worldspace_location

logger = getLogger(__name__)
logger.addHandler(NullHandler())


def export_nest_locations(world: WorldData, proxy: CustomActorList, _log_identifier: str = 'a map'):
    for nest_marker in proxy.ActorList[0].values:
        yield format_location_for_export(get_actor_worldspace_location(nest_marker.value.value), world.latitude, world.longitude)
