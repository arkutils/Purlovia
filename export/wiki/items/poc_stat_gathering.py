from typing import Any, Dict

from ark.types import PrimalItem
from ue.asset import ExportTableItem
from ue.hierarchy import find_parent_classes

DEFAULTS = {
    # DevKit Verified
    'bUsed': False,
    'InitialValueConstant': 0,
}

STAT_GENERIC_QUALITY = 0
STAT_ARMOR = 1
STAT_DURABILITY = 2
STAT_DAMAGE_PERCENT = 3
STAT_CLIP_AMMO = 4
STAT_HYPO_INSULATION = 5
STAT_WEIGHT = 6
STAT_HYPER_INSULATION = 7


def _gather_props_from_export(export: ExportTableItem, index: int, output: Dict[str, Any]):
    props = export.properties.get_property('ItemStatInfos', index, fallback=None)
    if not props:
        return

    for key, value in props.as_dict().items():
        output[key] = value


def gather_item_stat(item: PrimalItem, index: int) -> Dict[str, Any]:
    leaf_export = item.get_source()
    loader = leaf_export.asset.loader
    output = dict(**DEFAULTS)

    # Make sure this is always the default export, and not e.g. default class.
    leaf_export = leaf_export.asset.default_export

    for kls in reversed(list(find_parent_classes(leaf_export))):

        if not kls.startswith('/Game'):
            continue

        asset = loader[kls]
        super_export = asset.default_export

        _gather_props_from_export(super_export, index, output)

    _gather_props_from_export(leaf_export, index, output)

    return output
