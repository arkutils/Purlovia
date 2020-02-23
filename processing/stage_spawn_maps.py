from logging import NullHandler, getLogger
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Set, Union

from ark.overrides import get_overrides_for_map
from automate.exporter import ExportManager
from processing.common import SVGBoundaries, remove_unicode_control_chars

from .spawn_maps.game_mod import merge_game_mod_groups
from .spawn_maps.rarity import apply_ideal_global_swaps, apply_ideal_grouplevel_swaps, calculate_blueprint_freqs, fix_up_groups, make_random_class_weights_dict
from .spawn_maps.species import generate_dino_mappings
from .spawn_maps.svg import generate_svg_map
from .stage_base import ProcessingStage

logger = getLogger(__name__)
logger.addHandler(NullHandler())

__all__ = [
    'ProcessSpawnMapsStage',
]


class ProcessSpawnMapsStage(ProcessingStage):
    def get_skip(self) -> bool:
        return not self.manager.config.processing.ProcessSpawns

    def extract_core(self, _: Path):
        # Find data of maps with NPC spawns
        map_set: List[Path] = [path.parent for path in self.wiki_path.glob('*/npc_spawns.json')]

        # Load ASB and spawning group data
        data_asb = self._load_asb(None)
        data_groups = self._load_spawning_groups(None)
        if not data_asb or not data_groups:
            logger.warning(f'Data required by the processor is missing or invalid. Skipping.')
            return

        # Do all the insanity now and fix up the groups.
        fix_up_groups(data_groups)
        apply_ideal_grouplevel_swaps(data_groups)

        for map_data_path in map_set:
            self._map_process_data(map_data_path, data_asb, data_groups)

    def extract_mod(self, _: Path, modid: str):
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        mod_type = int(mod_data.get('type', 1))
        if mod_type == 1:
            self._game_mod_generate_svgs(modid, mod_data['name'])
        elif mod_type == 2:
            self._map_mod_generate_svgs(modid, mod_data['name'])

    def _load_asb(self, modid: Optional[str]):
        path = self.asb_path
        if modid:
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            path = (path / f'{modid}-{mod_data["name"]}.json')
        else:
            path = (path / 'values.json')
        return self.load_json_file(path)

    def _load_spawning_groups(self, modid: Optional[str]):
        path = self.wiki_path
        if modid:
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            path = (path / f'{modid}-{mod_data["name"]}/spawngroups.json')
        else:
            path = (path / 'spawngroups.json')
        return self.load_json_file(path)

    def _map_mod_generate_svgs(self, modid: str, mod_name: str):
        # Find data of maps with NPC spawns
        root_wiki_mod_dir = Path(self.wiki_path / f'{modid}-{mod_name}')
        map_set: List[Path] = [path.parent for path in root_wiki_mod_dir.glob('*/npc_spawns.json')]

        # Load and merge ASB data
        data_asb_core = self._load_asb(None)
        data_asb_mod = self._load_asb(modid)
        if not data_asb_core or not data_asb_mod:
            logger.warning(f'Data required by the processor is missing or invalid. Skipping.')
            return
        data_asb_mod['species'] += data_asb_core['species']

        # Load and merge spawning group data
        data_groups_core = self._load_spawning_groups(None)
        data_groups_mod = self._load_spawning_groups(modid)
        if not data_groups_core or not data_groups_mod:
            logger.warning(f'Data required by the processor is missing or invalid. Skipping.')
            return
        data_groups_mod['spawngroups'] += data_groups_core['spawngroups']

        # Do all the insanity now and fix up the groups.
        fix_up_groups(data_groups_mod)
        apply_ideal_grouplevel_swaps(data_groups_mod)

        for map_data_path in map_set:
            self._map_process_data(map_data_path, data_asb_mod, data_groups_mod, None)

    def _game_mod_generate_svgs(self, modid: str, mod_name: str):
        # Find data of core maps with NPC spawns
        map_set: List[Path] = [path.parent for path in self.wiki_path.glob('*/npc_spawns.json')]

        # Load ASB and spawning group data
        data_asb = self._load_asb(modid)
        data_groups = self._load_spawning_groups(None)
        data_groups_mod = self._load_spawning_groups(modid)
        if not data_asb or not data_groups or not data_groups_mod:
            logger.warning(f'Data required by the processor is missing or invalid. Skipping.')
            return

        # Merge spawning group data
        if 'externalGroupChanges' in data_groups_mod:
            merge_game_mod_groups(data_groups['spawngroups'], data_groups_mod['externalGroupChanges'])

        # Do all the insanity now and fix up the groups.
        fix_up_groups(data_groups)
        apply_ideal_grouplevel_swaps(data_groups)
        apply_ideal_global_swaps(data_groups, data_groups_mod.get('classSwaps', []))

        for map_data_path in map_set:
            self._map_process_data(map_data_path, data_asb, data_groups, (self.wiki_path / f'{modid}-{mod_name}' / 'spawn_maps'))

    def _map_process_data(self, data_path: Path, asb, spawngroups, output_path: Optional[Path] = None):
        map_name = data_path.name
        logger.info(f'Processing data of map: {map_name}')

        # Load exported data
        data_map_settings = self.load_json_file(data_path / 'world_settings.json')
        data_map_spawns = self.load_json_file(data_path / 'npc_spawns.json')
        if not data_map_settings or not data_map_spawns:
            logger.warning(f'Data required by the processor is missing or invalid. Skipping.')
            return

        # Generate mapping table (blueprint path to name)
        species = generate_dino_mappings(self.manager.loader, asb)

        # Get world-level random dino class swaps.
        random_class_weights = data_map_settings['worldSettings'].get('randomNPCClassWeights', [])
        class_swaps = make_random_class_weights_dict(random_class_weights)

        if not output_path:
            if data_path.name != map_name:
                output_path = (data_path / 'spawn_maps' / map_name)
            else:
                output_path = (data_path / 'spawn_maps')
        else:
            output_path = (output_path / map_name)

        for descriptive_name, blueprints in species.items():
            # The rarity is arbitrarily divided in 6 groups from "very rare" (0) to "very common" (5)
            freqs = calculate_blueprint_freqs(spawngroups, class_swaps, blueprints)

            config = get_overrides_for_map(data_map_settings['persistentLevel'], None).svgs
            bounds = SVGBoundaries(
                size=300,
                border_top=config.border_top,
                border_left=config.border_left,
                coord_width=config.border_right - config.border_left,
                coord_height=config.border_bottom - config.border_top,
            )

            svg = generate_svg_map(bounds, descriptive_name, freqs, data_map_spawns)
            if svg:
                clean_species_name = remove_unicode_control_chars(descriptive_name)
                self.save_raw_file(svg, (output_path / f'Spawning_{clean_species_name}.svg'))
