from dataclasses import dataclass, field
from logging import NullHandler, getLogger
from typing import *

from ark.export_wiki.geo import qowyn_format_location
from ue.asset import UAsset
from ue.base import UEBase

logger = getLogger(__name__)
logger.addHandler(NullHandler())


def gather_nest_locations(level: UAsset):
    # Temporary; will move this check out once any other gatherer
    # can be set up.
    for export in level.exports:
        if str(export.klass.value.name) != 'CustomActorList':
            continue
        actor_list_export = export

        list_properties = actor_list_export.properties.as_dict()
        markers = list_properties['ActorList'][0]

        for nest_marker in markers.values:
            marker_properties = nest_marker.value.value.properties.as_dict()
            scene_component = marker_properties['RootComponent'][0].value.value
            marker_location = scene_component.properties.get_property("RelativeLocation").values[0]
            yield (marker_location.x.value, marker_location.y.value, marker_location.z.value)
