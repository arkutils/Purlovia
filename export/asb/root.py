from pathlib import PurePosixPath
from typing import Optional

from automate.exporter import ExportRoot

from .stage_species import SpeciesStage

__all__ = [
    'ASBRoot',
]


class ASBRoot(ExportRoot):
    def get_name(self) -> str:
        return 'asb'

    def get_relative_path(self) -> PurePosixPath:
        return PurePosixPath(self.manager.config.export_asb.PublishSubDir)

    def get_commit_header(self) -> str:
        return self.manager.config.export_asb.CommitHeader

    def get_name_for_path(self, path: PurePosixPath) -> Optional[str]:
        '''Return a nice name for a file to appear in the commit message.'''
        folder = path.parts[0]

        if folder == 'spawngroups':
            return f"Spawn groups for {path.stem}"

        return None  # will use a generic phrase

    def __init__(self):
        super().__init__()

        self.stages = [
            SpeciesStage(),
        ]
