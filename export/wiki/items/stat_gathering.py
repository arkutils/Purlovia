from enum import Enum
from typing import Any, Dict

from ark.types import PrimalItem
from ue.asset import ExportTableItem
from ue.hierarchy import find_parent_classes

DEFAULTS = {
    # DevKit Verified
    'bUsed': False,
    'InitialValueConstant': 0,
    'StateModifierScale': 1,
    'DefaultModifierValue': 0,
    'AbsoluteMaxValue': 0,
}


class Stat(Enum):
    GenericQuality = 0
    Armor = 1
    Durability = 2
    DamagePercent = 3
    ClipAmmo = 4
    HypoInsulation = 5
    Weight = 6
    HyperInsulation = 7


def _gather_props_from_export(export: ExportTableItem, index: int, output: Dict[str, Any]):
    props = export.properties.get_property('ItemStatInfos', index, fallback=None)
    if not props:
        return

    for key, value in props.as_dict().items():
        output[key] = value


def gather_item_stat(item: PrimalItem, index: Stat) -> Dict[str, Any]:
    leaf_export = item.get_source()
    loader = leaf_export.asset.loader
    output = dict(DEFAULTS)
    ark_index = index.value

    # Make sure this is always the default export, and not e.g. default class.
    leaf_export = leaf_export.asset.default_export

    for kls in reversed(list(find_parent_classes(leaf_export))):

        if not kls.startswith('/Game'):
            continue

        # Load the asset and get its default export (the CDO).
        # find_parent_classes gives us merely a list of parent classes, and not "parent" CDOs.
        asset = loader[kls]
        super_export = asset.default_export

        _gather_props_from_export(super_export, ark_index, output)

    return output
