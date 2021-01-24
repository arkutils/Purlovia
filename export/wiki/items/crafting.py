from typing import List, Optional, Tuple, Union

from ark.types import PrimalItem
from automate.hierarchy_exporter import ExportModel, Field
from ue.properties import FloatProperty, IntProperty


class RecipeIngredient(ExportModel):
    exact: Optional[bool] = Field(..., title="Are child classes accepted?")
    qty: Optional[FloatProperty] = Field(
        ...,
        title="Required quantity",
        description="Scales with blueprint quality",
    )
    type: Optional[str] = Field(..., title="Item blueprint")


class CraftingData(ExportModel):
    xp: Optional[FloatProperty] = Field(..., title="XP granted per item crafted")
    bpCraftTime: Optional[FloatProperty] = Field(..., title="Time to craft a blueprint")
    minLevelReq: Optional[IntProperty] = Field(..., title="Required player level")
    productCount: int = Field(..., title="Number of products")
    skillQualityMult: Tuple[FloatProperty,
                            FloatProperty] = Field(..., title="Min and max multipliers of Crafting Skill's effect on quality")
    recipe: List[Optional[RecipeIngredient]] = Field(..., title="Required ingredients")


class RepairData(ExportModel):
    xp: Optional[FloatProperty] = Field(..., title="XP granted per item repaired")
    time: Optional[FloatProperty] = Field(..., title="Time to repair an item")
    resourceMult: Optional[FloatProperty] = Field(..., title="Ingredient count multiplier")
    recipe: Optional[List[RecipeIngredient]] = Field(None, title="Required ingredients override")


def convert_recipe_entry(entry) -> RecipeIngredient:
    type_value = entry['ResourceItemType'].value
    type_value = type_value and type_value.value
    if not type_value:
        return None

    return RecipeIngredient(
        exact=bool(entry['bCraftingRequireExactResourceType']),
        qty=entry['BaseResourceRequirement'],
        type=str(type_value.name),
    )


def convert_crafting_values(item: PrimalItem) -> Tuple[Optional[CraftingData], Optional[RepairData]]:
    recipe = item.get('BaseCraftingResourceRequirements', 0, None)
    if not recipe:
        return None, None

    # Crafted item number
    if item.bCraftDontActuallyGiveItem[0]:
        product_count: Union[int, IntProperty] = 0
    elif item.CraftingGivesItemQuantityOverride[0].value >= 1:
        product_count = item.CraftingGiveItemCount[0]
    else:
        product_count = item.ItemQuantity[0]

    crafting = CraftingData(
        xp=item.BaseCraftingXP[0],
        bpCraftTime=item.BlueprintTimeToCraft[0],
        minLevelReq=item.CraftingMinLevelRequirement[0],
        productCount=int(product_count),
        skillQualityMult=(item.CraftingSkillQualityMultiplierMin[0], item.CraftingSkillQualityMultiplierMax[0]),
        recipe=[convert_recipe_entry(entry.as_dict()) for entry in recipe.values],
    )

    # Do not export crafting info if recipe consists only of nulls
    if not all(crafting.recipe):
        return None, None

    # Durability repair info
    repair = None
    if bool(item.bAllowRepair[0]) and bool(item.bUseItemDurability[0]):
        repair = RepairData(
            xp=item.BaseRepairingXP[0],
            time=item.TimeForFullRepair[0],
            resourceMult=item.RepairResourceRequirementMultiplier[0],
        )
        if item.bOverrideRepairingRequirements[0]:
            recipe = item.get('OverrideRepairingRequirements', 0, None)
            if recipe and recipe.values:
                repair.recipe = [convert_recipe_entry(entry.as_dict()) for entry in recipe.values]

    return crafting, repair
