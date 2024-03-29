from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional

from ark.mod import get_official_mods
from automate.exporter import ExportManager, ExportRoot, ExportStage
from automate.hierarchy_exporter import _calculate_relative_path, _output_schema
from automate.jsonutils import save_json_if_changed
from automate.version import createExportVersion
from ue.utils import get_leaf_from_assetname
from utils.log import get_logger
from utils.strings import get_valid_filename

from .maps.discovery import LevelDiscoverer, group_levels_by_directory
from .maps.world import EXPORTS, World

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

        # Prepare a schema, if requested
        for name, model_info in EXPORTS.items():
            model, _ = model_info
            _output_schema(model, path / self._get_schema_file_path(name))

        # Core versions are based on the game version and build number
        version = createExportVersion(self.manager.arkman.getGameVersion(), self.manager.arkman.getGameBuildId())  # type: ignore

        # Extract every core map
        maps = group_levels_by_directory(self.discoverer.discover_vanilla_levels())
        for directory, levels in maps.items():
            directory_name = get_leaf_from_assetname(directory)
            if self.manager.config.extract_maps is not None and directory_name not in self.manager.config.extract_maps:
                continue

            expansion = directory_name in self.manager.config.expansions.tags()

            logger.info(f'Performing extraction from map: {directory}')
            self._extract_and_save(version, path, Path(directory_name), levels, official=True, expansion=expansion)

    def extract_mod(self, path: Path, modid: str):
        '''Perform extraction for mod data.'''
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        selectable_maps: Optional[str] = None
        if modid not in get_official_mods():
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

            persistent: Optional[str] = None
            if selectable_maps:
                persistent = f'{directory}/{selectable_maps[0]}'

            official = modid in self.manager.config.official_mods.ids()
            expansion = modid in self.manager.config.expansions.ids()

            logger.info(f'Performing extraction from map: {directory}')
            self._extract_and_save(version,
                                   path,
                                   Path(directory_name),
                                   levels,
                                   modid,
                                   persistent,
                                   official=official,
                                   expansion=expansion)

    def _extract_and_save(self,
                          version: str,
                          base_path: Path,
                          relative_path: Path,
                          levels: List[str],
                          modid: Optional[str] = None,
                          known_persistent: Optional[str] = None,
                          official: bool = False,
                          expansion: bool = False):
        # Do the actual extraction
        world = World(known_persistent)
        for assetname in levels:
            asset = self.manager.loader[assetname]
            world.ingest_level(asset)

        if not world.bind_settings():
            logger.error(f'No world settings could have been found for {relative_path} - data will not be emitted.')
            return None

        world.convert_for_export()

        # Save
        pretty_json = self.manager.config.export_wiki.PrettyJson
        if pretty_json is None:
            pretty_json = True

        for file_name, data in world.construct_export_files():
            # Work out the clean output path
            output_path = (relative_path / file_name).with_suffix('.json')
            clean_relative_path = PurePosixPath(*(get_valid_filename(p) for p in output_path.parts))

            # Remove existing file if exists and no data was found.
            if not data:
                if output_path.is_file():
                    output_path.unlink()
                continue

            # Work out schema path
            schema_path = _calculate_relative_path(clean_relative_path, self._get_schema_file_path(file_name))

            # Setup the output structure
            output: Dict[str, Any] = dict()
            output['$schema'] = str(schema_path)
            output['version'] = version
            if modid:
                mod_data = self.manager.arkman.getModData(modid)
                assert mod_data
                title = mod_data['title'] or mod_data['name']
                output['mod'] = dict(id=modid, tag=mod_data['name'], title=title)
                if official:
                    output['mod']['official'] = True
                if expansion:
                    output['mod']['expansion'] = True
            else:
                core_data = dict()
                if official:
                    core_data['official'] = True
                if expansion:
                    core_data['expansion'] = True
                if core_data:
                    output['core'] = core_data
            output.update(data)

            # Save if the data changed
            save_json_if_changed(output, (base_path / output_path), pretty_json)

    def _get_schema_file_path(self, file_name: str) -> PurePosixPath:
        return PurePosixPath('.schema') / f'maps_{file_name}.json'
