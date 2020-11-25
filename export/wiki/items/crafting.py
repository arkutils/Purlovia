from typing import Any, Dict, Union

from ark.types import PrimalItem
from ue.properties import IntProperty


def convert_recipe_entry(entry):
    type_value = entry['ResourceItemType'].value
    type_value = type_value and type_value.value
    if not type_value:
        return None

    result = dict(
        exact=entry['bCraftingRequireExactResourceType'],
        qty=entry['BaseResourceRequirement'],
        type=type_value.name,
    )
    return result


def convert_crafting_values(item: PrimalItem) -> Dict[str, Any]:
    if item.bCraftDontActuallyGiveItem[0]:
        product_count: Union[int, IntProperty] = 0
    else:
        if item.CraftingGivesItemQuantityOverride[0].value >= 1:
            product_count = item.CraftingGiveItemCount[0]
        else:
            product_count = item.ItemQuantity[0]

    v: Dict[str, Any] = dict(crafting=dict(
        xp=item.BaseCraftingXP[0],
        bpCraftTime=item.BlueprintTimeToCraft[0],
        minLevelReq=item.CraftingMinLevelRequirement[0],
        productCount=product_count,
        skillQualityMult=(item.CraftingSkillQualityMultiplierMin[0], item.CraftingSkillQualityMultiplierMax[0]),
    ))

    recipe = item.get('BaseCraftingResourceRequirements', 0, None)
    if recipe and recipe.values:
        v['crafting']['recipe'] = [v for v in (convert_recipe_entry(entry.as_dict()) for entry in recipe.values) if v]

    if item.bAllowRepair[0]:
        v['repair'] = dict(
            xp=item.BaseRepairingXP[0],
            time=item.TimeForFullRepair[0],
            resourceMult=item.RepairResourceRequirementMultiplier[0],
        )
        if item.bOverrideRepairingRequirements[0]:
            recipe = item.get('OverrideRepairingRequirements', 0, None)
            if recipe and recipe.values:
                v['repair']['recipe'] = [v for v in (convert_recipe_entry(entry.as_dict()) for entry in recipe.values) if v]

    return v
