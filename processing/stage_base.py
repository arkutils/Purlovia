import json
from abc import ABCMeta, abstractmethod, abstractproperty
from logging import NullHandler, getLogger
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Optional, Set, Type

from automate.exporter import ExportManager, ExportRoot, ExportStage
from automate.hierarchy_exporter import JsonHierarchyExportStage
from automate.jsonutils import save_json_if_changed
from automate.version import createExportVersion

logger = getLogger(__name__)
logger.addHandler(NullHandler())

__all__ = [
    'ProcessingStage',
]


class ProcessingStage(ExportStage, metaclass=ABCMeta):
    def initialise(self, manager: ExportManager, root: ExportRoot):
        super().initialise(manager, root)
        self.asb_path = self.manager.config.settings.OutputPath / self.manager.config.export_asb.PublishSubDir
        self.wiki_path = self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir

    def load_json_file(self, path: Path) -> Any:
        try:
            with open(path, 'r') as fp:
                data = json.load(fp)
                return data
        except OSError:
            return None

    def save_raw_file(self, content: Any, path: Path):
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
