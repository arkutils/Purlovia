from logging import NullHandler, getLogger
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Set, Union

from automate.exporter import ExportManager, ExportRoot
from automate.jsonutils import save_json_if_changed
from export.asb.root import ASBRoot
from export.asb.stage_species import SpeciesStage
from export.wiki.maps.discovery import LevelDiscoverer
from export.wiki.root import WikiRoot
from export.wiki.stage_maps import MapStage
from export.wiki.stage_spawn_groups import SpawnGroupStage

from .region_maps.svg import generate_svg_map
from .stage_base import ProcessingStage

logger = getLogger(__name__)
logger.addHandler(NullHandler())

__all__ = [
    'WikiRegionMapsStage',
]


class WikiRegionMapsStage(ProcessingStage):
    def get_skip(self) -> bool:
        return False

    def process_core(self, path: Path):
        # Find data of maps with biomes
        base_map_output_path = Path(self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir)
        map_data_dirs: List[Path] = list(base_map_output_path.glob('*/biomes.json'))
        map_data_dirs = [path.parent for path in map_data_dirs]

        for map_data_path in map_data_dirs:
            map_name = map_data_path.name
            logger.info(f'Processing data of map: {map_name}')
            # Load exported data
            map_biomes = self.load_json_file(Path(map_data_path) / 'biomes.json')
            map_settings = self.load_json_file(map_data_path / 'world_settings.json')

            map_size = 1024
            svg = generate_svg_map(f'({map_name})', map_settings['worldSettings'], map_biomes, map_size, 7.2, 7.2, 92.8 - 7.2,
                                   92.8 - 7.2)
            if svg:
                self._save_raw_file(svg, (path / f'Regions {map_name}').with_suffix('.svg'))

    def _save_raw_file(self, content: Any, path: Path):
        parent = Path(path).parent
        parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as fp:
            fp.write(content)

    def _group_levels_by_directory(self, assetnames: Iterable[str]) -> Dict[str, List[str]]:
        # HACK: Copied straight from stage_maps.
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

    def process_mod(self, path: Path, modid: str):
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        if int(mod_data.get('type', 1)) != 2:
            return

        # Find data of maps with biomes
        base_map_output_path = Path(self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir /
                                    f'{modid}-{mod_data["name"]}')
        map_data_dirs: List[Path] = list(base_map_output_path.glob('*/biomes.json'))
        map_data_dirs = [path.parent for path in map_data_dirs]

        for map_data_path in map_data_dirs:
            map_name = map_data_path.name
            logger.info(f'Processing data of map: {map_name}')
            # Load exported data
            map_biomes = self.load_json_file(Path(map_data_path) / 'biomes.json')
            map_settings = self.load_json_file(map_data_path / 'world_settings.json')
            map_display_name = map_settings['worldSettings']['name']

            map_size = 1024
            svg = generate_svg_map(f' ({map_display_name})', map_settings['worldSettings'], map_biomes, map_size, 7.2, 7.2,
                                   92.8 - 7.2, 92.8 - 7.2)
            if svg:
                self._save_raw_file(svg, (path / f'Regions {map_name}').with_suffix('.svg'))


#
