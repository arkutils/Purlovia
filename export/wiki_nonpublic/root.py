from pathlib import PurePosixPath
from typing import Optional

from automate.exporter import ExportRoot

from .stage_explorer_notes import ExplorerNotesStage

__all__ = [
    'WikiNonPublicRoot',
]


class WikiNonPublicRoot(ExportRoot):
    def get_name(self) -> str:
        return 'wiki_nonpublic'

    def get_relative_path(self) -> PurePosixPath:
        return PurePosixPath(f'{self.manager.config.export_wiki.PublishSubDir}_local')

    def get_should_commit(self):
        return False  # processing nodes are not committed

    def get_commit_header(self) -> str:
        raise NotImplementedError

    def get_name_for_path(self, _: PurePosixPath) -> Optional[str]:
        raise NotImplementedError

    def __init__(self):
        super().__init__()

        self.stages = [
            ExplorerNotesStage(),
        ]
