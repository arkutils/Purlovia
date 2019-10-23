from functools import lru_cache
from logging import NullHandler, getLogger
from operator import attrgetter
from pathlib import Path
from typing import *

import yaml

from config import ConfigFile, get_global_config
from ue.asset import ExportTableItem, ImportTableItem, UAsset
from ue.context import ue_parsing_context
from ue.loader import AssetLoader, AssetLoadException
from utils.tree import IndexedTree, Node

__all__ = [
    'ROOT_NAME',
    'AssetRef',
    'HierarchyError',
    'UnexpectedClass',
    'MissingParent',
    'Hierarchy',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())

ROOT_NAME = '/Script/CoreUObject.Object'


@lru_cache(maxsize=1024)
def _get_parent_cls(export: ExportTableItem) -> Optional[str]:
    return export.super.value.fullname if export.super and export.super.value else None


class AssetRef:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return self.name


class HierarchyError(Exception):
    pass


class UnexpectedClass(HierarchyError):
    pass


class MissingParent(HierarchyError):
    pass


class Hierarchy:
    def __init__(self, loader: AssetLoader, config: ConfigFile = get_global_config()):
        self.tree = IndexedTree[AssetRef](AssetRef(ROOT_NAME), attrgetter('name'))
        self.config = config
        self.extensions = ('.uasset', '.umap')
        self.loader = loader

    def load_internal_hierarchy(self, filename: Path):
        with open(filename, 'rt') as f:
            hierarchy_config = yaml.safe_load(f)

        def walk_config(name, content):
            if isinstance(content, str):
                self.tree.add(name, AssetRef(content))
                return

            for value in content:
                if isinstance(value, str):
                    self.tree.add(name, AssetRef(value))
                elif isinstance(value, dict):
                    key, subvalue = next(iter(value.items()))
                    self.tree.add(name, AssetRef(key))
                    walk_config(key, subvalue)

        walk_config(ROOT_NAME, hierarchy_config[ROOT_NAME])

    def explore_path(self, path: str, exclude: str = None):
        '''Run hierarchy discovery over every matching asset within the given path.'''

        # Use globally configure ignore paths, plus optionally specified path
        excludes = set(self.config.optimisation.SearchIgnore)
        if exclude:
            excludes.add(exclude)

        logger.info('Exploring path: %s', path)

        n = 0

        asset_iterator = self.loader.find_assetnames('.*',
                                                     path,
                                                     exclude=excludes,
                                                     extension=self.extensions,
                                                     return_extension=True)
        for (assetname, ext) in asset_iterator:
            n += 1
            if n % 200 == 0: logger.info(assetname)
            try:
                with ue_parsing_context(properties=False):
                    asset = self.loader[assetname]
            except AssetLoadException:
                logger.warning("Failed to load asset: %s", assetname)
                continue

            try:
                self._ingest_asset(asset)
            except AssetLoadException:
                logger.warning("Failed to check parentage of %s", assetname)

            if ext == '.umap':
                self.loader.cache.remove(assetname)

    def _ingest_asset(self, asset: UAsset):
        if not asset.default_class: return

        current_cls = asset.default_class
        segment: Optional[Node[AssetRef]] = None
        fullname = current_cls.fullname
        assert fullname

        # We may have already covered this while traversing parents
        if fullname in self.tree:
            # logger.warning(f'Trying to add {fullname}, but already present in the tree!')
            return

        while True:
            # Extend unsaved segment
            old_segment = segment
            segment = Node(AssetRef(fullname))
            if old_segment:
                segment.add(old_segment)

            # Get name of parent class
            parent_name = _get_parent_cls(current_cls)
            if not parent_name:
                raise MissingParent(f'Unable to find parent of {fullname}')

            # Is the parent present in the tree?
            anchor_point = self.tree.get(parent_name, None)

            # If we've risen outside /Game but didn't find a match, add it to the root and complain
            if not anchor_point and not parent_name.startswith('/Game'):
                logger.warning(f'Internal class {parent_name} missing from pre-defined hierarchy')
                self.tree.add(ROOT_NAME, AssetRef(parent_name))
                anchor_point = self.tree.get(parent_name, None)

            if anchor_point:
                # Insert segment and finish
                self.tree.insert_segment(parent_name, segment)
                return

            # Load parent class and replace current
            parent_cls = self.loader.load_class(parent_name)
            current_cls = parent_cls
            fullname = current_cls.fullname
            assert fullname
