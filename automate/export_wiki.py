import hashlib
import json
import re
from datetime import datetime
from logging import NullHandler, getLogger
from operator import attrgetter
from pathlib import Path
from typing import *

import ark.properties
from ark.common import PGD_PKG
from ark.export_wiki.biomes import export_biome_zone_volume
from ark.export_wiki.geo import GeoData, gather_geo_data
from ark.export_wiki.map import MapData, get_settings_from_map
from ark.export_wiki.npc_spawns import export_npc_zone_manager
from ark.export_wiki.spawncontainers import get_spawn_entry_container_data
from ark.export_wiki.sublevels import gather_sublevel_names
from ark.export_wiki.supply_drops import export_supply_crate_volume
from ark.export_wiki.types import (BiomeZoneVolume, NPCZoneManager, SupplyCrateSpawningVolume)
from ark.export_wiki.utils import property_serializer
from ark.worldcomposition import SublevelDiscoverer
from automate.ark import ArkSteamManager
from automate.version import createExportVersion
from config import ConfigFile, get_global_config
from ue.asset import UAsset
from ue.base import UEBase
from ue.gathering import gather_properties
from ue.loader import AssetNotFound

logger = getLogger(__name__)
logger.addHandler(NullHandler())

__all__ = [
    'export_map_data',
]

KNOWN_KLASS_NAMES = [
    # NPC spawns
    'NPCZoneManager',
    'NPCZoneManagerBlueprint_Cave_C',
    'NPCZoneManagerBlueprint_Land_C',
    'NPCZoneManagerBlueprint_Water_C',
    # Biomes
    'BiomeZoneVolume',
    # Supply Drops
    'SupplyCrateSpawningVolume',
]


def export_map_data(arkman: ArkSteamManager, modids: Set[str], config: ConfigFile):
    logger.info('Wiki export beginning')
    if config.wiki_settings.SkipExtract:
        logger.info('(skipped)')
        return

    # Ensure the output directory exists
    outdir = config.wiki_settings.PublishDir
    outdir.mkdir(parents=True, exist_ok=True)

    # Export based on current config
    exporter = Exporter(arkman, modids, config)
    exporter.perform()

    logger.info('Export complete')


class Exporter:
    def __init__(self, arkman: ArkSteamManager, modids: Set[str], config: ConfigFile):
        self.config = config
        self.arkman = arkman
        self.modids = modids
        self.loader = arkman.createLoader()
        self.wc_discoverer = SublevelDiscoverer(self.loader)
        self.game_version = self.arkman.getGameVersion()

    def perform(self):
        self._prepare_versions()

        logger.info('Beginning export of maps')
        game_buildid = self.arkman.getGameBuildId()
        version = self._create_version(game_buildid)
        self._export_levels(self.config.maps, version=version)

    def _prepare_versions(self):
        if not self.game_version:
            raise ValueError("Game not installed or ArkSteamManager not yet initialised")

    def _create_version(self, timestamp: str) -> str:
        return createExportVersion(self.game_version, timestamp)  # type: ignore

    def _export_levels(self, persistent_levels: List, version: str, other: Dict = None, moddata: Optional[Dict] = None):
        for assetname in persistent_levels:
            logger.info(f'Collecting data from the top-level {assetname}')
            asset = self.loader[assetname]
            map_data = get_settings_from_map(asset)

            self._gather_data_from_level(asset, map_data)
            del self.loader[assetname]
            logger.info('Persistent level extracted and unloaded. Sublevels will now be loaded.')

            for sublevel in self.wc_discoverer.discover_submaps(asset):
                subasset = self.loader[sublevel]
                self._gather_data_from_level(subasset, map_data)
                del self.loader[sublevel]

            self._gather_spawn_groups(map_data)
            self._export_values(map_data.name, map_data.as_dict(), version)
            del map_data

    def _gather_data_from_level(self, level: UAsset, map_data: MapData):
        for export in level.exports:
            if str(export.klass.value.name) not in KNOWN_KLASS_NAMES:
                continue
            proxy = gather_properties(export)  # type:ignore

            if isinstance(proxy, NPCZoneManager):
                if not self.config.wiki_settings.ExportSpawnData or not proxy.bEnabled[0].value:
                    continue

                data = export_npc_zone_manager(map_data, proxy, log_identifier=f'{level.assetname} (export "{export.name}")')
                if data:
                    map_data.spawns.append(data)

                    spawn_group = data['spawnGroup'].format_for_json()
                    if spawn_group not in map_data.spawn_groups:
                        map_data.spawn_groups.append(spawn_group)
            elif isinstance(proxy, BiomeZoneVolume):
                if not self.config.wiki_settings.ExportBiomeData or proxy.bHidden[0].value:
                    continue

                data = export_biome_zone_volume(map_data,
                                                export,
                                                proxy,
                                                log_identifier=f'{level.assetname} (export "{export.name}")')
                if data:
                    map_data.biomes.append(data)
            elif isinstance(proxy, SupplyCrateSpawningVolume):
                if not self.config.wiki_settings.ExportSupplyCrateData or proxy.bHidden[0].value:
                    continue

                data = export_supply_crate_volume(map_data, proxy, log_identifier=f'{level.assetname} (export "{export.name}")')
                if data:
                    map_data.loot_crates.append(data)
            else:
                logger.error(f'{proxy.get_ue_type()} is not going to be exported (unknown destination).')

            del proxy

    def _gather_spawn_groups(self, world: MapData):
        for index in range(len(world.spawn_groups)):
            group_data = get_spawn_entry_container_data(self.loader, world.spawn_groups[index])
            if group_data:
                world.spawn_groups[index] = group_data.as_dict()

    def _export_values(self, level_name: str, values: dict, version: str):
        level_name = level_name.rstrip('_C')
        level_name = level_name.rstrip('_P')

        versioned_values = {"map": level_name, "version": version}
        versioned_values.update(values)
        fullpath = (self.config.wiki_settings.PublishDir / level_name).with_suffix('.json')
        self._save_json_if_changed(versioned_values, fullpath)

    def _save_json_if_changed(self, values: Dict[str, Any], fullpath: Path):
        changed, version = _should_save_json(values, fullpath)
        if changed:
            pretty = self.config.settings.PrettyJson
            logger.info(f'Saving export to {fullpath} with version {version}')
            values['version'] = version
            _save_as_json(values, fullpath, pretty=pretty)
        else:
            logger.info(f'No changes to {fullpath}')


