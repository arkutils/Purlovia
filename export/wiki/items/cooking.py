from typing import Optional

from ark.types import PrimalItem
from automate.hierarchy_exporter import ExportModel, Field
from ue.properties import FloatProperty


class CookingIngredientData(ExportModel):
    health: Optional[FloatProperty] = Field(..., title="Health increased per item")
    stamina: Optional[FloatProperty] = Field(..., title="Stamina increased per item")
    food: Optional[FloatProperty] = Field(..., title="Food increased per item")
    weight: Optional[FloatProperty] = Field(..., title="Weight increased per item")
    water: Optional[FloatProperty] = Field(..., title="Water increased per item in a drink")


def convert_cooking_values(item: PrimalItem) -> CookingIngredientData:
    return CookingIngredientData(
        health=item.Ingredient_HealthIncreasePerQuantity[0],
        stamina=item.Ingredient_StaminaIncreasePerQuantity[0],
        food=item.Ingredient_FoodIncreasePerQuantity[0],
        weight=item.Ingredient_WeightIncreasePerQuantity[0],
        water=item.Ingredient_WaterIncreasePerQuantity[0],
    )
