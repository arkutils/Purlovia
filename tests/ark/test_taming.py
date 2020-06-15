'''
Verify some of the functionality in ark.taming_food.

Much of this file relies heavily on game data and will need to be updated if it changes.
Core species are used in an effort to reduce this.
'''

from typing import *

import pytest

import ark.taming_food

from ..common import *

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


@pytest.fixture(name='items', scope='module')
def fixture_items(consumables, loader: AssetLoader):
    ark.taming_food.gather_items(loader)


@pytest.fixture(name='dodo_foods', scope='module')
def fixture_dodo_foods(dodos, loader: AssetLoader) -> List[ark.taming_food.ItemOverride]:
    return ark.taming_food.collect_species_data(DODO_CHR, loader)


@pytest.fixture(name='bary_foods', scope='module')
def fixture_bary_foods(baryonyx, loader: AssetLoader) -> List[ark.taming_food.ItemOverride]:
    return ark.taming_food.collect_species_data(BARY_CHR, loader)


@pytest.mark.requires_game
def test_gathering_items(items, loader: AssetLoader):
    # Check we gathered some key items and that they have a correct hierarchy
    assert MEATRAW_ITEM in ark.taming_food.items
    assert FISHRAW_ITEM in ark.taming_food.items
    assert ark.taming_food.items[FISHRAW_ITEM].parent == ark.taming_food.items[MEATRAW_ITEM]


@pytest.mark.requires_game
def test_collect_species_dodo(dodos, loader: AssetLoader):
    effects = ark.taming_food.collect_species_data(DODO_CHR, loader)
    assert len(effects) == 15
    assert effects[0].bp.endswith('SuperTestMeat_C') and effects[0].overrides.get('affinity', 0) == 100000.0
    assert effects[1].bp.endswith('Berry_Amarberry_C') and effects[1].overrides.get('affinity', 0) == 20.0


@pytest.mark.requires_game
def test_collect_species_bary(baryonyx, loader: AssetLoader):
    effects = ark.taming_food.collect_species_data(BARY_CHR, loader)
    assert len(effects) == 19
    assert effects[0].bp.endswith('SuperTestMeat_C') and effects[0].overrides.get('affinity', 0) == 100000.0
    assert effects[1].bp.endswith('RawMeat_Fish_C') and effects[1].overrides.get('affinity', 0) == 50.0


@pytest.mark.requires_game
def test_collect_item_amarberry(items, loader: AssetLoader):
    effect = ark.taming_food.items[BERRYAMAR_ITEM].data
    assert effect.name == 'Amarberry'
    assert effect.food.base == 1.0 and effect.food.speed == 3.0
    assert effect.torpor.base == 0.0 and effect.torpor.speed == 0.0
    assert effect.affinity.base == 0.0 and effect.affinity.speed == 0.0


@pytest.mark.requires_game
def test_collect_item_narcoberry(items, loader: AssetLoader):
    effect = ark.taming_food.items[BERRYNARC_ITEM].data
    assert effect.name == 'Narcoberry'
    assert effect.food.base == 4.0 and effect.food.speed == 3.0
    assert effect.torpor.base == 7.0 and effect.torpor.speed == 3.0
    assert effect.affinity.base == 0.0 and effect.affinity.speed == 0.0


@pytest.mark.requires_game
def test_collect_item_raw_meat(items, loader: AssetLoader):
    effect = ark.taming_food.items[MEATRAW_ITEM].data
    assert effect.name == 'Raw Meat'
    assert effect.food.base == 10.0 and effect.food.speed == 5.0
    assert effect.torpor.base == 0.0 and effect.torpor.speed == 0.0
    assert effect.affinity.base == 0.0 and effect.affinity.speed == 0.0


@pytest.mark.requires_game
def test_collect_item_raw_fish(items, loader: AssetLoader):
    effect = ark.taming_food.items[FISHRAW_ITEM].data
    assert effect.name == 'Raw Fish Meat'
    assert effect.food.base == 5.0 and effect.food.speed == 5.0
    assert effect.torpor.base == 0.0 and effect.torpor.speed == 0.0
    assert effect.affinity.base == 0.0 and effect.affinity.speed == 0.0


DODO_FOOD_EFFECTS = (
    (0.0, 0.0, 0.0, MEATRAW_ITEM),  # food * 0
    (13.33333, 0.0, 20.0, BERRYAMAR_ITEM),  # food = 1 * 13.333
    (4.0, 7.0, 0.0, BERRYNARC_ITEM),  # not overridden at all
)


@pytest.mark.requires_game
@pytest.mark.parametrize('food, torpor, affinity, item_cls', DODO_FOOD_EFFECTS)
def test_apply_dodo_items(dodo_foods, items, item_cls, food, torpor, affinity):
    effect = ark.taming_food.apply_species_overrides_to_item(ark.taming_food.items[item_cls].data, dodo_foods)
    assert effect.food.base == pytest.approx(food)
    assert effect.torpor.base == pytest.approx(torpor)
    assert effect.affinity.base == pytest.approx(affinity)


BARY_FOOD_EFFECTS = (
    (0.0, 0.0, 0.0, MEATRAW_ITEM),  # food * 0
    (5.0 * 5.0, 0.0, 50.0, FISHRAW_ITEM),
    (10.0 * 1.25, 0.0, 25.0, FISHCOOKED_ITEM),
    (0.0, 0.0, 0.0, BERRYAMAR_ITEM),  # food * 0
    (0.0, 7.0, 0.0, BERRYNARC_ITEM),  # food * 0
)


@pytest.mark.requires_game
@pytest.mark.parametrize('food, torpor, affinity, item_cls', BARY_FOOD_EFFECTS)
def test_apply_bary_items(bary_foods, items, item_cls, food, torpor, affinity):
    effect = ark.taming_food.apply_species_overrides_to_item(ark.taming_food.items[item_cls].data, bary_foods)
    assert effect.food.base == pytest.approx(food)
    assert effect.torpor.base == pytest.approx(torpor)
    assert effect.affinity.base == pytest.approx(affinity)
