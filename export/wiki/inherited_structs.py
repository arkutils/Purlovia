from typing import Any, Dict

from ue.asset import ExportTableItem
from ue.hierarchy import find_parent_classes


def _gather_props_from_export(export: ExportTableItem, name: str, index: int, output: Dict[str, Any]):
    props = export.properties.get_property(name, index, fallback=None)
    if not props:
        return

    for key, value in props.as_dict().items():
        output[key] = value


def gather_inherited_struct_fields(leaf_export: ExportTableItem,
                                   field: str,
                                   defaults: Dict[str, Any],
                                   index: int = 0) -> Dict[str, Any]:
    loader = leaf_export.asset.loader
    output = dict(defaults)

    # Make sure this is always the default export, and not e.g. default class.
    leaf_export = leaf_export.asset.default_export

    for kls in reversed(list(find_parent_classes(leaf_export))):

        if not kls.startswith('/Game'):
            continue

        # Load the asset and get its default export (the CDO).
        # find_parent_classes gives us merely a list of parent classes, and not "parent" CDOs.
        asset = loader[kls]
        super_export = asset.default_export

        _gather_props_from_export(super_export, field, index, output)

    return output
