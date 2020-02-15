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
        root_wiki_dir = Path(self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir)
        map_set: List[Path] = [path.parent for path in root_wiki_dir.glob('*/biomes.json')]

        for map_data_path in map_set:
            self._process(map_data_path)

    def process_mod(self, path: Path, modid: str):
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        if int(mod_data.get('type', 1)) != 2:
            # Mod is not a map, skip it.
            return

        # Find data of maps with biomes
        root_wiki_mod_dir = Path(self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir /
                                 f'{modid}-{mod_data["name"]}')
        map_set: List[Path] = [path.parent for path in root_wiki_mod_dir.glob('*/biomes.json')]

        for map_data_path in map_set:
            self._process(map_data_path)

    def _process(self, path: Path):
        map_name = path.name
        logger.info(f'Processing data of map: {map_name}')

        # Load exported data
        data_biomes = self.load_json_file(path / 'biomes.json')
        data_map_settings = self.load_json_file(path / 'world_settings.json')
        if not data_biomes or not data_map_settings:
            logger.warning(f'Data required by the processor is missing or invalid. Skipping.')
            return
        map_display_name = data_map_settings['worldSettings']['name']

        map_size = 1024
        svg = generate_svg_map(map_display_name, data_map_settings['worldSettings'], data_biomes, map_size, 7.2, 7.2, 92.8 - 7.2,
                               92.8 - 7.2, True)
        if svg:
            self.save_raw_file(svg, (path / f'Regions {map_name}').with_suffix('.svg'))


#
