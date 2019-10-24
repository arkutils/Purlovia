import ue.hierarchy

from .common import *

PRIMAL_DINO_CHR = '/Script/ShooterGame.PrimalDinoCharacter'
PRIMAL_CHR = '/Script/ShooterGame.PrimalCharacter'
DODO_CHR = '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP.Dodo_Character_BP_C'
DINO_CHR = '/Game/PrimalEarth/CoreBlueprints/Dino_Character_BP.Dino_Character_BP_C'
DODO_AB_CHR = '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP_Aberrant.Dodo_Character_BP_Aberrant_C'


@pytest.fixture(name='internal_hierarchy')
def fixture_internal_hierarchy():
    ue.hierarchy.tree.clear()
    ue.hierarchy.load_internal_hierarchy('config/hierarchy.yaml')


@pytest.fixture(name='dodos')
def fixture_dodos(loader: AssetLoader, internal_hierarchy):  # pylint: disable=unused-argument
    # Scan the Dodo directory
    ue.hierarchy.explore_path('/Game/PrimalEarth/Dinos/Dodo', loader, set())


@pytest.mark.requires_game
def test_hierarchy_init(internal_hierarchy):  # pylint: disable=unused-argument
    # Verify that some basic UE/ShooterGame types are in the hierarchy
    it = ue.hierarchy.find_parent_classes(PRIMAL_CHR)
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
    assert DINO_CHR in tree

    # ...and that they're all linked
    assert tree[DODO_AB_CHR].parent is tree[DODO_CHR]
    assert tree[DODO_CHR].parent is tree[DINO_CHR]
    assert tree[DINO_CHR].parent is tree[PRIMAL_DINO_CHR]
    assert tree[PRIMAL_DINO_CHR].parent is tree[PRIMAL_CHR]


@pytest.mark.requires_game
def test_find_parents(dodos):  # pylint: disable=unused-argument
    parents = list(ue.hierarchy.find_parent_classes(DODO_CHR))
    expected = [DINO_CHR, PRIMAL_DINO_CHR, '/Script/ShooterGame.PrimalCharacter', '/Script/Engine.Character']
    assert parents[:len(expected)] == expected


@pytest.mark.requires_game
def test_find_subclasses(dodos):  # pylint: disable=unused-argument
    subclasses = list(ue.hierarchy.find_sub_classes(DINO_CHR))
    assert DODO_CHR in subclasses
    assert DODO_AB_CHR in subclasses


@pytest.mark.requires_game
def test_inherits_from(loader: AssetLoader, dodos):  # pylint: disable=unused-argument
    dodo_ab_asset = loader[DODO_AB_CHR]
    assert dodo_ab_asset.default_class
    assert dodo_ab_asset.default_export

    # Ab Dodo inherits from Dino Chr
    assert ue.hierarchy.inherits_from(dodo_ab_asset.default_export, DINO_CHR)
    assert ue.hierarchy.inherits_from(dodo_ab_asset.default_class, DINO_CHR)

    # Ab Dodo inherits from Dodo Chr
    assert ue.hierarchy.inherits_from(dodo_ab_asset.default_export, DODO_CHR)
    assert ue.hierarchy.inherits_from(dodo_ab_asset.default_class, DODO_CHR)

    # Ab Dodo *export* inherits from Dodo Ab Chr
    assert ue.hierarchy.inherits_from(dodo_ab_asset.default_export, DODO_AB_CHR)

    # Ab Dodo *class* does not inherit from itself
    assert not ue.hierarchy.inherits_from(dodo_ab_asset.default_class, DODO_AB_CHR)
