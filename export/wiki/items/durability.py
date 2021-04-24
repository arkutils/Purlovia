from typing import Optional

from ark.types import PrimalItem

from .poc_stat_gathering import STAT_DURABILITY, gather_item_stat


def convert_durability_values(item: PrimalItem) -> Optional[float]:
    if not item.bUseItemDurability[0] or not item.bUseItemStats[0]:
        return None

    statinfo = gather_item_stat(item, STAT_DURABILITY)
    if not statinfo['bUsed']:
        return None

    return statinfo['InitialValueConstant']
