from ark.types import PrimalItem
from automate.hierarchy_exporter import ExportModel, Field


class CookingIngredientData(ExportModel):
    health: float = Field(0, title="Health increased per item")
    stamina: float = Field(0, title="Stamina increased per item")
    food: float = Field(0, title="Food increased per item")
    weight: float = Field(0, title="Weight increased per item")
    water: float = Field(0, title="Water increased per item in a drink")


def convert_cooking_values(item: PrimalItem) -> CookingIngredientData:
    return CookingIngredientData(
        health=float(item.Ingredient_HealthIncreasePerQuantity[0]),
        stamina=float(item.Ingredient_StaminaIncreasePerQuantity[0]),
        food=float(item.Ingredient_FoodIncreasePerQuantity[0]),
        weight=float(item.Ingredient_WeightIncreasePerQuantity[0]),
        water=float(item.Ingredient_WaterIncreasePerQuantity[0]),
    )
