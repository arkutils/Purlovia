from typing import Set, TypeVar, Union, cast

from .asset import ExportTableItem, UAsset
from .consts import BLUEPRINT_GENERATED_CLASS_CLS
from .hierarchy import find_parent_classes
from .loader import AssetLoader
from .properties import ObjectProperty
from .proxy import UEProxyStructure, get_proxy_for_type
from .tree import is_fullname_an_asset

__all__ = [
    'gather_properties',
    'find_default_for_class',
]

Tproxy = TypeVar('Tproxy', bound=UEProxyStructure)


def gather_properties(export: Union[ExportTableItem, ObjectProperty, UAsset]) -> Tproxy:
    '''Collect properties from an export, respecting the inheritance tree.'''
    if isinstance(export, ObjectProperty):
        return gather_properties(cast(ExportTableItem, export.value))

    if isinstance(export, UAsset):
        export = getattr(export, 'default_export', None)
        if export is None:
            raise ValueError("UAsset must have a default_export")

    if not isinstance(export, ExportTableItem):
        raise TypeError("ExportTableItem required")

    assert export.fullname
    assert export.asset and export.asset.loader
    loader = export.asset.loader
    proxy: Tproxy = get_proxy_for_type(export.fullname, loader)

    if not proxy:
        raise TypeError(f"No proxy type available for {export.fullname}")

    proxy.set_source(export)

    # Now fill properties in, starting from the bottom-most baseclass
    done: Set[ExportTableItem] = set()
    for fullname in reversed(list(find_parent_classes(export, include_self=True))):
        # Ignore classes outside /Game as they are not loadable assets
        # ...and their default values should already be built in to the proxies
        if not is_fullname_an_asset(fullname):
            continue

        export_to_read = find_default_for_class(fullname, loader)
        # Where an asset contains <cls> and Default__<cls> we redirect to the Default__
        # ...and ensure we don't import from the same place twice
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
