'''
Verify some of the functionality in ark.taming_food.

Much of this file relies heavily on game data and will need to be updated if it changes.
Core species are used in an effort to reduce this.
'''

import pytest

import ark.taming_food.evaluate
import ark.taming_food.items
import ark.taming_food.species
from ark.stats import Stat
from ark.taming_food.datatypes import Item, ItemStatEffect, SpeciesFoods
from ue.loader import AssetLoader
from utils.tree import IndexedTree

from ..common import BARY_CHR, BERRY_ITEM, BERRYAMAR_ITEM, BERRYMEJO_ITEM, BERRYNARC_ITEM, DODO_CHR, FISHCOOKED_ITEM, \
    FISHCOOKEDPRIME_ITEM, FISHRAW_ITEM, FISHRAWPRIME_ITEM, KIBBLEBASIC_ITEM, KIBBLEREGULAR_ITEM, MEATCOOKED_ITEM, \
    MEATCOOKEDPRIME_ITEM, MEATRAW_ITEM, MEATRAWPRIME_ITEM, VEGCARROT_ITEM, fixture_arkman, fixture_baryonyx, \
    fixture_config, fixture_consumables, fixture_dodos, fixture_internal_hierarchy, fixture_loader  # noqa: F401
from .taming.fixtures import fixture_bary_foods, fixture_daeodon_foods, fixture_dodo_foods, fixture_items  # noqa: F401

# All of these make sense for testing purposes
# pylint: disable=singleton-comparison
# pylint: disable=unidiomatic-typecheck
# pylint: disable=unused-argument

TEST_ITEMS = (
    BERRY_ITEM,
    BERRYAMAR_ITEM,
    BERRYMEJO_ITEM,
    BERRYNARC_ITEM,
    MEATRAW_ITEM,
    MEATRAWPRIME_ITEM,
    MEATCOOKED_ITEM,
    MEATCOOKEDPRIME_ITEM,
    FISHRAW_ITEM,
    FISHRAWPRIME_ITEM,
    FISHCOOKED_ITEM,
    FISHCOOKEDPRIME_ITEM,
)


@pytest.mark.requires_game
def test_gathering_items(items: IndexedTree[Item], loader: AssetLoader):
    # Check we gathered some key items and that they have a correct hierarchy
    assert MEATRAW_ITEM in items
    assert FISHRAW_ITEM in items
    assert items[FISHRAW_ITEM].parent == items[MEATRAW_ITEM]


@pytest.mark.requires_game
def test_collect_species_dodo(dodos, loader: AssetLoader):
    dodo_data = ark.taming_food.species.collect_species_data(DODO_CHR, loader)
    assert len(dodo_data.adult_eats) == 15
    assert dodo_data.adult_eats[0].bp.endswith('SuperTestMeat_C') and dodo_data.adult_eats[0].affinity_override == 100000.0
    assert dodo_data.adult_eats[1].bp.endswith('Berry_Amarberry_C') and dodo_data.adult_eats[1].affinity_override == 20.0


@pytest.mark.requires_game
def test_collect_species_bary(baryonyx, loader: AssetLoader):
    bary_data = ark.taming_food.species.collect_species_data(BARY_CHR, loader)
    assert len(bary_data.adult_eats) == 19
    assert bary_data.adult_eats[0].bp.endswith('SuperTestMeat_C') and bary_data.adult_eats[0].affinity_override == 100000.0
    assert bary_data.adult_eats[1].bp.endswith('RawMeat_Fish_C') and bary_data.adult_eats[1].affinity_override == 50.0


@pytest.mark.requires_game
def test_collect_item_amarberry(items: IndexedTree[Item], loader: AssetLoader):
    effect = items[BERRYAMAR_ITEM].data
    assert effect.name == 'Amarberry'
    assert effect.use_item_stats[Stat.Food] == ItemStatEffect(1.5, 3.0)
    assert Stat.Torpidity not in effect.use_item_stats
    assert effect.affinity_mult == 1.0


