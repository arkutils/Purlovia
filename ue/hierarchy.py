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
from ue.tree import get_parent_fullname
from utils.tree import IndexedTree, Node

from .consts import BLUEPRINT_GENERATED_CLASS_CLS

__all__ = [
    'ROOT_NAME',
    'HierarchyError',
    'UnexpectedClass',
    'MissingParent',
    'inherits_from',
    'find_sub_classes',
    'find_parent_classes',
    'load_internal_hierarchy',
    'explore_path',
    'iterate_all',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())

ROOT_NAME = '/Script/CoreUObject.Object'


@lru_cache(maxsize=1024)
def _get_parent_cls(export: ExportTableItem) -> Optional[str]:
    src = export.klass.value
    if src.fullname == BLUEPRINT_GENERATED_CLASS_CLS:
        src = export.super.value
    return src.fullname if src else None


class HierarchyError(Exception):
    pass


class UnexpectedClass(HierarchyError):
    pass


class MissingParent(HierarchyError):
    pass


tree: IndexedTree[str] = IndexedTree[str](ROOT_NAME)
asset_extensions = ('.uasset', '.umap')


def inherits_from(klass: Union[str, ExportTableItem], target: str, safe=False, include_self=False) -> bool:
    '''
    Check if a class inherits from another.
    `klass` should be a full classname or an exported class.
    `target` should be a full classname.
    `safe` as True will return False when encountering a HierarchyError.
    `include_self` to allow the case where the two inputs are equivalent.
    '''
    if safe:
        try:
            return target in find_parent_classes(klass, include_self=include_self)
        except HierarchyError:
            return False
    else:
        return target in find_parent_classes(klass, include_self=include_self)


def find_sub_classes(klass: Union[str, ExportTableItem]) -> Iterator[str]:
    '''
    Iterate over all sub-classes of the given class.
    `klass` should be a full classname or an exported class.
    '''
    if isinstance(klass, str):
        name = klass
    elif isinstance(klass, ExportTableItem):
        assert klass.fullname
        name = klass.fullname
    else:
        raise TypeError('Invalid argument')

    node = tree.get(name, None)
    if not node:
        raise ValueError(f'Node f{name} not found')

    yield from (node.data for node in node.walk_iterator(skip_self=True))


def find_parent_classes(klass: Union[str, ExportTableItem], *, include_self=False) -> Iterator[str]:
    '''
    Iterate over an export's parent classes.
    `klass` should be a full classname or an exported class.

    Note that if the supplied `klass` is not an asset's main class it must be
    supplied as an ExportTableItem to allow discovery of intermediate hierarchy.
    '''
    export: Optional[ExportTableItem] = None

    if isinstance(klass, str):
        name = klass
    elif isinstance(klass, ExportTableItem):
        assert klass.fullname
        name = klass.fullname
        export = klass
    else:
        raise TypeError('Invalid argument')

    node = tree.get(name, None)
    if not node and not export:
        raise ValueError(f'Cannot find {name} in the hierarchy and no export supplied to scan from')

    if include_self:
        yield name

    # Phase 1: step through non-primary parent classes until we find a matching node in the tree
    while export and not node:
        parent_name = get_parent_fullname(export)
        if not parent_name:
            raise MissingParent(f'Unable to find useful parent for {export.fullname}')

        yield parent_name

        node = tree.get(parent_name, None)
        if not node and not parent_name.startswith('/Game'):
            raise MissingParent(f'Unable to find parent for {parent_name}')
        if not node:
            export = export.asset.loader.load_class(parent_name)

    # Phase 2: simply step up through our own hierarchy
    while node.parent:
        parent = node.parent
        yield parent.data
        node = parent


def iterate_all() -> Iterator[str]:
    yield from tree.keys()


NO_DEFAULT = object()


def _node_from_argument(klass: Union[str, ExportTableItem], default=NO_DEFAULT) -> Node[str]:
    if isinstance(klass, str):
        name = klass
    elif isinstance(klass, ExportTableItem):
        assert klass.fullname
        name = klass.fullname
    else:
        raise TypeError('Invalid argument')

    node = tree.get(name, None)
    if not node and default is NO_DEFAULT:
        raise ValueError(f'Node f{name} not found')

    return node


