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

    chain = list(find_parent_classes(export, include_self=True))
    proxy = None
    while not proxy and chain:
        baseclass_fullname = chain.pop()
        proxy = proxy_for_type(baseclass_fullname)

    if not proxy:
        raise TypeError(f"No proxy type available for {baseclass_fullname}")

    for fullname in reversed(chain):
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
