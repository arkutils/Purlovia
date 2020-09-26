from pathlib import Path

from automate.exporter import ExportStage
from utils.log import get_logger

__all__ = [
    'TradesStage',
]

logger = get_logger(__name__)


# TODO: Delete once safe.
class TradesStage(ExportStage):
    def get_name(self) -> str:
        return 'trades'

    def extract_core(self, path: Path):
        filepath = Path(path / 'trades.json')
        if filepath.is_file():
            filepath.unlink()

    def extract_mod(self, path: Path, modid: str):
        ...