def load_internal_hierarchy(filename: Path):
    '''
    Pre-load hierarchy with 'internal' type data that cannot otherwise be discovered.
    `filename` should be a yaml file with a top-level key matching the root name.
    '''
    logger.info('Loading internal UE hierarchy from: %s', filename)
    with open(filename, 'rt') as f:
        hierarchy_config = yaml.safe_load(f)

    def walk_hierarchy_yaml(name, content):
        if isinstance(content, str):
            tree.add(name, content)
            return

        for value in content:
            if isinstance(value, str):
                tree.add(name, value)
            elif isinstance(value, dict):
                key, subvalue = next(iter(value.items()))
                tree.add(name, key)
                walk_hierarchy_yaml(key, subvalue)

    walk_hierarchy_yaml(ROOT_NAME, hierarchy_config[ROOT_NAME])


# export_path('...', loader, config.optimisation.SearchIgnore)


def explore_path(path: str, loader: AssetLoader, excludes: Iterable[str], verbose=False):
    '''Run hierarchy discovery over every matching asset within the given path.'''
    excludes = set(excludes)

    logger.info('Discovering hierarchy in path: %s', path)

    n = 0

    with ue_parsing_context(properties=False):
        asset_iterator = loader.find_assetnames('.*', path, exclude=excludes, extension=asset_extensions, return_extension=True)
        for (assetname, ext) in asset_iterator:
            n += 1
            if verbose and n % 200 == 0: logger.info(assetname)

            try:
                asset = loader[assetname]
            except AssetLoadException:
                logger.warning("Failed to load asset: %s", assetname)
                continue

            try:
                _ingest_asset(asset, loader, ext)
            except AssetLoadException:
                logger.warning("Failed to check parentage of %s", assetname)
            except MissingParent as ex:
                logger.exception("Missing parent for %s", assetname)
                raise MissingParent from ex

            # Remove maps from the cache immediately as they are large and cannot be inherited from
            if ext == '.umap':
                loader.cache.remove(assetname)


def _find_exports_to_store(asset: UAsset, ext: str) -> Iterator[ExportTableItem]:
    current_cls = asset.default_class or asset.default_export
    if current_cls:
        yield current_cls

    if ext == '.umap':
        for export in asset.exports:
            if export.klass.value and export.klass.value.fullname in ('/Script/Engine.World', '/Script/Engine.LevelScriptActor'):
                yield export


def _ingest_asset(asset: UAsset, loader: AssetLoader, ext: str):
    for export in _find_exports_to_store(asset, ext):
        _ingest_export(export, loader)


def _ingest_export(export: ExportTableItem, loader: AssetLoader):
    current_cls: ExportTableItem = export

    segment: Optional[Node[str]] = None
    fullname = current_cls.fullname
    assert fullname

    # We may have already covered this while traversing parents
    if fullname in tree:
        return

    while True:
        # Extend unsaved segment
        old_segment = segment
        segment = Node(fullname)
        if old_segment:
            segment.add(old_segment)

        # Get name of parent class
        parent_name = _get_parent_cls(current_cls)
        if not parent_name:
            raise MissingParent(f'Unable to find parent of {fullname}')

        # Is the parent present in the tree?
        anchor_point = tree.get(parent_name, None)

        # If we've risen outside /Game but didn't find a match, add it to the root and complain
        if not anchor_point and not parent_name.startswith('/Game'):
            logger.debug(f'Internal class {parent_name} missing from pre-defined hierarchy')
            tree.add(ROOT_NAME, parent_name)
            anchor_point = tree.get(parent_name, None)

        if anchor_point:
            # Insert segment and finish
            tree.insert_segment(parent_name, segment)
            return

        # Load parent class and replace current
        parent_cls = loader.load_class(parent_name)
        current_cls = parent_cls
        fullname = current_cls.fullname
        assert fullname
