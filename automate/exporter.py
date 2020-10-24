from __future__ import annotations

from abc import ABCMeta, abstractmethod
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple

from ark.mod import get_core_mods, get_separate_mods
from automate.ark import ArkSteamManager
from config import ConfigFile, get_global_config
from ue.gathering import gather_properties
from ue.hierarchy import find_sub_classes
from ue.loader import AssetLoader, AssetLoadException
from ue.proxy import UEProxyStructure
from utils.log import get_logger

from .git import GitManager
from .manifest import MANIFEST_FILENAME, update_manifest
from .run_sections import should_run_section

logger = get_logger(__name__)

__all__ = [
    'ExportStage',
    'ExportManager',
]


class ExportRoot(metaclass=ABCMeta):
    path: Path
    stages: List[ExportStage]
    manifest: Optional[Dict[str, Any]]
    manager: ExportManager

    @abstractmethod
    def get_name(self) -> str:
        '''Return the primary name of this root (e.g. 'asb').'''
        ...

    def get_relative_path(self) -> PurePosixPath:
        '''Return the relative path of this root (e.g. 'data/asb').'''
        return PurePosixPath(f'data/{self.get_name()}')

    @abstractmethod
    def get_commit_header(self) -> Optional[str]:
        '''Return the header for commit messages in this root.'''
        ...

    @abstractmethod
    def get_name_for_path(self, path: PurePosixPath) -> Optional[str]:
        '''Return a nice name for a path to appear in the commit message (or return None for default).'''
        ...

    def get_should_commit(self) -> bool:
        '''Return true if changes to this root should be committed. Defaults to True.'''
        return True


class ExportStage(metaclass=ABCMeta):
    section_name: str
    manager: ExportManager
    root: ExportRoot

    def initialise(self, manager: ExportManager, root: ExportRoot):
        '''Implementation can override this but should run this super method.'''
        self.root = root
        self.manager = manager

    @abstractmethod
    def get_name(self) -> str:
        '''Return the primary name of this stage (e.g. 'species').'''
        ...

    @abstractmethod
    def extract_core(self, path: Path):
        '''Perform extraction for core (non-mod) data.'''
        ...

    @abstractmethod
    def extract_mod(self, path: Path, modid: str):
        '''Perform extraction for the specified mod.'''
        ...


