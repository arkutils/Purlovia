'''
Verify some of the functionality in ark.taming_food.

These tests use artificial data and attempt to verify the tree reduction mechanisms.
'''

from operator import attrgetter
from typing import *

import pytest

import ark.taming_food.calc
import ark.taming_food.items
import ark.taming_food.species
from ark.taming_food.datatypes import Item, ItemOverride, ItemStatus
from utils.tree import IndexedTree

from ..common import *


@pytest.fixture(name='fake_items', scope='function')
def fixture_fake_items() -> IndexedTree[Item]:
    items = IndexedTree[Item](Item(bp='root', modid=''), attrgetter('bp'))

    items.add('root', Item(bp='berries', modid=''))
    items.add('berries', Item(bp='berry a', modid=''))
    items.add('berries', Item(bp='berry b', modid=''))
    items.add('berries', Item(bp='berry c', modid=''))

    items.add('root', Item(bp='meats', modid=''))
    items.add('meats', Item(bp='raw meat', modid=''))
    items.add('meats', Item(bp='cooked meat', modid=''))
    items.add('raw meat', Item(bp='raw prime', modid=''))
    items.add('raw meat', Item(bp='raw lamb', modid=''))
    items.add('cooked meat', Item(bp='cooked prime', modid=''))
    items.add('cooked meat', Item(bp='cooked lamb', modid=''))
    items.add('cooked meat', Item(bp='cooked meat jerky', modid=''))
    items.add('cooked prime', Item(bp='cooked prime jerky', modid=''))

    return items


def IS(bp: str, food: float = 0, affinity: float = 0):
    return ItemStatus(bp=bp, food=food, affinity=affinity)


def test_tree_collapse_identical_entries_into_empty_parent(fake_items):
    evals = IndexedTree[ItemStatus](IS('root'), attrgetter('bp'))

    evals.add('root', IS('berries'))
    evals.add('berries', IS('berry a', food=4, affinity=3))
    evals.add('berries', IS('berry b', food=4, affinity=3))
    evals.add('berries', IS('berry c', food=4, affinity=3))

    ark.taming_food.calc.collapse_full_trees(evals, fake_items)

    # Just root and berries should remain
    assert len(evals) == 2
    assert 'root' in evals
    assert 'berries' in evals

    # Ensure the common berry stats were boosted to berries
    assert evals['berries'].data.food == 4
    assert evals['berries'].data.affinity == 3


def test_collapse_identical_entries_into_identical_parent(fake_items):
    evals = IndexedTree[ItemStatus](IS('root'), attrgetter('bp'))

    evals.add('root', IS('berries', food=4, affinity=3))
    evals.add('berries', IS('berry a', food=4, affinity=3))
    evals.add('berries', IS('berry b', food=4, affinity=3))
    evals.add('berries', IS('berry c', food=4, affinity=3))

    ark.taming_food.calc.collapse_full_trees(evals, fake_items)

    # Just root and berries should remain
    assert len(evals) == 2
    assert 'root' in evals
    assert 'berries' in evals

    # Ensure the common berry stats were boosted to berries
    assert evals['berries'].data.food == 4
    assert evals['berries'].data.affinity == 3


def test_not_collapse_identical_entries_into_different_parent(fake_items):
    evals = IndexedTree[ItemStatus](IS('root'), attrgetter('bp'))

    evals.add('root', IS('berries', food=2, affinity=3))
    evals.add('berries', IS('berry a', food=4, affinity=3))
    evals.add('berries', IS('berry b', food=4, affinity=3))
    evals.add('berries', IS('berry c', food=4, affinity=3))

    ark.taming_food.calc.collapse_full_trees(evals, fake_items)

    # Just root and berries should remain
    assert len(evals) == 5
    assert 'root' in evals
    assert 'berries' in evals
    assert 'berry a' in evals
    assert 'berry b' in evals
    assert 'berry c' in evals

    # Ensure the common berry stats were not touched
    assert evals['berries'].data.food == 2
    assert evals['berries'].data.affinity == 3


def test_not_collapse_varied_entries_into_empty_parent(fake_items):
    evals = IndexedTree[ItemStatus](IS('root'), attrgetter('bp'))

    evals.add('root', IS('berries'))
    evals.add('berries', IS('berry a', food=2, affinity=3))
    evals.add('berries', IS('berry b', food=4, affinity=3))
    evals.add('berries', IS('berry c', food=4, affinity=3))

    ark.taming_food.calc.collapse_full_trees(evals, fake_items)

    # Just root and berries should remain
    assert len(evals) == 5
    assert 'root' in evals
    assert 'berries' in evals
    assert 'berry a' in evals
    assert 'berry b' in evals
    assert 'berry c' in evals

    # Ensure the common berry stats were not touched
    assert evals['berries'].data.food == 0
    assert evals['berries'].data.affinity == 0


def test_tree_recursive_collapse(fake_items):
    evals = IndexedTree[ItemStatus](IS('root'), attrgetter('bp'))

    evals.add('root', IS('meats'))
    evals.add('meats', IS('cooked meat', food=4, affinity=3))
    evals.add('cooked meat', IS('cooked prime', food=4, affinity=3))
    evals.add('cooked meat', IS('cooked meat jerky', food=4, affinity=3))
    evals.add('cooked meat', IS('cooked lamb', food=4, affinity=3))
    evals.add('cooked prime', IS('cooked prime jerky', food=4, affinity=3))

    ark.taming_food.calc.collapse_full_trees(evals, fake_items)

    # Entire cooked meat tree should collapse
    assert len(evals) == 3
    assert 'root' in evals
    assert 'meats' in evals
    assert 'cooked meat' in evals

    # Ensure the common berry stats were boosted to berries
    assert evals['cooked meat'].data.food == 4
    assert evals['cooked meat'].data.affinity == 3
