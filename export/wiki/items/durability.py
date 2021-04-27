from typing import Optional

from ark.types import PrimalItem

from .stat_gathering import Stat, gather_item_stat


def convert_durability_values(item: PrimalItem) -> Optional[float]:
    if not item.bUseItemDurability[0] or not item.bUseItemStats[0]:
        return None

    statinfo = gather_item_stat(item, Stat.Durability)
    if not statinfo['bUsed']:
        return None

    # Enough for the base value.
    out = statinfo['InitialValueConstant']

    maxv = statinfo['AbsoluteMaxValue']
    if maxv != 0 and out > maxv:
        out = statinfo['AbsoluteMaxValue']

    return out
