from pathlib import Path, PurePosixPath
from typing import Optional

from automate.exporter import ExportRoot

from .stage_maps import MapStage
from .stage_spawn_groups import SpawnGroupStage

__all__ = [
    'WikiRoot',
]

class WikiRoot(ExportRoot):
    def get_relative_path(self) -> PurePosixPath:
        return PurePosixPath(self.manager.config.export_wiki.PublishSubDir)

    def get_skip(self) -> bool:
        return self.manager.config.export_wiki.Skip

    def get_commit_header(self) -> str:
        return self.manager.config.export_wiki.CommitHeader

    def get_name_for_path(self, path: PurePosixPath) -> Optional[str]:
        return 'Wiki'

    def __init__(self):
        super().__init__()

        self.stages = [
            MapStage(),
            SpawnGroupStage(),
        ]
