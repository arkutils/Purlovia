from typing import Any, Dict

from ark.types import PrimalItem


def convert_cooking_values(item: PrimalItem) -> Dict[str, Any]:
    return dict(cookingStats=dict(
        health=item.Ingredient_HealthIncreasePerQuantity[0],
        stamina=item.Ingredient_StaminaIncreasePerQuantity[0],
        food=item.Ingredient_FoodIncreasePerQuantity[0],
        weight=item.Ingredient_WeightIncreasePerQuantity[0],
    ))
