from logging import NullHandler, getLogger
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Set, Union

from ark.overrides import SVGGenerationSettings, get_overrides_for_map
from automate.exporter import ExportManager

from .spawn_maps.game_mod import merge_game_mod_groups
from .spawn_maps.species import collect_class_spawning_data, make_species_mapping_from_asb, merge_class_spawning_data
from .spawn_maps.svg import generate_svg_map
from .stage_base import ProcessingStage

logger = getLogger(__name__)
logger.addHandler(NullHandler())

__all__ = [
    'WikiSpawnMapsStage',
]


class WikiSpawnMapsStage(ProcessingStage):
    def get_skip(self) -> bool:
        return False

    def process_core(self, path: Path):
        # Find data of maps with NPC spawns
        root_wiki_dir = Path(self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir)
        map_set: List[Path] = [path.parent for path in root_wiki_dir.glob('*/npc_spawns.json')]

        # Load ASB and spawning group data
        data_asb = self._load_asb(None)
        data_groups = self._load_spawning_groups(None)
        if not data_asb or not data_groups:
            logger.warning(f'Data required by the processor is missing or invalid. Skipping.')
            return

        # Generate mapping table (blueprint path to name)
        species_mapping = make_species_mapping_from_asb(data_asb)

        for map_data_path in map_set:
            self._map_process_data(map_data_path, species_mapping, data_groups)

    def process_mod(self, path: Path, modid: str):
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        mod_type = int(mod_data.get('type', 1))
        if mod_type == 1:
            return self._game_mod_generate_svgs(path, modid)
        elif mod_type == 2:
            return self._map_mod_generate_svgs(path, modid, mod_data['name'])

    def _load_asb(self, modid: Optional[str]):
        path = (self.manager.config.settings.OutputPath / self.manager.config.export_asb.PublishSubDir)
        if modid:
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            path = (path / f'{modid}-{mod_data["name"]}.json')
        else:
            path = (path / 'values.json')
        return self.load_json_file(path)

    def _load_spawning_groups(self, modid: Optional[str]):
        path = (self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir)
        if modid:
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            path = (path / f'{modid}-{mod_data["name"]}/spawngroups.json')
        else:
            path = (path / 'spawngroups.json')
        return self.load_json_file(path)

    def _map_mod_generate_svgs(self, path: Path, modid: str, mod_name: str):
        # Find data of maps with NPC spawns
        root_wiki_mod_dir = Path(self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir /
                                 f'{modid}-{mod_name}')
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

        # Generate mapping table (blueprint path to name)
        species_mapping = make_species_mapping_from_asb(data_asb_mod)

        for map_data_path in map_set:
            self._map_process_data(map_data_path, species_mapping, data_groups_mod, None)

    def _game_mod_generate_svgs(self, path: Path, modid: str):
        # Find data of core maps with NPC spawns
        root_wiki_dir = Path(self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir)
        map_set: List[Path] = [path.parent for path in root_wiki_dir.glob('*/npc_spawns.json')]

        # Load ASB and spawning group data
        data_asb = self._load_asb(modid)
        data_groups_core = self._load_spawning_groups(None)
        data_groups_mod = self._load_spawning_groups(modid)
        if not data_asb or not data_groups_core or not data_groups_mod:
            logger.warning(f'Data required by the processor is missing or invalid. Skipping.')
            return

        # Merge spawning group data
        merge_game_mod_groups(data_groups_core['spawngroups'], data_groups_mod['externalGroupChanges'])

        # Generate mapping table (blueprint path to name)
        species_mapping = make_species_mapping_from_asb(data_asb)

        for map_data_path in map_set:
            self._map_process_data(map_data_path, species_mapping, data_groups_core, data_groups_mod.get('classSwaps', []),
                                   (path / 'spawn_maps'))

    def _map_process_data(self,
                          data_path: Path,
                          species_mapping,
                          spawning_groups,
                          extra_random_class_weights: Optional[List] = None,
                          output_path: Optional[Path] = None):
        map_name = data_path.name
        logger.info(f'Processing data of map: {map_name}')

        # Load exported data
        data_map_settings = self.load_json_file(data_path / 'world_settings.json')
        data_map_spawns = self.load_json_file(data_path / 'npc_spawns.json')
        if not data_map_settings or not data_map_spawns:
            logger.warning(f'Data required by the processor is missing or invalid. Skipping.')
            return

        # Join random class weights if that data has been passed.
        random_class_weights = data_map_settings['worldSettings'].get('randomNPCClassWeights', [])
        if extra_random_class_weights:
            random_class_weights = [*extra_random_class_weights, *random_class_weights]

        # Gather spawning modifiers from NPC class data and random class weights.
        species = collect_class_spawning_data(species_mapping, spawning_groups, random_class_weights)
        species = merge_class_spawning_data(species)

        if not output_path:
            if data_path.name != map_name:
                output_path = (data_path / 'spawn_maps' / map_name)
            else:
                output_path = (data_path / 'spawn_maps')
        else:
            output_path = (output_path / map_name)

        for descriptive_name, modifiers in species.items():
            config: SVGGenerationSettings = get_overrides_for_map(data_map_settings['persistentLevel'], None).svgs

            svg = generate_svg_map(data_map_spawns, spawning_groups, config.border_left, config.border_top,
                                   config.border_right - config.border_left, config.border_bottom - config.border_top,
                                   descriptive_name, modifiers)
            if svg:
                self.save_raw_file(svg, (output_path / f'Spawning {descriptive_name}.svg'))
