from typing import *
from functools import lru_cache
from collections import deque

from ue.asset import UAsset, ExportTableItem, ImportTableItem
from .asset import findParentPackages

__all__ = [
    'get_parent_of_export',
    'export_inherits_from',
    'inherits_from',
    'walk_parents',
]


@lru_cache(maxsize=1024)
def get_parent_of_export(export: ExportTableItem) -> Optional[ExportTableItem]:
    '''Return the parent of the given export. This will be an export, possibly from a different asset.'''
    klassref = export.klass and export.klass.value

    # Ignore klass if it is a built-in type
    if klassref and isinstance(klassref, ImportTableItem) and klassref.namespace and klassref.namespace.value:
        if not str(klassref.namespace.value.name).startswith('/Game'):
            klassref = None

    # Parent can be a (useful) klass or any super
    parentref = klassref or (export.super and export.super.value)

    # Reached the top of the tree?
    if not parentref:
        return None

    # Figure out what's above us in the tree
    if isinstance(parentref, ImportTableItem):
        # An import - maybe load it
        if not str(parentref.namespace.value.name).startswith('/Game'):
            return None  # nowhere else to go
        parent_asset: UAsset = export.asset.loader.load_related(parentref)
        parent: Optional[ExportTableItem] = parent_asset.default_export
        if not parent:
            return None
    elif isinstance(parentref, ExportTableItem):
        # An export - simply follow it
        parent = parentref
    else:
        raise TypeError(f"Can't handle parent {parentref} of type {type(parentref)}")

    return parent


@lru_cache(maxsize=1024)
def export_inherits_from(export: ExportTableItem, target: ExportTableItem) -> bool:
    '''Test if the given export has the target export in its inheritance tree.'''
    assert isinstance(export, ExportTableItem)
    assert isinstance(target, ExportTableItem)
    assert export.fullname is not None and target.fullname is not None

    # Found our target?
    if export.fullname == target.fullname:
        return True

    # Figure out where to go next, up the tree
    parent = get_parent_of_export(export)
    if not parent:
        return False

    # Recurse up to the parent
    return export_inherits_from(parent, target)


@lru_cache(maxsize=512)
def inherits_from(asset: UAsset, targetname: str) -> bool:
    '''Check if the asset inherits from the given package.'''
    return walk_parents(asset, lambda parentname: True if parentname == targetname else None) or False


def walk_parents(asset: UAsset, fn: Callable[[str], Optional[Any]]) -> Optional[Any]:
    '''Walk up the inheritance hierarchy, calling the supplied function for each node.

    To terminate the walk early return anything other than None from the supplied function.

    :returns: The result of the early termination, or None otherwise.
    '''
    assert asset.loader and asset.assetname
    loader = asset.loader
    queue: Deque[str] = deque()
    queue.append(asset.assetname)
    done: Set[str] = set()

    while queue:
        assetname = queue.popleft()
        if assetname in done:
            continue

        if not assetname.startswith('/Game'):
            continue

        asset = loader[assetname]

        for parentname in findParentPackages(asset):
            # Allow the function to look at the
            result = fn(parentname)
            if result is not None:
                return result  # bail early with the given result

            # Queue up the parents for continued "recursion"
            queue.append(parentname)

        done.add(assetname)

    return None
