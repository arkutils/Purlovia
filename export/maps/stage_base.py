import json
from abc import ABCMeta
from pathlib import Path
from typing import Any

from automate.exporter import ExportManager, ExportRoot, ExportStage
from utils.log import get_logger

logger = get_logger(__name__)

__all__ = [
    'ProcessingStage',
]


class ProcessingStage(ExportStage, metaclass=ABCMeta):  # pylint: disable=abstract-method
    asb_path: Path
    wiki_path: Path
    output_path: Path

    def initialise(self, manager: ExportManager, root: ExportRoot):
        super().initialise(manager, root)

        self.output_path = self.manager.config.settings.OutputPath / self.root.get_relative_path()
        self.asb_path = self.manager.config.settings.OutputPath / self.manager.config.export_asb.PublishSubDir
        self.wiki_path = self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir

    def load_json_file(self, path: Path) -> Any:
        try:
            with open(path, 'rt', encoding='utf-8') as fp:
                data = json.load(fp)
                return data
        except OSError:
            return None

    def save_raw_file(self, content: Any, path: Path):
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wt', newline='\n', encoding='utf-8') as f:
            f.write(content)
