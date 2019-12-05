from logging import NullHandler, getLogger
from pathlib import Path
from typing import *

from ark.export_wiki.base import MapGathererBase
from ark.export_wiki.consts import LEVEL_SCRIPT_ACTOR_CLS, WORLD_CLS
from ark.export_wiki.discovery import LevelDiscoverer
from ark.export_wiki.gathering import find_gatherer_by_category_name, find_gatherer_for_export
from ark.export_wiki.map import MapInfo
from automate.ark import ArkSteamManager
from automate.jsonutils import save_as_json, should_save_json
from automate.version import createExportVersion
from config import ConfigFile, get_global_config
from ue.asset import UAsset
from ue.gathering import gather_properties
from ue.hierarchy import MissingParent, find_sub_classes, inherits_from
from ue.loader import AssetNotFound
from utils.strings import get_valid_filename

logger = getLogger(__name__)
logger.addHandler(NullHandler())

__all__ = [
    'export_map_data',
]


def export_map_data(arkman: ArkSteamManager, modids: Set[str], config: ConfigFile):
    logger.info('Wiki export beginning')
    if config.settings.SkipExtract or config.export_wiki.Skip:
        logger.info('(skipped)')
        return

    # Ensure the output directory exists
    outdir = Path(config.settings.OutputPath)
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
        self.loader = arkman.getLoader()
        self.game_version = self.arkman.getGameVersion()
        self.discoverer = LevelDiscoverer(self.loader)

    def perform(self):
        self._prepare_versions()
        # Clear the cache after other exports
        self.loader.wipe_cache()

        if self.config.export_wiki.ExportVanillaMaps:
            logger.info('Beginning export of vanilla maps')
            self._export_vanilla()

        #for modid in self.modids:
        #    logger.info(f'Beginning mod {modid} export')
        #    self._export_mod(modid)

        #    # Remove assets with this mod's prefix from the cache
        #    prefix = '/Game/Mods/' + self.loader.get_mod_name('/Game/Mods/' + modid)
        #    self.loader.wipe_cache_with_prefix(prefix)

        logger.info('Max memory: %6.2f Mb', self.loader.max_memory / 1024.0 / 1024.0)
        logger.info('Max cache entries: %d', self.loader.max_cache)

    def _group_levels_by_directory(self, assetnames: Iterable) -> Dict[str, List[str]]:
        '''
        Takes an unsorted list of levels and groups them by directory.
        '''
        levels: Dict[str, List[str]] = dict()

        for assetname in assetnames:
            path = assetname[:assetname.rfind('/')]
            if path not in levels:
                levels[path] = list()
            levels[path].append(assetname)

        return levels

    def _prepare_versions(self):
        if not self.game_version:
            raise ValueError("Game not installed or ArkSteamManager not yet initialised")

    def _create_version(self, timestamp: str) -> str:
        return createExportVersion(self.game_version, timestamp)  # type: ignore

    def _export_vanilla(self):
        game_buildid = self.arkman.getGameBuildId()
        version = self._create_version(game_buildid)
        maps = self._group_levels_by_directory(self.discoverer.discover_vanilla_levels())

        for map_directory in maps:
            logger.info(f'Exporting data from map: {map_directory}')
            data = self._gather_data_from_levels(map_directory, maps[map_directory])
            self._sort_data(data)
            self._export_values(data, version)

    def _export_mod(self, modid: str):
        moddata = self.arkman.getModData(modid)
        if not moddata:
            raise ValueError("Mod not installed or ArkSteamManager not yet initialised")
        version = self._create_version(moddata['version'])

        #if int(moddata.get('type', 1)) != 2:
        #    return self._export_modded_spawn_groups(modid, version, moddata)

        #map_list = moddata.get('maps', None)
        #if map_list:
        #    for map_name in map_list:
        #        self._export_level(f'/Game/Mods/{modid}/{map_name}', version, moddata)
        #else:
        #    logger.warning(f'Mod {modid} is missing its list of maps.')

    def _gather_data_from_levels(self, directory: str, levels: List[str]) -> MapInfo:
        '''
        Goes through each sublevel, gathering data and looking for the persistent level.
        '''
        map_info = MapInfo(name=directory[directory.rfind('/') + 1:], data=dict())
        for assetname in levels:
            asset = self.loader[assetname]

            # Check if asset is a persistent level and collect data from it.
            if not getattr(asset, 'tile_info', None):
                if getattr(map_info, 'persistent_level', None):
                    logger.warning(
                        f'Found another persistent level ({assetname}) but {map_info.persistent_level} was located earlier: skipping.'
                    )
                    continue

                map_info.persistent_level = assetname
                # TODO: Gather data from persistent level

            # Go through each export and, if valuable, gather data from it.
            for export in asset.exports:
                helper = find_gatherer_for_export(export)
                if helper:
                    # Make sure the data list is initialized.
                    category_name = helper.get_category_name()  # type:ignore
                    if category_name not in map_info.data:
                        map_info.data[category_name] = list()

                    # Extract data and add it to the list.
                    try:
                        export_data = helper.extract(proxy=gather_properties(export))  # type:ignore
                    except:  # pylint: disable=bare-except
                        logger.warning(f'Gathering properties failed for export "{export.name}" in {assetname}', exc_info=True)
                        continue
                    if export_data:
                        map_info.data[category_name].append(export_data)

            # Preemptively remove the level from linker cache.
            self.loader.cache.remove(assetname)

        return map_info

    def _sort_data(self, map_info: MapInfo):
        '''
        Sorts data by every category's criteria.
        '''
        for key, values in map_info.data.items():
            helper = find_gatherer_by_category_name(key)
            values.sort(key=helper.sorting_key)

    def _export_values(self, map_info: MapInfo, version: str, other: Dict = None, moddata: Optional[Dict] = None):
        values: Dict[str, Any] = dict()
        values['map'] = map_info.name
        values['format'] = '1.0'

        if moddata:
            filename = f"{moddata['id']}-{moddata['name']}-{map_info.name}"
            filename = get_valid_filename(filename)
            title = moddata['title'] or moddata['name']
            values['mod'] = dict(id=moddata['id'], tag=moddata['name'], title=title)
        else:
            filename = map_info.name

        values['version'] = version
        values.update(map_info.data)

        if other:
            values.update(other)

        fullpath = Path(self.config.settings.OutputPath / self.config.export_wiki.PublishSubDir / dirname)
        fullpath.mkdir(parents=True, exist_ok=True)
        fullpath = (fullpath / 'map').with_suffix('.json')
        self._save_json_if_changed(values, fullpath)

    #def _export_world_data(self, world_data: WorldData, version: str, moddata: Optional[Dict] = None):
    #    values: Dict[str, Any] = dict()

    #    if moddata:
    #        dirname = f"{moddata['id']}-{moddata['name']}-{world_data.name}"
    #        dirname = get_valid_filename(dirname)
    #        title = moddata['title'] or moddata['name']
    #        values['mod'] = dict(id=moddata['id'], tag=moddata['name'], title=title)
    #    else:
    #        dirname = get_valid_filename(world_data.name)

    #    values['version'] = version
    #    values.update(world_data.format_for_json())

    #    fullpath = (self.config.settings.OutputPath / self.config.export_wiki.PublishSubDir / dirname)
    #    fullpath.mkdir(parents=True, exist_ok=True)
    #    fullpath = (fullpath / 'map').with_suffix('.json')
    #    self._save_json_if_changed(values, fullpath)

    #def _export_modded_spawn_groups(self, modid: str, version: str, moddata: dict):
    #    mod_pgd = moddata.get('package', None)
    #    if not mod_pgd:
    #        logger.warning(f'PrimalGameData information missing for mod {modid}')
    #        return
    #    pgd = self.loader[mod_pgd]
    #    groups = gather_spawn_groups_from_pgd(self.loader, pgd)
    #    if not groups:
    #        return

    #    values: Dict[str, Any] = dict()
    #    dirname = f"{moddata['id']}-{moddata['name']}"
    #    dirname = get_valid_filename(dirname)
    #    title = moddata['title'] or moddata['name']
    #    values['mod'] = dict(id=moddata['id'], tag=moddata['name'], title=title)
    #    values['version'] = version
    #    values['spawnGroups'] = groups

    #    fullpath = (self.config.settings.OutputPath / self.config.export_wiki.PublishSubDir / dirname)
    #    fullpath.mkdir(parents=True, exist_ok=True)
    #    fullpath = (fullpath / 'spawningGroups').with_suffix('.json')
    #    self._save_json_if_changed(values, fullpath)

    def _save_json_if_changed(self, values: Dict[str, Any], fullpath: Path):
        changed, version = should_save_json(values, fullpath)
        if changed:
            pretty = self.config.export_wiki.PrettyJson
            logger.info(f'Saving export to {fullpath} with version {version}')
            values['version'] = version
            save_as_json(values, fullpath, pretty=pretty)
        else:
            logger.info(f'No changes to {fullpath}')
