from pathlib import Path, PurePosixPath
from typing import Optional

from automate.exporter import ExportRoot
from config import ConfigFile

from .stage_spawngroups import SpawnGroupStage

__all__ = [
    'ExampleRoot',
]


class ExampleRoot(ExportRoot):
    def get_relative_path(self) -> PurePosixPath:
        return PurePosixPath('data/example')
        # return PurePosixPath(self.manager.config.export_asb.PublishSubDir)

    def get_skip(self) -> bool:
        return False
        # return self.manager.config.export_asb.Skip

    def get_commit_header(self) -> str:
        return "Example witty commit message header"
        # return self.manager.config.export_asb.CommitHeader

    def get_name_for_path(self, path: PurePosixPath) -> Optional[str]:
        '''Return a nice name for a file to appear in the commit message.'''
        folder = path.parts[0]

        if folder == 'spawngroups':
            return f"Spawn groups for {path.stem}"

        return None  # will use a generic phrase

    def __init__(self):
        super().__init__()

        self.stages = [
            SpawnGroupStage(),
        ]
