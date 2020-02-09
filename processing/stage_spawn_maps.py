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

from .spawn_maps.species import collect_npc_class_spawning_data, make_species_mapping_from_asb
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
            map_name = map_data_path.name
            logger.info(f'Processing data of map: {map_name}')
            # Load exported data
            map_spawns = self.load_json_file(Path(map_data_path) / 'npc_spawns.json')
            map_settings = self.load_json_file(map_data_path / 'world_settings.json')
            # ???
            species = collect_npc_class_spawning_data(species_mapping, map_settings, spawning_groups)

            for bp, bp_data in species.items():
                for species_name in bp_data:
                    map_size = 300
                    point_radius = max(map_size // 150, 2)
                    svg = generate_svg_map(map_spawns, spawning_groups, map_size, 7.2, 7.2, 92.8 - 7.2, 92.8 - 7.2, point_radius,
                                           bp, species_name, bp_data[species_name])
                    if svg:
                        self._save_raw_file(svg, (path / map_name / f'Spawning {species_name}').with_suffix('.svg'))

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
        # TODO: Mods need much more changes to the scripts.
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        if int(mod_data.get('type', 1)) != 2:
            return

        # Find data of maps with NPC spawns
        base_map_output_path = Path(self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir /
                                    f'{modid}-{mod_data["name"]}')
        map_data_dirs: List[Path] = list(base_map_output_path.glob('*/npc_spawns.json'))
        map_data_dirs = [path.parent for path in map_data_dirs]

        # Load ASB and spawning group data
        # TODO: Check if these files fail to load.
        asb_values_core = self.load_exported_json_file(ASBRoot, SpeciesStage, modid=None)
        asb_values_mod = self.load_exported_json_file(ASBRoot, SpeciesStage, modid=modid)
        spawning_groups_core = self.load_exported_json_file(WikiRoot, SpawnGroupStage, modid=None)
        spawning_groups_mod = self.load_exported_json_file(WikiRoot, SpawnGroupStage, modid=modid)
        asb_values_mod['species'] += asb_values_core['species']
        spawning_groups_mod['spawngroups'] += spawning_groups_core['spawngroups']
        # Generate mapping table (blueprint path to name)
        species_mapping = make_species_mapping_from_asb(asb_values_mod)

        for map_data_path in map_data_dirs:
            map_name = map_data_path.name
            logger.info(f'Processing data of map: {map_name}')
            # Load exported data
            map_spawns = self.load_json_file(Path(map_data_path) / 'npc_spawns.json')
            map_settings = self.load_json_file(map_data_path / 'world_settings.json')
            # ???
            species = collect_npc_class_spawning_data(species_mapping, map_settings, spawning_groups_mod)

            for bp, bp_data in species.items():
                for species_name in bp_data:
                    map_size = 300
                    point_radius = max(map_size // 150, 2)
                    svg = generate_svg_map(
                        map_spawns,
                        spawning_groups_mod,
                        map_size,
                        0,
                        0,
                        100,
                        100,  #7.2, 7.2, 92.8 - 7.2, 92.8 - 7.2,
                        point_radius,
                        bp,
                        species_name,
                        bp_data[species_name])
                    if svg:
                        self._save_raw_file(svg, (path / map_name / f'Spawning {species_name}').with_suffix('.svg'))