class ExportManager:
    official_mod_prefixes: Tuple[str, ...]

    def __init__(self, arkman: ArkSteamManager, git: GitManager, config=get_global_config()):
        self.config: ConfigFile = config
        self.arkman: ArkSteamManager = arkman
        self.loader: AssetLoader = arkman.getLoader()
        self.git = git

        self.roots: List[ExportRoot] = []

    def add_root(self, root: ExportRoot) -> ExportRoot:
        '''Add a new export root, to which stages can be added.'''
        self.roots.append(root)
        root.manager = self
        return root

    def perform(self):
        '''Run the defined root/stages structure.'''
        self._perform_export()

    def _get_name_for_stage(self, root: ExportRoot, stage: Optional[ExportStage]) -> str:
        root_name = root.__class__.__name__.replace('Root', '')
        if not stage:
            return root_name
        stage_name = stage.__class__.__name__.replace('Stage', '')
        return f'{root_name}:{stage_name}'

    def _get_mod_name(self, modid: str) -> str:
        moddata = self.arkman.getModData(modid)
        return moddata['title'] if moddata else modid

    def _perform_export(self):
        game_version = self.arkman.getGameVersion()
        base_path = self.config.settings.OutputPath

        modids = get_separate_mods()

        if not game_version:
            raise ValueError("Game not installed or ArkSteamManager not yet initialised")

        logger.info('Export beginning')
        if self.config.settings.SkipExtract:
            logger.info('(all exports skipped due to SkipExtract)')

        # Ensure the output directory exists
        outdir = self.config.settings.OutputPath
        outdir.mkdir(parents=True, exist_ok=True)

        # Prepare roots
        for root in self.roots:
            root.files = []

            # Pre-calculate the real platform-dependant path, creating it if needed
            root.path = Path(self.config.settings.OutputPath / root.get_relative_path())
            root.path.mkdir(parents=True, exist_ok=True)

            root.manager = self
            for stage in root.stages:
                stage.initialise(self, root)
                stage.section_name = f'{root.get_name()}.{stage.get_name()}'

        # Extract : Core : Run each stage of each root
        self.official_mod_prefixes = tuple(f'/Game/Mods/{modid}/' for modid in get_core_mods())
        for root in self.roots:
            root_path = Path(base_path / root.get_relative_path())
            for stage in root.stages:
                if not should_run_section(stage.section_name, self.config.run_sections):
                    continue
                logger.info('Extracting %s in core', self._get_name_for_stage(root, stage))
                stage.extract_core(root_path)
                self._log_stats()

        # Extract : Mods : Run each stage of each root
        for modid in modids:
            for root in self.roots:
                root_path = Path(base_path / root.get_relative_path())
                for stage in root.stages:
                    if not should_run_section(stage.section_name, self.config.run_sections):
                        continue
                    logger.info("Extracting %s in mod %s '%s'", self._get_name_for_stage(root, stage), modid,
                                self._get_mod_name(modid))
                    stage.extract_mod(root_path, modid)
                    self._clear_mod_from_cache(modid)
                    self._log_stats()

        # Finish up : manifests, commit
        for root in self.roots:
            logger.info('Finishing up %s root', self._get_name_for_stage(root, None))

            # Update manifest in this root
            root.manifest = update_manifest(root.path)

            # git after - commit, etc
            if root.get_should_commit():
                self.git.after_exports(root.path.relative_to(outdir), root.get_commit_header(), self._commit_line_for_file)

    def _commit_line_for_file(self, filename: str) -> Optional[str]:
        '''Works out a reasonable single-line commit comment for the given file path.'''
        path = PurePosixPath(self.config.settings.OutputPath / filename)

        # Generic line for removals
        if not Path(path).is_file:
            return f'{path} removed'

        # Don't report manifest file updates
        if path.name.lower() == MANIFEST_FILENAME.lower():
            # Do not report this file
            return False  # type: ignore  # no Literal support in Python 3.7

        # Don't report files in dotted directories
        for dirname in PurePosixPath(filename).parent.parts:
            if dirname.startswith('.') and len(dirname) > 1:
                # Do not report this file
                return False  # type: ignore  # no Literal support in Python 3.7

        # Look up the relevant root
        root = self._find_matching_root(str(path))
        if not root:
            return None  # we don't know this file - fall back to default report

        relative_path = path.relative_to(root.path)

        # See if there's a relevant manifest entry with a version number
        entry = self._find_matching_manifest_entry(root, str(path))
        version: Optional[str] = entry.get('version', None) if entry else None

        # Get the of the path from the root
        name = root.get_name_for_path(relative_path)

        if name and version:
            return f'{name} updated to version {version}'

        if name:
            return f'{name} updated'

        if version:
            return f'{relative_path} updated to version {version}'

        # Don't know this file
        return None

    def _find_matching_root(self, path: str) -> Optional[ExportRoot]:
        '''Look for a root that owns the given file path, which can be deep within the root.'''
        # We use Unix-style paths on both sides and just compare using startswith
        path = str(PurePosixPath(path))

        for root in self.roots:
            root_path_str = str(PurePosixPath(root.path))
            if path.startswith(root_path_str):
                return root

        return None

    def _find_matching_manifest_entry(self, root: ExportRoot, filename: str) -> Optional[Dict[str, Any]]:
        '''Look for a manifest entry matching the given file path within the root.'''
        filepath = PurePosixPath(filename).relative_to(root.path)  # throws if filename is not in the root
        assert root.manifest
        files = root.manifest.get('files', None)
        if not files:
            return None
        return files.get(str(PurePosixPath(filepath)), None)

    def _clear_mod_from_cache(self, modid: str):
        # Remove assets with this mod's prefix from the cache
        modname = self.loader.get_mod_name('/Game/Mods/' + modid)
        assert modname
        prefix = '/Game/Mods/' + modname
        self.loader.wipe_cache_with_prefix(prefix)

    def _log_stats(self):
        max_mem = self.loader.max_memory / 1024.0 / 1024.0
        logger.debug("Stats: max mem = %6.2f Mb, max cache entries = %d", max_mem, self.loader.max_cache)

    def iterate_core_exports_of_type(self, type_name: str, sort=True, filter=None) -> Iterator[UEProxyStructure]:
        '''
        Yields a ready-to-use proxy for each class that inherits from `type_name` and exists in the core+DLC of the game.
        Classes that have a 'Default__' counterpart are excluded from the output.
        By default the results are sorted by class fullname.
        '''
        # Gather classes of this type in the core
        # (core path prefixes were pre-calculated earlier)
        classes: Set[str] = set()
        for cls_name in find_sub_classes(type_name):
            if filter and not filter(cls_name):
                continue

            if not cls_name.startswith('/Game'):
                continue

            if cls_name.startswith('/Game/Mods'):
                if not any(cls_name.startswith(prefix) for prefix in self.official_mod_prefixes):
                    continue

            classes.add(cls_name)

        # The rest of the work is shared
        yield from self._iterate_exports(classes, sort)

    def iterate_mod_exports_of_type(self, type_name: str, modid: str, sort=True, filter=None) -> Iterator[UEProxyStructure]:
        '''
        Yields a ready-to-use proxy for each class that inherits from `type_name` and exists in the specified mod.
        Classes that have a 'Default__' counterpart are excluded from the output.
        By default the results are sorted by class fullname.
        '''
        # Work out the base path for this mod
        mod_path = self.loader.clean_asset_name(f'/Game/Mods/{modid}') + '/'

        # Gather classes of this type in the mod
        classes: Set[str] = set()
        for cls_name in find_sub_classes(type_name):
            if filter and not filter(cls_name):
                continue

            if not cls_name.startswith(mod_path):
                continue

            classes.add(cls_name)

        # The rest of the work is shared
        yield from self._iterate_exports(classes, sort)

    def _iterate_exports(self, classes: Set[str], sort: bool) -> Iterator[UEProxyStructure]:
        # Exclude classes that have a Default__ counterpart
        to_remove = []
        for cls_name in classes:
            if '.Default__' in cls_name:
                to_remove.append(cls_name.replace('Default__', ''))

        classes -= set(to_remove)

        # Sort them to help with consistent outputs, if requested
        output_order = sorted(classes) if sort else classes

        # Load and output each one
        for cls_name in output_order:
            try:
                export = self.loader.load_class(cls_name)
            except AssetLoadException:
                logger.warning('Failed to load asset during export: %s', cls_name)
                continue

            try:
                proxy: UEProxyStructure = gather_properties(export)
            except Exception:  # pylint: disable=broad-except
                logger.warning('Failed to gather properties from asset: %s', cls_name)
                continue

            yield proxy

    def get_mod_version(self, modid: str) -> str:
        return self.arkman.getModData(modid)['version']  # type: ignore
