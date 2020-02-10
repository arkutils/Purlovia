from typing import Any, Dict

from ark.types import PrimalItem


def convert_durability_values(item: PrimalItem) -> Dict[str, Any]:
    return dict(durability=dict(
        min=item.MinItemDurability[0],
        ignoreInWater=item.bDurabilityRequirementIgnoredInWater[0],
    ))
