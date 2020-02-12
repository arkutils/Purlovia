from pathlib import Path, PurePosixPath
from typing import Optional

from automate.exporter import ExportRoot
from config import ConfigFile

from .stage_region_maps import WikiRegionMapsStage
from .stage_spawn_maps import WikiSpawnMapsStage

__all__ = [
    'ProcessingRoot',
]


class ProcessingRoot(ExportRoot):
    def get_relative_path(self) -> PurePosixPath:
        return PurePosixPath('data/processed')

    def get_skip(self) -> bool:
        return False

    def get_commit_header(self) -> str:
        return 'COMMIT HEADER'

    def get_name_for_path(self, path: PurePosixPath) -> Optional[str]:
        '''Return a nice name for a file to appear in the commit message.'''
        #folder = path.parts[0]

        #if folder == 'spawngroups':
        #    return f"Spawn groups for {path.stem}"

        return None  # will use a generic phrase

    def __init__(self):
        super().__init__()

        self.stages = [
            WikiSpawnMapsStage(),
            WikiRegionMapsStage(),
        ]
