import shutil
from collections import namedtuple
from pathlib import Path
from typing import Any, Dict, Optional

from ark.overrides import get_overrides_for_map, get_overrides_for_mod
from utils.log import get_logger

from .common import SVGBoundaries, remove_unicode_control_chars
from .spawn_maps.game_mod import apply_remaps, is_custom_map, merge_game_mod_groups
from .spawn_maps.species import calculate_blueprint_freqs, determine_tamability, generate_dino_mappings
from .spawn_maps.svg import generate_svg_map
from .spawn_maps.swaps import apply_ideal_global_swaps, apply_ideal_grouplevel_swaps, \
    copy_spawn_groups, fix_up_groups, inflate_swap_rules
from .stage_base import ProcessingStage

logger = get_logger(__name__)

__all__ = [
    'ProcessSpawnMapsStage',
]

_SpawningData = namedtuple('_SpawningData', ('asb', 'species', 'groups', 'global_swaps'))


class ProcessSpawnMapsStage(ProcessingStage):
    def get_name(self) -> str:
        return "spawn_maps"

    def extract_core(self, _: Path):
        self.get_data_and_generate(None)

    def extract_mod(self, _: Path, modid: str):
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        if modid:
            overrides = get_overrides_for_mod(modid)
            if overrides.skip_spawn_maps:
                return

        self.get_data_and_generate(mod_data)

    def load_asb(self, modid: Optional[str]):
        if modid:
            path = (self.asb_path / f'{self.get_mod_subroot_name(modid)}.json')
        else:
            path = (self.asb_path / 'values.json')
        return self.load_json_file(path)

    def load_spawning_groups(self, modid: Optional[str]):
        if modid:
            path = (self.wiki_path / self.get_mod_subroot_name(modid) / 'spawn_groups.json')
        else:
            path = (self.wiki_path / 'spawn_groups.json')
        return self.load_json_file(path)

    def get_spawning_groups(self, modid: Optional[str], is_game_mod: bool = False):
        core_data = self.load_spawning_groups(None)
        if not core_data:
            return None, None
        swaps = core_data['classSwaps']

        # Load data from separated official mods
        for official_mod in self.manager.config.settings.SeparateOfficialMods:
            core_data_2 = self.load_spawning_groups(official_mod)
            if core_data_2:
                core_data['spawngroups'] += core_data_2['spawngroups']

        # Load mod data and merge it with core
        if modid:
            mod_data = self.load_spawning_groups(modid)
            if not mod_data:
                # No data exists.
                return None, None
            # Join group container lists
            mod_data['spawngroups'] += core_data['spawngroups']

            if is_game_mod:
                swaps = mod_data.get('classSwaps', [])
                # Join group mods with core groups
                if 'externalGroupChanges' in mod_data:
                    merge_game_mod_groups(mod_data['spawngroups'], mod_data['externalGroupChanges'])

            data = mod_data
        else:
            # Not a mod.
            data = core_data

        # Do all the insanity now and fix up the groups
        fix_up_groups(data['spawngroups'])
        apply_ideal_grouplevel_swaps(data['spawngroups'])
        inflate_swap_rules(swaps)
        apply_remaps(data['spawngroups'], data.get('dinoRemaps', None))
        # Global class swaps will be applied during freq calculations

        return data['spawngroups'], swaps

    def get_data_and_generate(self, mod: Optional[Dict[str, Any]]):
        modid = mod['id'] if mod else None
        is_a_map = not mod or is_custom_map(mod)

        if not mod:
            # Core
            asb = self.load_asb(None)
            spgroups, klsswaps = self.get_spawning_groups(None)
        elif is_a_map:
            # Custom map or separate map
            asb = self.load_asb(None)
            asbmod = self.load_asb(modid)
            if asbmod:
                asb['species'] += asbmod['species']
            spgroups, klsswaps = self.get_spawning_groups(modid)
        else:
            # Game mod
            asb = self.load_asb(modid)
            spgroups, klsswaps = self.get_spawning_groups(modid, is_game_mod=True)

        # If required data couldn't be loaded, skip.
        if not asb or not spgroups:
            logger.debug('Data required by the processor is missing or invalid. Skipping.')
            return

        # Find target maps
        if not mod:
            # Core
            maps = self.find_official_maps(True, keyword='npc_spawns')
        elif is_a_map:
            # Custom map or separate map
            maps = self.find_maps(self.wiki_path / self.get_mod_subroot_name(modid))
        else:
            # Game mod
            maps = self.find_official_maps(False, keyword='npc_spawns')

        spawndata = _SpawningData(
            asb=asb,
            # Generate species groups
            species=generate_dino_mappings(asb),
            # Original spawning groups
            groups=spgroups,
            global_swaps=klsswaps,
        )

        for map_path in maps:
            # Determine base output path
            output_path = self._get_svg_output_path(map_path, map_path.name, modid)

            # Remove existing directory
            if output_path.is_dir():
                shutil.rmtree(output_path)

            # Generate the maps
            self._map_process_data(map_path, spawndata, output_path)

    def _get_svg_output_path(self, data_path: Path, map_name: str, modid: Optional[str]) -> Path:
        if not modid:
            # Core maps
            #   processed/wiki-maps/spawns/Map/
            return (self.output_path / 'spawns' / map_name)

        # Mods
        #   processed/wiki-maps/spawns/Map/Id-Mod/
        return (self.output_path / 'spawns' / map_name / self.get_mod_subroot_name(modid))

    def _map_process_data(self, data_path: Path, spawndata: _SpawningData, output_path: Path):
        logger.info(f'Processing data of map: {data_path.name}')

        # Load exported data
        data_map_settings = self.load_json_file(self.wiki_path / data_path / 'world_settings.json')
        data_map_spawns = self.load_json_file(self.wiki_path / data_path / 'npc_spawns.json')
        if not data_map_settings or not data_map_spawns:
            logger.debug('Data required by the processor is missing or invalid. Skipping.')
            return

        # Initialize bound structure for this map
        bounds = _get_svg_bounds_for_map(data_map_settings['persistentLevel'])

        # Copy spawning groups data
        allows_global_swaps = 'onlyEventGlobalSwaps' not in data_map_settings['worldSettings']
        spawngroups = copy_spawn_groups(spawndata.groups)

        # Apply world-level random dino class swaps
        map_swaps = data_map_settings['worldSettings'].get('randomNPCClassWeights', [])
        inflate_swap_rules(map_swaps)
        apply_ideal_global_swaps(spawngroups, map_swaps)

        # Apply global swaps if allowed
        apply_ideal_global_swaps(spawngroups, spawndata.global_swaps, only_events=not allows_global_swaps)

        # Generate maps for every species
        for export_class, blueprints in spawndata.species.items():
            untameable = not determine_tamability(spawndata.asb, export_class)

            # The rarity is arbitrarily divided in 6 groups from "very rare" (0) to "very common" (5)
            freqs = calculate_blueprint_freqs(spawngroups, [], blueprints)

            svg = generate_svg_map(bounds, freqs, data_map_spawns, untameable)
            if svg:
                filepath = output_path / self._make_filename_for_export(export_class)
                self.save_raw_file(svg, filepath)

    def _make_filename_for_export(self, blueprint_path):
        clean_bp_name = blueprint_path.rsplit('.')[-1]
        if clean_bp_name.endswith('_C'):
            clean_bp_name = clean_bp_name[:-2]
        clean_bp_name = remove_unicode_control_chars(clean_bp_name)

        modid = self.manager.loader.get_mod_id(blueprint_path)
        if modid:
            clean_bp_name += f'_({modid})'

        return f'Spawning_{clean_bp_name}.svg'


def _get_svg_bounds_for_map(persistent_level: str) -> SVGBoundaries:
    config = get_overrides_for_map(persistent_level, None).svgs
    bounds = SVGBoundaries(
        size=300,
        border_top=config.border_top,
        border_left=config.border_left,
        coord_width=config.border_right - config.border_left,
        coord_height=config.border_bottom - config.border_top,
    )
    return bounds
