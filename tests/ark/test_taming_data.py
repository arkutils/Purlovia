import pytest

from ark.stats import Stat
from ark.taming_food.datatypes import SpeciesFoods
from tests.ark.test_taming_game import fixture_arkman, fixture_config, fixture_dodo_foods, \
    fixture_dodos, fixture_internal_hierarchy, fixture_loader  # noqa: F401


@pytest.mark.requires_game
def test_dodo_food_effects(dodo_foods: SpeciesFoods):
    assert dodo_foods.child_eats is None
    assert len(dodo_foods.adult_eats) == 15
    checks = (
        (0, 'SuperTestMeat', 100000, 1),
        (1, 'Berry_Amarberry', 20, 13.33333),
        (14, 'Kibble_Base_XSmall', 400, 0.888),
    )
    for i, name, affinity, food in checks:
        assert name in dodo_foods.adult_eats[i].bp
        assert dodo_foods.adult_eats[i].affinity_override == affinity
        assert dodo_foods.adult_eats[i].mults.get(Stat.Food, 0) == food
