from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from ark.types import PrimalItem
from automate.hierarchy_exporter import ExportModel, Field
from export.wiki.models import FloatLike
from ue.properties import FloatProperty, IntProperty, StructProperty
from ue.utils import clean_float


class RecipeIngredient(ExportModel):
    exact: bool = Field(True, description="If true, child classes can be used instead")
    qty: FloatLike = Field(..., title="Base quantity")
    type: str = Field(..., title="Item class name")


class CraftingData(ExportModel):
    xp: FloatProperty = Field(..., description="XP granted per item crafted")
    time: FloatProperty = Field(..., description="Time it takes to craft a blueprint")
    levelReq: IntProperty = Field(..., title="Required player level")
    productCount: int = Field(
        ..., description="If zero, the item is likely given via scripts or triggers a specific action (like boss summoners)")
    skillQualityMult: Tuple[FloatProperty, FloatProperty] = Field(
        ...,
        description="Min and max multipliers of Crafting Skill's effect on quality",
    )
    recipe: List[RecipeIngredient] = Field(...)


class RepairData(ExportModel):
    xp: FloatProperty = Field(..., description="XP granted per item repaired")
    time: FloatProperty = Field(..., description="Time to repair an item")
    recipe: List[RecipeIngredient] = Field(
        [],
        title="Required ingredients, if different from crafting",
    )


def convert_recipe_entry(entry: Dict[str, Any]) -> Optional[RecipeIngredient]:
    type_value = entry['ResourceItemType'].value
    type_value = type_value and type_value.value
    if not type_value:
        return None

    return RecipeIngredient(
        exact=bool(entry['bCraftingRequireExactResourceType']),
        qty=entry['BaseResourceRequirement'],
        type=str(type_value.name),
    )


def convert_recipe_entries(entries: List[StructProperty]) -> Iterable[RecipeIngredient]:
    # Game skips entries where the resource class is null.
    for entry in entries:
        converted = convert_recipe_entry(entry.as_dict())
        if converted:
            yield converted


def convert_crafting_values(item: PrimalItem,
                            has_durability: bool = False) -> Tuple[Optional[CraftingData], Optional[RepairData]]:
    recipe = item.get('BaseCraftingResourceRequirements', 0, None)
    if not recipe:
        return (None, None)

    # Crafted item number
    if item.bCraftDontActuallyGiveItem[0]:
        product_count: Union[int, IntProperty] = 0
    elif item.CraftingGivesItemQuantityOverride[0].value >= 1:
        product_count = item.CraftingGiveItemCount[0]
    else:
        product_count = item.ItemQuantity[0]

    crafting = CraftingData(
        xp=item.BaseCraftingXP[0],
        time=item.BlueprintTimeToCraft[0],
        levelReq=item.CraftingMinLevelRequirement[0],
        productCount=int(product_count),
        skillQualityMult=(item.CraftingSkillQualityMultiplierMin[0], item.CraftingSkillQualityMultiplierMax[0]),
        recipe=list(convert_recipe_entries(recipe.values)),
    )

    # Do not export crafting info if recipe consists only of nulls.
    if not crafting.recipe:
        return (None, None)

    # Durability repair info
    repair = None
    if item.bAllowRepair[0] and has_durability:
        repair = RepairData(
            xp=item.BaseRepairingXP[0],
            time=item.TimeForFullRepair[0],
            recipe=[],
        )

        if item.bOverrideRepairingRequirements[0]:
            recipe = item.get('OverrideRepairingRequirements', 0, None)
            if not recipe or not recipe.values:
                # Override to no ingredients, skip repair.
                repair = None
            else:
                # Convert the repair requirements list.
                repair.recipe = list(convert_recipe_entries(recipe.values))

                # Do not export repair info if the overrides lead to no valid ingredients
                if not repair.recipe:
                    repair = None
        else:
            # Copy crafting ingredients and scale their quantities by the repair multiplier.
            qty_mult = item.RepairResourceRequirementMultiplier[0]
            if qty_mult != 1.0:
                for ingredient in crafting.recipe:
                    ingredient_copy = ingredient.copy()
                    ingredient_copy.qty = clean_float(ingredient_copy.qty * qty_mult)
                    repair.recipe.append(ingredient_copy)

    return (crafting, repair)
