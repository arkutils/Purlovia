from functools import lru_cache
from typing import List, Optional

from .asset import ExportTableItem, ImportTableItem
from .consts import BLUEPRINT_GENERATED_CLASS_CLS
from .loader import AssetLoader

__all__ = [
    'discover_inheritance_chain',
    'get_parent_fullname',
    'is_fullname_an_asset',
]


def inherits_from(export: ExportTableItem, klass_name: str) -> bool:
    '''Return true if klass_name appears in the inheritance tree for the given export.'''
    # TODO: Optimise: Cancel early if found and cache at all levels
    found = klass_name in discover_inheritance_chain(export)
    return found


def discover_inheritance_chain(export: ExportTableItem, reverse=False) -> List[str]:
    '''Return a list representing the inheritance chain of this export,
    ordered with the most distant descandants first by default.'''
    assert export and export.asset and export.asset.loader and export.fullname

    chain: List[str] = list()
    loader: AssetLoader = export.asset.loader
    current: ExportTableItem = export

    chain.append(export.fullname)

    while True:
        # Find the full name of our parent
        parent_fullname = get_parent_fullname(current)
        if not parent_fullname:
            break

        # Record it
        chain.append(parent_fullname)

        # Stop if we hit the top
        if not is_fullname_an_asset(parent_fullname):
            break

        # Load this asset and continue up the chain
        current = loader.load_class(parent_fullname)

    if not reverse:
        chain.reverse()

    return chain


@lru_cache(maxsize=1024)
def get_parent_fullname(export: ExportTableItem) -> Optional[str]:
    '''Calculate the parent class of the given export.'''
    klass_ref = export.klass and export.klass.value

    # Ignore klass if it is /Script/Engine.BlueprintGeneratedClass
    if klass_ref and klass_ref.fullname == BLUEPRINT_GENERATED_CLASS_CLS:
        klass_ref = None

    # Parent can be a (useful) klass or any super
    parentref = klass_ref or (export.super and export.super.value)

    # Reached the top of the tree?
    if not parentref:
        return None

    # Figure out what's above us in the tree
    if isinstance(parentref, ImportTableItem):
        # An import - maybe load it
        parent_fullname = parentref.fullname
        if not is_fullname_an_asset(parent_fullname):
            return parent_fullname  # nowhere else to go

        parent = export.asset.loader.load_class(parent_fullname)
    elif isinstance(parentref, ExportTableItem):
        # An export - simply follow it
        parent = parentref
    else:
        raise TypeError(f"Can't handle parent {parentref} of type {type(parentref)}")

    return parent.fullname


def is_fullname_an_asset(fullname: str):
    return fullname.startswith('/Game')
