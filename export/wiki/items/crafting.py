from typing import Any, Dict

from ark.types import PrimalItem


def convert_recipe_entry(entry):
    result = dict(
        exact=entry['bCraftingRequireExactResourceType'],
        qty=entry['BaseResourceRequirement'],
        type=entry['ResourceItemType'].value.value.name,
    )
    return result


def convert_crafting_values(item: PrimalItem) -> Dict[str, Any]:
    v: Dict[str, Any] = dict(
        xp=item.BaseCraftingXP[0],
        bpCraftTime=(item.MinBlueprintTimeToCraft[0], item.BlueprintTimeToCraft[0]),
        minLevelReq=item.CraftingMinLevelRequirement[0],
        productCount=item.CraftingGiveItemCount[0],
        skillQualityMult=(item.CraftingSkillQualityMultiplierMin[0], item.CraftingSkillQualityMultiplierMax[0]),
    )

    recipe = item.get('BaseCraftingResourceRequirements', 0, None)
    if recipe and recipe.values:
        v['recipe'] = [convert_recipe_entry(entry.as_dict()) for entry in recipe.values]

    return v


def convert_repair_values(item: PrimalItem) -> Dict[str, Any]:
    v: Dict[str, Any] = dict(
        xp=item.BaseRepairingXP[0],
        time=item.TimeForFullRepair[0],
        resourceMult=item.RepairResourceRequirementMultiplier[0],
    )

    if item.bOverrideRepairingRequirements[0]:
        recipe = item.get('OverrideRepairingRequirements', 0, None)
        if recipe and recipe.values:
            v['recipe'] = [convert_recipe_entry(entry.as_dict()) for entry in recipe.values]

    return v
