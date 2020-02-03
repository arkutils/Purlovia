from functools import lru_cache
from typing import *

from ark.defaults import *

from .asset import ExportTableItem
from .base import UEBase
from .consts import BLUEPRINT_GENERATED_CLASS_CLS
from .hierarchy import find_parent_classes
from .loader import AssetLoader
from .properties import ObjectProperty
from .proxy import UEProxyStructure, proxy_for_type
from .tree import is_fullname_an_asset

__all__ = [
    'gather_properties',
    'get_default_props_for_class',
]

Tproxy = TypeVar('Tproxy', bound=UEProxyStructure)


def gather_properties(export: ExportTableItem) -> Tproxy:
    '''Collect properties from an export, respecting the inheritance tree.'''
    if isinstance(export, ObjectProperty):
        return gather_properties(export.value)

    if not isinstance(export, ExportTableItem):
        raise TypeError("ExportTableItem required")

    loader = export.asset.loader

    chain = list(find_parent_classes(export, include_self=True))
    proxy = None
    while not proxy and chain:
        baseclass_fullname = chain.pop()
        proxy = proxy_for_type(baseclass_fullname)

    if not proxy:
        raise TypeError(f"No proxy type available for {baseclass_fullname}")

    proxy.set_source(export)

    done: Set[ExportTableItem] = set()
    for fullname in reversed(chain):
        if not is_fullname_an_asset(fullname):
            continue  # Defaults are already in proxy - skip

        export_to_read = find_default_for_class(fullname, loader)
        if export_to_read in done:
            continue

        done.add(export_to_read)

        props = export_to_read.properties.as_dict()
        proxy.update(props)

    return proxy


def find_default_for_class(fullname: str, loader: AssetLoader) -> ExportTableItem:
    '''
    Work out which export to read properties from.
    In normal cases this will be the export itself, but for BlueprintGeneratedClass exports
    we need to look for a Default__ export that inherits from it.
    '''
    cls = loader.load_class(fullname)

    # Special-case all BP-generated classes - redirect to the Default__ export's properties
    if cls.klass and cls.klass.value.fullname == BLUEPRINT_GENERATED_CLASS_CLS:
        # Check the asset's default_export as this is usually the correct export
        if cls.asset.default_export and cls.asset.default_export.klass and cls.asset.default_export.klass.value is cls:
            return cls.asset.default_export

        # Find the Default__ export for this class and return its properties
        for export in cls.asset.exports:
            if str(export.name).startswith('Default__') and export.klass and export.klass.value is cls:
                return export

        raise RuntimeError("Unable to find Default__ property export for: " + str(cls))

    return cls
