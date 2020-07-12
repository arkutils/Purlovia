from pathlib import PurePosixPath
from typing import Optional

from automate.exporter import ExportRoot

from .stage_biome_maps import ProcessBiomeMapsStage
from .stage_spawn_maps import ProcessSpawnMapsStage

__all__ = [
    'WikiMapsRoot',
]


class WikiMapsRoot(ExportRoot):
    def get_name(self) -> str:
        return 'maps'

    def get_relative_path(self) -> PurePosixPath:
        return PurePosixPath('processed/wiki-maps')

    def get_should_commit(self):
        return False  # processing nodes are not committed

    def get_commit_header(self) -> str:
        raise NotImplementedError

    def get_name_for_path(self, path: PurePosixPath) -> Optional[str]:
        raise NotImplementedError

    def __init__(self):
        super().__init__()

        self.stages = [
            ProcessBiomeMapsStage(),
            ProcessSpawnMapsStage(),
        ]