def _should_save_json(values: Dict[str, Any], fullpath: Path) -> Tuple[bool, str]:
    '''
    Works out if a file needs to be saved and with which version number.

    This is calcualted using the digest of its content, excluding the version field.
    Also handles cases where the content has changed but the version has not, by bumping the build number.

    Returns a tuple of (changed, version), where `changed` is a boolean saying whether the data needs to be
    saved and `version` is the version number to use.
    '''
    new_version: str = values.get('version', None)
    if not new_version:
        raise ValueError('Export data must contain a version field')

    # Load the existing file
    try:
        with open(fullpath) as f:
            existing_data = json.load(f)
    except:  # pylint: disable=bare-except
        # Old file doesn't exist/isn't readable/is corrupt
        return (True, new_version)

    # Can only do this with dictionaries
    if not isinstance(existing_data, dict):
        return (True, new_version)

    # Get the old and new versions and digests
    _, new_digest = _calculate_digest(values)
    old_version, old_digest = _calculate_digest(existing_data)

    # If content hasn't changed, don't save regardless of any version changes
    if new_digest == old_digest:
        return (False, old_version or new_version)

    # Content has changed... if the version is changed also then we're done
    old_parts = [int(v) for v in old_version.strip().split('.')]
    new_parts = [int(v) for v in new_version.strip().split('.')]
    if old_parts[:3] != new_parts[:3]:
        return (True, new_version)

    # Content has changed but version hasn't... bump build number
    parts = old_parts
    parts = parts + [0] * (4 - len(parts))
    parts[3] += 1
    bumped_version = '.'.join(str(v) for v in parts)

    return (True, bumped_version)


def _calculate_digest(values: Dict[str, Any]) -> Tuple[Optional[str], str]:
    '''Calculates the digest of the given data, returning a tuple of (version, digest).'''
    assert isinstance(values, dict)

    # Take a shallow copy of the data and remove the version field
    values = dict(values)
    version: Optional[str] = values.pop('version', None)

    # Calculate the digest of the minified output, using SHA512
    as_bytes = _format_json(values, pretty=False).encode('utf8')
    digest = hashlib.sha512(as_bytes).hexdigest()

    return (version, digest)


JOIN_LINES_REGEX = re.compile(r"(?:\n\t+)?(?<=\t)([\d.-]+,?)(?:\n\t+)?")
JOIN_COLORS_REGEX = re.compile(r"\[\n\s+([\w\" ]+),\n\s+(.{,90})\n\s+\]")
SHRINK_EMPTY_COLOR_REGEX = re.compile(r"\{\n\s+(\"\w+\": \w+)\n\s+\}")


def _format_json(data, pretty=False):
    if pretty:
        json_string = json.dumps(data, indent='\t', default=property_serializer)
        json_string = re.sub(JOIN_LINES_REGEX, r" \1", json_string)
        json_string = re.sub(JOIN_COLORS_REGEX, r"[ \1, \2 ]", json_string)
        json_string = re.sub(SHRINK_EMPTY_COLOR_REGEX, r"{ \1 }", json_string)
        json_string = re.sub(r'(\d)\]', r'\1 ]', json_string)
    else:
        json_string = json.dumps(data, indent=None, separators=(',', ':'), default=property_serializer)
    return json_string


def _save_as_json(data, filename, pretty=False):
    json_string = _format_json(data, pretty)
    with open(filename, 'w', newline='\n') as f:
        f.write(json_string)
