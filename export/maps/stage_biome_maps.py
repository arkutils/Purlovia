from pathlib import Path
from typing import Optional

from ark.mod import get_official_mods
from ark.overrides import get_overrides_for_map
from utils.log import get_logger

from .common import SVGBoundaries
from .region_maps.svg import generate_svg_map
from .stage_base import ProcessingStage

logger = get_logger(__name__)

__all__ = [
    'ProcessBiomeMapsStage',
]


class ProcessBiomeMapsStage(ProcessingStage):
    def get_name(self) -> str:
        return "biome_maps"

    def extract_core(self, _: Path):
        # Find data of maps with biomes
        map_set = self.find_official_maps(True, keyword='biomes')

        for _name, data_path in map_set:
            self._process(self.wiki_path / data_path, None)

    def extract_mod(self, _: Path, modid: str):
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        if int(mod_data.get('type', 1)) != 2 and modid not in get_official_mods():
            # Mod is not a map, skip it.
            return

        # Find data of maps with biomes
        map_set = self.find_maps(modid, keyword='biomes')

        for _name, data_path in map_set:
            self._process(self.wiki_path / data_path, modid)

    def _get_svg_output_path(self, map_name: str, modid: Optional[str]) -> Path:
        if not modid:
            # Core maps
            #   processed/wiki-maps/regions/Map.svg
            return (self.output_path / 'regions' / map_name).with_suffix('.svg')

        # Mods
        #   processed/wiki-maps/regions/Id-Mod.svg
        return (self.output_path / 'regions' / self.get_mod_subroot_name(modid)).with_suffix('.svg')

    def _process(self, in_path: Path, modid: Optional[str]):
        map_name = in_path.name
        logger.info(f'Processing data of map: {map_name}')

        # Load exported data
        data_biomes = self.load_json_file(in_path / 'biomes.json')
        data_map_settings = self.load_json_file(in_path / 'world_settings.json')
        if not data_biomes or not data_map_settings:
            logger.debug('Data required by the processor is missing or invalid. Skipping.')
            return

        config = get_overrides_for_map(data_map_settings['persistentLevel'], None).svgs
        bounds = SVGBoundaries(
            size=1024,
            border_top=config.border_top,
            border_left=config.border_left,
            coord_width=config.border_right - config.border_left,
            coord_height=config.border_bottom - config.border_top,
        )

        svg = generate_svg_map(bounds, map_name, data_map_settings['worldSettings'], data_biomes, modid is not None)
        filename = self._get_svg_output_path(map_name, modid)
        if svg:
            self.save_raw_file(svg, filename)
        elif filename.is_file():
            filename.unlink()
