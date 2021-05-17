import pytest

import ark.discovery
from automate.ark import ArkSteamManager
from utils.tree import IndexedTree

from .common import *  # noqa: F401,F403  # needed to pick up all fixtures


@pytest.mark.requires_game
def test_populate(arkman: ArkSteamManager):
    tree = IndexedTree('/')
    relations = [
        ('A1', 'A'),
        ('A2', 'A'),
        ('B1', 'B'),
        ('A', '/'),
        ('B', '/'),
    ]

    ark.discovery._populate_tree_from_relations(tree, relations)

    assert len(tree.root.nodes) == 2
    assert len(tree['A'].nodes) == 2
    assert len(tree['B'].nodes) == 1
    assert 'A' in tree.root
    assert 'B' in tree.root
    assert 'A1' in tree['A']
    assert 'A2' in tree['A']
    assert 'B1' in tree['B']
