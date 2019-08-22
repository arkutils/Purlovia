from functools import lru_cache
from typing import *

from ark.defaults import *

from .asset import ExportTableItem, ImportTableItem, UAsset
from .base import UEBase
from .consts import BLUEPRINT_GENERATED_CLASS_CLS
from .loader import AssetLoader
from .properties import ObjectProperty
from .proxy import UEProxyStructure, proxy_for_type

__all__ = [
    'gather_properties',
    'get_default_props_for_class',
    'discover_inheritance_chain',
    'get_parent_fullname',
    'is_fullname_an_asset',
]

Tproxy = TypeVar('Tproxy', bound=UEProxyStructure)


def gather_properties(export: ExportTableItem) -> Tproxy:
    '''Collect properties from an export, respecting the inheritance tree.'''
    if isinstance(export, ObjectProperty):
        return gather_properties(export.value)

    if not isinstance(export, ExportTableItem):
        raise TypeError("ExportTableItem required")

    chain = discover_inheritance_chain(export)
    proxy = None
    while not proxy and chain:
        baseclass_fullname = chain.pop(0)
        proxy = proxy_for_type(baseclass_fullname)

    if not proxy:
        raise TypeError(f"No proxy type available for {baseclass_fullname}")

    for fullname in chain:
        if not is_fullname_an_asset(fullname):
            continue  # Defaults are already in proxy - skip

        props = get_default_props_for_class(fullname, export.asset.loader)
        proxy.update(props)

    return proxy


def get_default_props_for_class(fullname: str, loader: AssetLoader) -> Mapping[str, Mapping[int, UEBase]]:
    '''Fetch properties for an export.

    This reads the properties directly for bare classes, or finds the appropriate
    Default__ prefixed export for BlueprintGeneratedClasses.'''
    cls = loader.load_class(fullname)

    # Special-case all BP-generated classes - redirect to the Default__ export's properties
    if cls.klass and cls.klass.value.fullname == BLUEPRINT_GENERATED_CLASS_CLS:
        # Check the asset's default_export as this is usually the correct export
        if cls.asset.default_export and cls.asset.default_export.klass and cls.asset.default_export.klass.value is cls:
            return cls.asset.default_export.properties.as_dict()

        # Find the Default__ export for this class and return its properties
        for export in cls.asset.exports:
            if str(export.name).startswith('Default__') and export.klass and export.klass.value is cls:
                return export.properties.as_dict()

        raise RuntimeError("Unable to find Default__ property export for: " + str(cls))

    return cls.properties.as_dict()


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
    klassref = export.klass and export.klass.value

    # Ignore klass if it is /Script/Engine.BlueprintGeneratedClass
    if klassref and klassref.fullname == BLUEPRINT_GENERATED_CLASS_CLS:
        klassref = None

    # Parent can be a (useful) klass or any super
    parentref = klassref or (export.super and export.super.value)

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
