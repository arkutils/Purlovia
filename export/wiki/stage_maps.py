from pathlib import Path, PurePosixPath
from types import GeneratorType
from typing import Any, Dict, Iterable, List, Optional, Set

from ark.overrides import get_overrides_for_map
from automate.exporter import ExportManager, ExportRoot, ExportStage
from automate.jsonutils import save_json_if_changed
from automate.version import createExportVersion
from ue.gathering import gather_properties
from ue.utils import get_leaf_from_assetname, sanitise_output
from utils.log import get_logger

from .maps.discovery import LevelDiscoverer, group_levels_by_directory
from .maps.world import World

logger = get_logger(__name__)

__all__ = [
    'MapStage',
]


class MapStage(ExportStage):
    discoverer: LevelDiscoverer

    def initialise(self, manager: ExportManager, root: ExportRoot):
        super().initialise(manager, root)
        self.discoverer = LevelDiscoverer(self.manager.loader)

    def get_name(self) -> str:
        return 'maps'

    def extract_core(self, path: Path):
        '''Perform extraction for core (non-mod) data.'''
        if not self.manager.config.export_wiki.ExportVanillaMaps:
            return

        # Core versions are based on the game version and build number
        version = createExportVersion(self.manager.arkman.getGameVersion(), self.manager.arkman.getGameBuildId())  # type: ignore

        # Extract every core map
        maps = group_levels_by_directory(self.discoverer.discover_vanilla_levels())
        for directory, levels in maps.items():
            directory_name = get_leaf_from_assetname(directory)
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
        maps = group_levels_by_directory(self.discoverer.discover_mod_levels(modid))
        for directory, levels in maps.items():
            directory_name = get_leaf_from_assetname(directory)
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

        # Do the actual extraction
        world = World(known_persistent)
        for assetname in levels:
            asset = self.manager.loader[assetname]
            world.ingest_level(asset)

        if not world.bind_settings():
            logger.error(f'No world settings could have been found for {relative_path} - data will not be emitted.')
            return None

        # Export
        world.convert_for_export()
        for section_name, section_data in world.construct_export_files():
            self._save_section(version, output_path, section_name, section_data)

    def _save_section(self, version: str, base_path: Path, file_name: str, data: Dict[str, Any]):
        output_path = (base_path / file_name).with_suffix('.json')

        if not data:
            # No data for this file. Remove an existing one if it exists
            if output_path.is_file():
                output_path.unlink()
            return

        # Setup the output structure
        output: Dict[str, Any] = dict(version=version)
        output.update(data)

        pretty_json = self.manager.config.export_wiki.PrettyJson
        if pretty_json is None:
            pretty_json = True

        # Save if the data changed
        save_json_if_changed(output, output_path, pretty_json)
