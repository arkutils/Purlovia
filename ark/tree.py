from typing import *
from functools import lru_cache
from collections import deque

from ue.asset import UAsset
from .asset import findParentPackages

__all__ = [
    'inherits_from',
    'walk_parents',
]


@lru_cache(maxsize=512)
def inherits_from(asset: UAsset, targetname: str):
    '''Check if the asset inherits from the given package.'''
    return walk_parents(asset, lambda parentname: True if parentname == targetname else None)


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

        if assetname.startswith('/Script') or assetname.startswith('/Engine'):
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
