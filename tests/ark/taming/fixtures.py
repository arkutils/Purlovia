import pytest

import ark.taming_food.items
import ark.taming_food.species
from ark.taming_food.datatypes import Item, SpeciesFoods
from tests.common import BARY_CHR, DAEODON_CHR, DODO_CHR, fixture_arkman, fixture_config, \
    fixture_consumables, fixture_internal_hierarchy, fixture_loader  # noqa: F401
from ue.loader import AssetLoader
from utils.tree import IndexedTree


@pytest.fixture(name='items', scope='module')
def fixture_items(consumables, loader: AssetLoader) -> IndexedTree[Item]:
    ark.taming_food.items.gather_items(loader)
    return ark.taming_food.items.food_items


@pytest.fixture(name='dodo_foods', scope='module')
def fixture_dodo_foods(dodos, loader: AssetLoader) -> SpeciesFoods:
    return ark.taming_food.species.collect_species_data(DODO_CHR, loader)


@pytest.fixture(name='bary_foods', scope='module')
def fixture_bary_foods(baryonyx, loader: AssetLoader) -> SpeciesFoods:
    return ark.taming_food.species.collect_species_data(BARY_CHR, loader)


@pytest.fixture(name='daeodon_foods', scope='module')
def fixture_daeodon_foods(daeodon, loader: AssetLoader) -> SpeciesFoods:
    return ark.taming_food.species.collect_species_data(DAEODON_CHR, loader)
