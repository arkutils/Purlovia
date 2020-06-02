import pytest

import ue.hierarchy
from ark.types import DINO_CHR_CLS, PDC_CLS, PRIMAL_CHR_CLS
from ue.loader import AssetLoader

from .common import *  # noqa: F401,F403  # needed to pick up all fixtures
from .common import DODO_AB_CHR, DODO_CHR


@pytest.mark.requires_game
def test_hierarchy_init(internal_hierarchy):  # pylint: disable=unused-argument
    # Verify that some basic UE/ShooterGame types are in the hierarchy
    it = ue.hierarchy.find_parent_classes(PRIMAL_CHR_CLS)
    assert next(it) == '/Script/Engine.Character'
    assert next(it) == '/Script/Engine.Pawn'
    assert next(it) == '/Script/Engine.Actor'
    assert next(it) == '/Script/CoreUObject.Object'
    with pytest.raises(StopIteration):
        next(it)


@pytest.mark.requires_game
def test_exploring_assets(dodos):  # pylint: disable=unused-argument
    tree = ue.hierarchy.tree

    # Ensure some of the assets from this directory are present
    assert DODO_CHR in tree
    assert DODO_AB_CHR in tree

    # Also ensure it loaded the parent asset (which is outside this directory)
    assert DINO_CHR_CLS in tree

    # ...and that they're all linked
    assert tree[DODO_AB_CHR].parent is tree[DODO_CHR]
    assert tree[DODO_CHR].parent is tree[DINO_CHR_CLS]
    assert tree[DINO_CHR_CLS].parent is tree[PDC_CLS]
    assert tree[PDC_CLS].parent is tree[PRIMAL_CHR_CLS]


@pytest.mark.requires_game
def test_find_parents(dodos):  # pylint: disable=unused-argument
    parents = list(ue.hierarchy.find_parent_classes(DODO_CHR))
    expected = [DINO_CHR_CLS, PDC_CLS, '/Script/ShooterGame.PrimalCharacter', '/Script/Engine.Character']
    assert parents[:len(expected)] == expected


@pytest.mark.requires_game
def test_find_subclasses(dodos):  # pylint: disable=unused-argument
    subclasses = list(ue.hierarchy.find_sub_classes(DINO_CHR_CLS))
    assert DODO_CHR in subclasses
    assert DODO_AB_CHR in subclasses


@pytest.mark.requires_game
def test_inherits_from(loader: AssetLoader, dodos):  # pylint: disable=unused-argument
    dodo_ab_asset = loader[DODO_AB_CHR]
    assert dodo_ab_asset.default_class
    assert dodo_ab_asset.default_export

    # Ab Dodo inherits from Dino Chr
    assert ue.hierarchy.inherits_from(dodo_ab_asset.default_export, DINO_CHR_CLS)
    assert ue.hierarchy.inherits_from(dodo_ab_asset.default_class, DINO_CHR_CLS)

    # Ab Dodo inherits from Dodo Chr
    assert ue.hierarchy.inherits_from(dodo_ab_asset.default_export, DODO_CHR)
    assert ue.hierarchy.inherits_from(dodo_ab_asset.default_class, DODO_CHR)

    # Ab Dodo *export* inherits from Dodo Ab Chr
    assert ue.hierarchy.inherits_from(dodo_ab_asset.default_export, DODO_AB_CHR)

    # Ab Dodo *class* does not inherit from itself
    assert not ue.hierarchy.inherits_from(dodo_ab_asset.default_class, DODO_AB_CHR)
