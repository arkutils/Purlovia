from pathlib import Path, PurePosixPath
from typing import Optional

from automate.exporter import ExportRoot
from processing.stage_biome_maps import ProcessBiomeMapsStage
from processing.stage_spawn_maps import ProcessSpawnMapsStage

from .stage_drops import DropsStage
from .stage_engrams import EngramsStage
from .stage_items import ItemsStage
from .stage_loot_crates import LootCratesStage
from .stage_maps import MapStage
from .stage_missions import MissionsStage
from .stage_spawn_groups import SpawnGroupStage
from .stage_species import SpeciesStage
from .stage_trades import TradesStage

__all__ = [
    'WikiRoot',
]


class WikiRoot(ExportRoot):
    def get_name(self) -> str:
        return 'wiki'

    def get_relative_path(self) -> PurePosixPath:
        return PurePosixPath(self.manager.config.export_wiki.PublishSubDir)

    def get_commit_header(self) -> str:
        return self.manager.config.export_wiki.CommitHeader

    def get_name_for_path(self, path: PurePosixPath) -> Optional[str]:
        return None

    def __init__(self):
        super().__init__()

        self.stages = [
            MapStage(),
            SpawnGroupStage(),
            EngramsStage(),
            ItemsStage(),
            DropsStage(),
            LootCratesStage(),
            SpeciesStage(),
            TradesStage(),
            MissionsStage(),

            # The following are processing stages, depending on the output of previous stages
            # TODO: Allow these to move to their own root
            ProcessBiomeMapsStage(),
            ProcessSpawnMapsStage(),
        ]
