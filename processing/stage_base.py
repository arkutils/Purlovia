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
    @abstractmethod
    def process_core(self, path: Path):
        '''Process data extracted from core.'''
        raise NotImplementedError

    @abstractmethod
    def process_mod(self, path: Path, modid: Optional[str]):
        '''Process data extracted from a mod.'''
        raise NotImplementedError

    def extract_core(self, path: Path):
        self.process_core(path)

    def extract_mod(self, path: Path, modid: str):
        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        path = (path / f'{modid}-{mod_data["name"]}')
        self.process_mod(path, modid)

    def _find_export_root_of_type(self, cls: Type[ExportRoot]) -> Optional[ExportRoot]:
        for export_root in self.manager.roots:
            if isinstance(export_root, cls):
                return export_root

        return None

    def _find_export_stage_of_type(self, root: ExportRoot, cls: Type[ExportStage]) -> Optional[ExportStage]:
        for export_stage in root.stages:
            if isinstance(export_stage, cls):
                return export_stage

        return None

    def load_exported_json_file(self, root_type: Type[ExportRoot], stage_type: Type[ExportStage],
                                modid: Optional[str] = None) -> Any:
        root = self._find_export_root_of_type(root_type)
        assert root
        stage = self._find_export_stage_of_type(root, stage_type)
        assert stage
        path = Path(self.manager.config.settings.OutputPath / root.get_relative_path())

        if isinstance(stage, JsonHierarchyExportStage):
            if not modid:
                path = (path / stage.get_core_file_path())
            else:
                path = (path / stage.get_mod_file_path(modid))
        else:
            raise ValueError('Unable to determine file path - no hierarchy-based stage and no file path.')

        return self.load_json_file(path)

    def load_json_file(self, path: Path) -> Any:
        #path = PurePosixPath(self.manager.config.settings.OutputPath / path)
        with open(path, 'r') as fp:
            data = json.load(fp)
            return data
