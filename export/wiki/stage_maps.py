from logging import NullHandler, getLogger
from pathlib import Path, PurePosixPath
from types import GeneratorType
from typing import Any, Dict, Iterable, List, Optional, Set

from ark.overrides import get_overrides_for_map
from automate.exporter import ExportManager, ExportRoot, ExportStage
from automate.jsonutils import save_json_if_changed
from automate.version import createExportVersion
from ue.gathering import gather_properties
from ue.utils import sanitise_output

from .maps.data_container import MapInfo
from .maps.discovery import LevelDiscoverer
from .maps.gathering import EXPORTS, find_gatherer_by_category_name, find_gatherer_for_export
from .maps.geo import GeoCoordCalculator

logger = getLogger(__name__)
logger.addHandler(NullHandler())

__all__ = [
    'MapStage',
]


class MapStage(ExportStage):
    discoverer: LevelDiscoverer

    def initialise(self, manager: ExportManager, root: ExportRoot):
        super().initialise(manager, root)
        self.discoverer = LevelDiscoverer(self.manager.loader)

    def get_format_version(self) -> str:
        return '1'

    def get_name(self) -> str:
        return 'maps'

    def extract_core(self, path: Path):
        '''Perform extraction for core (non-mod) data.'''
        if not self.manager.config.export_wiki.ExportVanillaMaps:
            return

        # Core versions are based on the game version and build number
        version = createExportVersion(self.manager.arkman.getGameVersion(), self.manager.arkman.getGameBuildId())  # type: ignore

        # Extract every core map
        maps = self._group_levels_by_directory(self.discoverer.discover_vanilla_levels())
        for directory, levels in maps.items():
            directory_name = directory.split('/')[-1]
            if self.manager.config.extract_maps and directory_name not in self.manager.config.extract_maps:
                continue
            logger.info(f'Performing extraction from map: {directory}')
            self._extract_and_save(version, path, directory_name, levels)

    def extract_mod(self, path: Path, modid: str):
        '''Perform extraction for mod data.'''
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        if int(mod_data.get('type', 1)) != 2:
            return
        selectable_maps = mod_data.get('maps', None)
        if not selectable_maps:
            return

        # Core versions are based on the game version and build number
        version = createExportVersion(self.manager.arkman.getGameVersion(), self.manager.arkman.getGameBuildId())  # type: ignore

        # Extract the map
        path = (path / f'{modid}-{mod_data["name"]}')
        maps = self._group_levels_by_directory(self.discoverer.discover_mod_levels(modid))
        for directory, levels in maps.items():
            directory_name = directory.split('/')[-1]
            if self.manager.config.extract_maps and directory_name not in self.manager.config.extract_maps:
                continue
            logger.info(f'Performing extraction from map: {directory}')
            self._extract_and_save(version, path, directory_name, levels, known_persistent=f'{directory}/{selectable_maps[0]}')

    def _extract_and_save(self,
                          version: str,
                          base_path: Path,
                          relative_path: str,
                          levels: List[str],
                          known_persistent: Optional[str] = None):
        # Work out the output path
        output_path = Path(base_path / relative_path)

        # Do the actual export
        intermediate = self._gather_data_from_levels(levels, known_persistent=known_persistent)
        if not intermediate.data['worldSettings']:
            logger.error(f'World settings were not extracted from {relative_path} - data will not be emitted.')
            return
        self._convert_data_for_export(intermediate)

        # Save all files if the data changed
        for file_name in EXPORTS:
            self._save_section(version, output_path, file_name, intermediate)

    def _save_section(self, version: str, base_path: Path, file_name: str, intermediate: MapInfo):
        # Setup the output structure
        results: Dict[str, Any] = dict()
        format_version = self.get_format_version()
        output: Dict[str, Any] = dict(version=version, format=format_version)
        output['persistentLevel'] = intermediate.persistent_level

        # Add exported data to the output
        for helper in EXPORTS[file_name]:
            output_key = helper.get_export_name()
            if output_key in intermediate.data:
                results[output_key] = intermediate.data[output_key]

        # Stop if no data has been extracted from this section
        if not results:
            return
        output.update(results)

        # Save if the data changed
        pretty_json = self.manager.config.export_wiki.PrettyJson
        if pretty_json is None:
            pretty_json = True
        save_json_if_changed(output, (base_path / file_name).with_suffix('.json'), pretty_json)

    def _group_levels_by_directory(self, assetnames: Iterable[str]) -> Dict[str, List[str]]:
        '''
        Takes an unsorted list of levels and groups them by directory.
        '''
        levels: Dict[str, Set[str]] = dict()

        for assetname in assetnames:
            path = assetname[:assetname.rfind('/')]
            if path not in levels:
                levels[path] = set()
            levels[path].add(assetname)

        return {path: list(sorted(names)) for path, names in levels.items()}

    def _gather_data_from_levels(self, levels: List[str], known_persistent: Optional[str] = None) -> MapInfo:
        '''
        Goes through each sublevel, gathering data and looking for the persistent level.
        '''
        map_info = MapInfo(data=dict())
        for assetname in levels:
            asset = self.manager.loader[assetname]

            # Check if asset is a persistent level and mark it as such in map info object
            if not getattr(asset, 'tile_info', None) and (not known_persistent or known_persistent == assetname):
                if getattr(map_info, 'persistent_level', None):
                    logger.warning(
                        f'Found another persistent level ({assetname}), but {map_info.persistent_level} was located earlier: skipping.'
                    )
                    continue
                map_info.persistent_level = assetname

            # Go through each export and, if valuable, gather data from it.
            for export in asset.exports:
                helper = find_gatherer_for_export(export)
                if helper:
                    category_name = helper.get_export_name()

                    # Extract data using helper class.
                    try:
                        data = helper.extract(proxy=gather_properties(export))
                    except:  # pylint: disable=bare-except
                        logger.warning(f'Gathering properties failed for export "{export.name}" in {assetname}', exc_info=True)
                        continue
                    if not data:
                        continue

                    # Make sure the data list is initialized.
                    if category_name not in map_info.data:
                        map_info.data[category_name] = list()

                    if isinstance(data, GeneratorType):
                        data_fragments: list = sanitise_output(list(data))
                        for fragment in data_fragments:
                            if fragment:
                                map_info.data[category_name].append(fragment)
                    else:
                        fragment = sanitise_output(data)
                        map_info.data[category_name].append(fragment)

            # Preemptively remove the level from linker cache.
            self.manager.loader.cache.remove(assetname)

        return map_info

    def _convert_data_for_export(self, map_info: MapInfo):
        '''
        Converts XYZ coords to long/lat keys, and sorts data by every category's criteria.
        '''
        # Create longitude and latitude calculators
        for candidate in map_info.data['worldSettings']:
            if candidate['source'] == map_info.persistent_level:
                world_settings = candidate
                del world_settings['source']
                break
        map_info.lat = GeoCoordCalculator(world_settings['latOrigin'], world_settings['latScale'])
        map_info.long = GeoCoordCalculator(world_settings['longOrigin'], world_settings['longScale'])

        # Run data-specific conversions
        for key, values in map_info.data.items():
            # Helper class exists if data has been exported from it.
            helper = find_gatherer_by_category_name(key)
            # Add lat and long keys as world settings have been found.
            for data in values:
                helper.before_saving(map_info, data)  # type:ignore

        # Move the world settings out of the single element list
        map_info.data['worldSettings'] = world_settings
