from pathlib import PurePosixPath
from typing import Optional

from automate.exporter import ExportRoot

from .stage_items import ItemsStage
from .stage_maps import MapsStage
from .stage_species import SpeciesStage

__all__ = [
    'SanityRoot',
]


class SanityRoot(ExportRoot):

    def get_name(self) -> str:
        return 'sanity'

    def get_commit_header(self) -> Optional[str]:
        return None

    def get_name_for_path(self, path: PurePosixPath) -> Optional[str]:
        return None  # will use a generic phrase

    def __init__(self):
        super().__init__()

        self.stages = [
            SpeciesStage(),
            ItemsStage(),
            MapsStage(),
        ]
