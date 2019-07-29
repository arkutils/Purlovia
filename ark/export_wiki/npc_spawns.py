from dataclasses import dataclass, field
from logging import NullHandler, getLogger
from typing import *

from ark.export_wiki.geo import qowyn_format_location
from ue.asset import UAsset
from ue.base import UEBase

logger = getLogger(__name__)
logger.addHandler(NullHandler())


@dataclass
class NPCSpawn:
    spawn_group: str = '<yet to be extracted>'
    locations: list = field(default_factory=lambda: [])
    spawn_locations: list = field(default_factory=lambda: [])
    spawn_points: list = field(default_factory=lambda: [])
    min_desired_npc_number: int = 0
    never_spawn_in_water: bool = False
    force_untameable: bool = False

    def as_dict(self, lat, long):
        self_as_dict = {
            "spawnGroups": self.spawn_group,
            "minDesiredNumberOfNPC": self.min_desired_npc_number,
            "bNeverSpawnInWater": self.never_spawn_in_water,
            "bForceUntameable": self.force_untameable,
            "locations": [qowyn_format_location(bounds, lat, long) for bounds in self.locations],
        }

        if self.spawn_points:
            self_as_dict["spawnPoints"] = [qowyn_format_location(location, lat, long) for location in self.spawn_points]
        else:
            self_as_dict["spawnLocations"] = [qowyn_format_location(bounds, lat, long) for bounds in self.spawn_locations]

        return self_as_dict


def _get_volume_worldspace_xy(volume):
    brush_component = volume.properties.get_property("BrushComponent").value.value
    body_setup = brush_component.properties.get_property("BrushBodySetup").value.value
    agg_geom = body_setup.properties.get_property("AggGeom").values[0].value
    convex_elems = agg_geom.values[0]
    volume_location = brush_component.properties.get_property("RelativeLocation").values[0]
    volume_box = convex_elems.as_dict()["ElemBox"].values[0]
    return (
        # Min
        volume_box.min.x.value + volume_location.x.value,
        volume_box.min.y.value + volume_location.y.value,
        # Max
        volume_box.max.x.value + volume_location.x.value,
        volume_box.max.y.value + volume_location.y.value)


def gather_npc_spawn_data(level: UAsset):
    # Temporary; will move this check out once any other gatherer
    # can be set up.
    for export in level.exports:
        if not str(export.klass.value.name).startswith('NPCZoneManager'):
            continue
        manager = export
        manager_properties = manager.properties.as_dict()
        is_enabled = manager_properties['bEnabled']
        if is_enabled and not is_enabled[0].value:
            continue

        collected_data = NPCSpawn()
        entry_container = manager_properties['NPCSpawnEntriesContainerObject'][0].value.value.namespace.value
        collected_data.spawn_group = str(entry_container.name)

        linked_zone_volumes = manager_properties['LinkedZoneVolumes'][0].values
        spawn_point_overrides = manager_properties['SpawnPointOverrides'][0]
        linked_spawn_volumes = manager_properties['LinkedZoneSpawnVolumeEntries'][0]
        if manager_properties['MinDesiredNumberOfNPC']:
            collected_data.min_desired_npc_number = manager_properties['MinDesiredNumberOfNPC'][0].value
        if manager_properties['bNeverSpawnInWater']:
            collected_data.never_spawn_in_water = manager_properties['bNeverSpawnInWater'][0].value
        if manager_properties['bForceUntameable']:
            collected_data.force_untameable = manager_properties['bForceUntameable'][0].value

        if linked_zone_volumes is None:
            logger.warning(f'Zone manager for {collected_data.spawn_group} does not have any zone volumes linked.')
            continue

        if linked_spawn_volumes is None and spawn_point_overrides is None:
            logger.warning(f'Zone manager for {collected_data.spawn_group} does not have any spawn zone volumes linked.')
            continue

        # Locations
        for zone_volume in linked_zone_volumes:
            zone_volume = zone_volume.value.value
            if zone_volume is not None:
                collected_data.locations.append(_get_volume_worldspace_xy(zone_volume))
                break
        else:
            logger.warning(f'A zone manager for {collected_data.spawn_group} is not linked to any volume.')
            continue

        # Determine whether we should export the spawn locations
        # or the spawn points. The latter is always used over the
        # spawn zones if present.
        if spawn_point_overrides is None:
            # Spawn Locations
            for spawn_zone_entry in linked_spawn_volumes.values:
                spawn_zone_properties = spawn_zone_entry.as_dict()
                spawn_volume = spawn_zone_properties["LinkedZoneSpawnVolume"].value.value
                if spawn_volume is None:
                    logger.warning(
                        f'A zone manager for {collected_data.spawn_group} has an entry but is not linked to a volume.')
                    continue

                collected_data.spawn_locations.append(_get_volume_worldspace_xy(spawn_volume))
        else:
            for spawn_point_marker in spawn_point_overrides.values:
                spawn_point_marker = spawn_point_marker.value.value
                if not spawn_point_marker:
                    logger.warning(f'A zone manager for {collected_data.spawn_group} uses a spawn point that is missing.')
                    continue

                scene_component = spawn_point_marker.properties.get_property("RootComponent").value.value
                marker_location = scene_component.properties.get_property("RelativeLocation").values[0]
                collected_data.spawn_points.append((marker_location.x.value, marker_location.y.value))

        if collected_data.spawn_locations and collected_data.spawn_points:
            continue
        yield collected_data
