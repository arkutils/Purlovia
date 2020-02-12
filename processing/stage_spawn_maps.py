from logging import NullHandler, getLogger
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Set, Union

from automate.exporter import ExportManager, ExportRoot
from automate.jsonutils import save_json_if_changed
from export.asb.root import ASBRoot
from export.asb.stage_species import SpeciesStage
from export.wiki.root import WikiRoot
from export.wiki.stage_maps import MapStage
from export.wiki.stage_spawn_groups import SpawnGroupStage

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
        base_map_output_path = Path(self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir)
        map_data_dirs: List[Path] = list(base_map_output_path.glob('*/npc_spawns.json'))
        map_data_dirs = [path.parent for path in map_data_dirs]

        # Load ASB and spawning group data
        # TODO: Check if these files fail to load.
        asb_values = self.load_exported_json_file(ASBRoot, SpeciesStage, modid=None)
        spawning_groups = self.load_exported_json_file(WikiRoot, SpawnGroupStage, modid=None)
        # Generate mapping table (blueprint path to name)
        species_mapping = make_species_mapping_from_asb(asb_values)

        for map_data_path in map_data_dirs:
            self._map_process_data(path, map_data_path, species_mapping, spawning_groups, None)

    def _map_mod_generate_svgs(self, path: Path, modid: str, mod_name: str):
        # Find data of maps with NPC spawns
        base_map_output_path = Path(self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir /
                                    f'{modid}-{mod_name}')
        map_data_dirs: List[Path] = list(base_map_output_path.glob('*/npc_spawns.json'))
        map_data_dirs = [path.parent for path in map_data_dirs]

        # TODO: Check if these files fail to load.
        # Load and merge ASB data
        asb_values_core = self.load_exported_json_file(ASBRoot, SpeciesStage, modid=None)
        asb_values_mod = self.load_exported_json_file(ASBRoot, SpeciesStage, modid=modid)
        asb_values_mod['species'] += asb_values_core['species']
        # Load and merge spawning group data
        spawning_groups_core = self.load_exported_json_file(WikiRoot, SpawnGroupStage, modid=None)
        spawning_groups_mod = self.load_exported_json_file(WikiRoot, SpawnGroupStage, modid=modid)
        spawning_groups_mod['spawngroups'] += spawning_groups_core['spawngroups']
        # Generate mapping table (blueprint path to name)
        species_mapping = make_species_mapping_from_asb(asb_values_mod)

        for map_data_path in map_data_dirs:
            self._map_process_data(path, map_data_path, species_mapping, spawning_groups_mod, None)

    def process_mod(self, path: Path, modid: str):
        # TODO: Mods need much more changes to the scripts.
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        mod_type = int(mod_data.get('type', 1))
        if mod_type == 1:
            return self._game_mod_generate_svgs(path, modid)
        elif mod_type == 2:
            return self._map_mod_generate_svgs(path, modid, mod_data['name'])

    def _map_process_data(self, path: Path, data_path: Path, species_mapping, spawning_groups,
                          extra_random_class_weights: Optional[List]):
        map_name = data_path.name
        logger.info(f'Processing data of map: {map_name}')
        # Load exported data
        map_settings = self.load_json_file(data_path / 'world_settings.json')
        map_spawns = self.load_json_file(data_path / 'npc_spawns.json')
        # Gather spawning modifiers from NPC class data and random class weights.
        random_class_weights = map_settings['worldSettings'].get('randomNPCClassWeights', [])
        if extra_random_class_weights:
            random_class_weights = [*extra_random_class_weights, *random_class_weights]
        species = collect_class_spawning_data(species_mapping, spawning_groups, random_class_weights)
        species = merge_class_spawning_data(species)

        for descriptive_name, modifiers in species.items():
            svg = generate_svg_map(map_spawns, spawning_groups, 7.2, 7.2, 92.8 - 7.2, 92.8 - 7.2, descriptive_name, modifiers)
            if svg:
                self._save_raw_file(svg, (path / map_name / f'Spawning {descriptive_name}').with_suffix('.svg'))

    def _save_raw_file(self, content: Any, path: Path):
        parent = Path(path).parent
        parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as fp:
            fp.write(content)

    def _game_mod_generate_svgs(self, path: Path, modid: str):
        # TODO: Mods need much more changes to the scripts.
        # Find data of maps with NPC spawns
        base_map_output_path = Path(self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir)
        map_data_dirs: List[Path] = list(base_map_output_path.glob('*/npc_spawns.json'))
        map_data_dirs = [path.parent for path in map_data_dirs]

        # TODO: Check if these files fail to load.
        # Load ASB data
        asb_values_mod = self.load_exported_json_file(ASBRoot, SpeciesStage, modid=modid)
        # Load and merge spawning group data
        spawning_groups_core = self.load_exported_json_file(WikiRoot, SpawnGroupStage, modid=None)
        spawning_groups_mod = self.load_exported_json_file(WikiRoot, SpawnGroupStage, modid=modid)
        merge_game_mod_groups(spawning_groups_core['spawngroups'], spawning_groups_mod['externalGroupChanges'])
        # Generate mapping table (blueprint path to name)
        species_mapping = make_species_mapping_from_asb(asb_values_mod)

        for map_data_path in map_data_dirs:
            self._map_process_data(path, map_data_path, species_mapping, spawning_groups_core,
                                   spawning_groups_mod.get('classSwaps', []))
