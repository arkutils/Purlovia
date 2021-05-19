from enum import Enum
from typing import Any, Dict

from ark.types import PrimalItem
from export.wiki.inherited_structs import gather_inherited_struct_fields

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


def gather_item_stat(item: PrimalItem, index: Stat) -> Dict[str, Any]:
    leaf_export = item.get_source()
    ark_index = index.value
    return gather_inherited_struct_fields(leaf_export, 'ItemStatInfos', DEFAULTS, ark_index)
