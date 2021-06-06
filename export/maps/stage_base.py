import json
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from automate.exporter import ExportManager, ExportRoot, ExportStage
from utils.log import get_logger

logger = get_logger(__name__)

__all__ = [
    'ProcessingStage',
]


class ModType(Enum):
    GameMod = 1
    CustomMap = 2
    IslandExtension = 3


class ProcessingStage(ExportStage, metaclass=ABCMeta):  # pylint: disable=abstract-method
    asb_path: Path
    wiki_path: Path
    output_path: Path

    def initialise(self, manager: ExportManager, root: ExportRoot):
        super().initialise(manager, root)

        self.output_path = self.manager.config.settings.OutputPath / self.root.get_relative_path()
        self.asb_path = self.manager.config.settings.OutputPath / self.manager.config.export_asb.PublishSubDir
        self.wiki_path = self.manager.config.settings.OutputPath / self.manager.config.export_wiki.PublishSubDir

    def get_mod_subroot_name(self, modid: str) -> str:
        if modid in self.manager.config.settings.SeparateOfficialMods:
            return f'{modid}-{modid}'

        mod_data = self.manager.arkman.getModData(modid)
        assert mod_data
        return f'{modid}-{mod_data["name"]}'

    def load_json_file(self, path: Path) -> Any:
        '''Attempts to load a JSON file. Returns None on error.'''
        try:
            with open(path, 'rt', encoding='utf-8') as fp:
                data = json.load(fp)
                return data
        except OSError:
            return None

    def load_wiki_file(self, modid: Optional[str], name: str):
        path = self.wiki_path
        if modid:
            path /= self.get_mod_subroot_name(modid)
        return self.load_json_file(path / f'{name}.json')

    def save_raw_file(self, content: str, path: Path):
        '''Writes a string to a UTF-8 encoded file.'''
        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wt', newline='\n', encoding='utf-8') as f:
            f.write(content)

    def find_maps(self, modid: Optional[str], keyword='world_settings', include_official_mods=False) -> List[Tuple[str, Path]]:
        '''Returns a list of maps in specific path of the output directory.'''
        path_to_query = self.wiki_path
        if modid:
            path_to_query /= self.get_mod_subroot_name(modid)

        out = [(path.parent.name, path.parent.relative_to(self.wiki_path)) for path in path_to_query.glob(f'*/{keyword}.json')]

        if include_official_mods:
            for official_mod in self.manager.config.settings.SeparateOfficialMods:
                out += self.find_maps(official_mod, keyword=keyword, include_official_mods=False)

        return out

    def find_official_maps(self, only_core=False, keyword='world_settings') -> List[Tuple[str, Path]]:
        '''Returns a list of official maps in the output directory.'''
        results = self.find_maps(None, keyword)

        if not only_core:
            for separate_id in self.manager.config.settings.SeparateOfficialMods:
                results += self.find_maps(separate_id, keyword)

        return results


class JsonProcessingStage(ProcessingStage, metaclass=ABCMeta):
    @abstractmethod
    def get_files_to_load(self, modid: Optional[str]) -> List[str]:
        raise NotImplementedError()

    def get_extra_dependencies(self, modid: Optional[str]) -> List[Optional[str]]:
        if modid:
            return [None, 'CrystalIsles']
        return []

    def requires_maps(self) -> Optional[List[str]]:
        return None

    @abstractmethod
    def process(self, base_path: Path, modid: Optional[str], modtype: Optional[ModType], data: Dict[str, List[Any]]):
        raise NotImplementedError()

    def extract_core(self, path: Path):
        self._load_data_and_process(path, None)

    def extract_mod(self, path: Path, modid: str):
        self._load_data_and_process(path, modid)

    def _load_data_and_process(self, path: Path, modid: Optional[str]):
        needed_files = self.get_files_to_load(modid)
        loaded_files = defaultdict(list)

        # Load all required files from the mod and its dependencies
        for depid in [modid] + self.get_extra_dependencies(modid):
            for filename in needed_files:
                # Construct a path to the file
                if depid:
                    filepath = (self.wiki_path / self.get_mod_subroot_name(depid) / filename).with_suffix('.json')
                else:
                    filepath = (self.wiki_path / filename).with_suffix('.json')

                # Load data
                filedata = self.load_json_file(filepath)
                loaded_files[filename].append(filedata)

        # Add mod subroot tag to the path
        if modid:
            path /= self.get_mod_subroot_name(modid)
        else:
            path /= 'core'

        # Get mod type
        modtype = None
        if modid:
            moddata = self.manager.arkman.getModData(modid)
            assert moddata
            modtype = ModType(int(moddata.get('type', 1)))

        # Do the processing
        self.process(path, modid, modtype, loaded_files)
