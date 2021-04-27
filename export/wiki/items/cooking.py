from ark.types import PrimalItem
from automate.hierarchy_exporter import ExportModel, Field

from export.wiki.models import FloatLike


class CookingIngredientData(ExportModel):
    health: FloatLike = Field(0, description="Health increased per item")
    stamina: FloatLike = Field(0, description="Stamina increased per item")
    food: FloatLike = Field(0, description="Food increased per item")
    weight: FloatLike = Field(0, description="Weight increased per item")
    water: FloatLike = Field(0, description="Water increased per item in a drink")


def convert_cooking_values(item: PrimalItem) -> CookingIngredientData:
    return CookingIngredientData(
        health=item.Ingredient_HealthIncreasePerQuantity[0],
        stamina=item.Ingredient_StaminaIncreasePerQuantity[0],
        food=item.Ingredient_FoodIncreasePerQuantity[0],
        weight=item.Ingredient_WeightIncreasePerQuantity[0],
        water=item.Ingredient_WaterIncreasePerQuantity[0],
    )
