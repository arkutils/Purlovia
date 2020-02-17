from logging import NullHandler, getLogger
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Set, Union

from ark.overrides import get_overrides_for_map
from automate.exporter import ExportManager, ExportRoot
from automate.jsonutils import save_json_if_changed
from processing.common import SVGBoundaries

from .region_maps.svg import generate_svg_map
from .stage_base import ProcessingStage

logger = getLogger(__name__)
logger.addHandler(NullHandler())

__all__ = [
    'WikiRegionMapsStage',
]


class WikiRegionMapsStage(ProcessingStage):
    def get_skip(self) -> bool:
        return not self.manager.config.processing.ProcessBiomeData

    def extract_core(self, _: Path):
        # Find data of maps with biomes
        map_set: List[Path] = [path.parent for path in self.wiki_path.glob('*/biomes.json')]

        for map_data_path in map_set:
            self._process(map_data_path, None)

    def extract_mod(self, _: Path, modid: str):
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        if int(mod_data.get('type', 1)) != 2:
            # Mod is not a map, skip it.
            return

        # Find data of maps with biomes
        root_wiki_mod_dir = Path(self.wiki_path / f'{modid}-{mod_data["name"]}')
        map_set: List[Path] = [path.parent for path in root_wiki_mod_dir.glob('*/biomes.json')]

        for map_data_path in map_set:
            self._process(map_data_path, modid)

    def _process(self, path: Path, modid: Optional[str]):
        map_name = path.name
        logger.info(f'Processing data of map: {map_name}')

        # Load exported data
        data_biomes = self.load_json_file(path / 'biomes.json')
        data_map_settings = self.load_json_file(path / 'world_settings.json')
        if not data_biomes or not data_map_settings:
            logger.warning(f'Data required by the processor is missing or invalid. Skipping.')
            return
        map_display_name = data_map_settings['worldSettings']['name']

        config = get_overrides_for_map(data_map_settings['persistentLevel'], None).svgs
        bounds = SVGBoundaries(
            size=1024,
            border_top=config.border_top,
            border_left=config.border_left,
            coord_width=config.border_right - config.border_left,
            coord_height=config.border_bottom - config.border_top,
        )
        svg = generate_svg_map(bounds, map_name, data_map_settings['worldSettings'], data_biomes, modid is not None)
        if svg:
            self.save_raw_file(svg, (path / f'Regions {map_name}.svg'))