@pytest.mark.requires_game
def test_collect_item_narcoberry(items: IndexedTree[Item], loader: AssetLoader):
    effect = items[BERRYNARC_ITEM].data
    assert effect.name == 'Narcoberry'
    assert effect.use_item_stats[Stat.Food] == ItemStatEffect(4.0, 3.0)
    assert effect.use_item_stats[Stat.Torpidity] == ItemStatEffect(7.5, 3.0)
    assert effect.affinity_mult == 1.0


@pytest.mark.requires_game
def test_collect_item_raw_meat(items: IndexedTree[Item], loader: AssetLoader):
    effect = items[MEATRAW_ITEM].data
    assert effect.name == 'Raw Meat'
    assert effect.use_item_stats[Stat.Food] == ItemStatEffect(10.0, 5.0)
    assert Stat.Torpidity not in effect.use_item_stats
    assert effect.affinity_mult == 1.0


@pytest.mark.requires_game
def test_collect_item_raw_fish(items: IndexedTree[Item], loader: AssetLoader):
    effect = items[FISHRAW_ITEM].data
    assert effect.name == 'Raw Fish Meat'
    assert effect.use_item_stats[Stat.Food] == ItemStatEffect(5.0, 5.0)
    assert Stat.Torpidity not in effect.use_item_stats
    assert effect.affinity_mult == 0.4


# In-game observations: (affinity calculated)

DODO_FOOD_EFFECTS = (
    (85.248, 0.0, 400, KIBBLEBASIC_ITEM),
    (40.0, 0.0, 40.0, VEGCARROT_ITEM),
    (30.0, 0.0, 30.0, BERRYMEJO_ITEM),
    (20.0, 0.0, 20.0, BERRYAMAR_ITEM),
    (None, None, None, BERRYNARC_ITEM),
    (0.0, 0.0, 1.0, MEATRAW_ITEM),  # DOES NOT EAT
)

BARY_FOOD_EFFECTS = (
    (85.248, 0.0, 400, KIBBLEREGULAR_ITEM),
    (25.0, 0.0, 60, FISHRAWPRIME_ITEM),  # ~60
    (25.0, 0.0, 20, FISHRAW_ITEM),  # ~20
    (25.7, 0.0, 30, FISHCOOKEDPRIME_ITEM),  # ~30
    (12.5, 0.0, 10, FISHCOOKED_ITEM),  # ~10
    (0.0, 0.0, 0.0, MEATRAW_ITEM),  # DOES NOT EAT
    (0.0, 0.0, 0.0, BERRYAMAR_ITEM),  # DOES NOT EAT
    (0.0, 7.5, 1.0, BERRYNARC_ITEM),  # DOES NOT EAT
)


@pytest.mark.requires_game
@pytest.mark.parametrize('food, torpor, affinity, item_cls', DODO_FOOD_EFFECTS)
def test_apply_dodo_items(dodo_foods: SpeciesFoods, items: IndexedTree[Item], item_cls, food, torpor, affinity):
    effect = ark.taming_food.evaluate._apply_species_overrides_to_item(items[item_cls].data, dodo_foods.adult_eats)
    if food is None:
        assert effect is None
        return

    assert effect

    if food:
        assert effect.use_item_stats[Stat.Food].base == pytest.approx(food)
    else:
        assert Stat.Food not in effect.use_item_stats

    if torpor:
        assert effect.use_item_stats[Stat.Torpidity].base == pytest.approx(torpor)
    else:
        assert Stat.Torpidity not in effect.use_item_stats

    assert effect.get_affinity_total() == pytest.approx(affinity)


# @pytest.mark.requires_game
# @pytest.mark.parametrize('food, torpor, affinity, item_cls', BARY_FOOD_EFFECTS)
# def test_apply_bary_items(bary_foods: SpeciesFoods, items: IndexedTree[Item], item_cls, food, torpor, affinity):
#     effect = ark.taming_food.evaluate._apply_species_overrides_to_item(items[item_cls].data, bary_foods.adult_eats)
#     assert effect

#     if food:
#         assert effect.use_item_stats[Stat.Food].base == pytest.approx(food)
#     else:
#         assert Stat.Food not in effect.use_item_stats

#     if torpor:
#         assert effect.use_item_stats[Stat.Torpidity].base == pytest.approx(torpor)
#     else:
#         assert Stat.Torpidity not in effect.use_item_stats

#     assert effect.affinity == pytest.approx(affinity)
