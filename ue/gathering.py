from typing import *

from ark.defaults import *

from .asset import ExportTableItem, ImportTableItem, UAsset
from .base import UEBase
from .loader import AssetLoader
from .properties import ObjectProperty
from .proxy import proxy_for_type


def gather_properties(export: ExportTableItem):
    if isinstance(export, ObjectProperty):
        return gather_properties(export.value)

    if not isinstance(export, ExportTableItem):
        raise TypeError("ExportTableItem required")

    chain = _discover_inheritance_chain(export)
    baseclass_fullname = chain.pop(0)
    proxy = proxy_for_type(baseclass_fullname)

    if not proxy:
        raise TypeError(f"No proxy type available for {baseclass_fullname}")

    for fullname in chain:
        if fullname.startswith('/Script'):
            continue  # Defaults are already in proxy - skip

        props = _get_props_for_class(fullname, export.asset.loader)
        proxy.update(props)

    return proxy


def _get_props_for_class(fullname: str, loader: AssetLoader) -> Mapping[str, Mapping[int, UEBase]]:
    cls = loader.load_class(fullname)
    asset = cls.asset

    # Find the Default__ export for this class and return its properties
    for export in asset.exports:
        if str(export.name).startswith('Default__') and str(export.klass) == str(cls):
            return export.properties.as_dict()

    return {}


def _discover_inheritance_chain(export: ExportTableItem) -> List[str]:
    assert export and export.asset and export.asset.loader and export.fullname

    chain: List[str] = list()
    loader: AssetLoader = export.asset.loader
    current: ExportTableItem = export

    chain.append(export.fullname)

    while True:
        # Find the full name of our parent
        parent_fullname = _get_parent_fullname(current)
        if not parent_fullname:
            break

        # Record it
        chain.append(parent_fullname)

        # Stop if we hit the top
        if parent_fullname.startswith('/Script'):
            break

        # Load this asset and continue up the chain
        current = loader.load_class(parent_fullname)

    chain.reverse()

    return chain


def _get_parent_fullname(export: ExportTableItem) -> Optional[str]:
    klassref = export.klass and export.klass.value

    # Ignore klass if it is a built-in type
    if klassref and isinstance(klassref, ImportTableItem) and klassref.namespace and klassref.namespace.value:
        if str(klassref.namespace.value.name).startswith('/Script'):
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
        if parent_fullname.startswith('/Script'):
            return parent_fullname  # nowhere else to go

        parent = export.asset.loader.load_class(parent_fullname)
    elif isinstance(parentref, ExportTableItem):
        # An export - simply follow it
        parent = parentref
    else:
        raise TypeError(f"Can't handle parent {parentref} of type {type(parentref)}")

    return parent.fullname
