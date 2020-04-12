from typing import Callable

import pytest  # type: ignore

import ue.hierarchy
from ark.discovery import initialise_hierarchy
from ark.types import *
from automate.ark import ArkSteamManager
from config import HIERARCHY_FILENAME, ConfigFile, get_global_config
from ue.asset import ExportTableItem, UAsset
from ue.context import ParsingContext, get_ctx, ue_parsing_context
from ue.loader import AssetLoader

TEST_PGD_PKG = '/Game/Mods/1821554891/PrimalGameData_BP_PurloviaTEST'
TEST_PGD_CLS = TEST_PGD_PKG + '.PrimalGameData_BP_PurloviaTEST_C'

TROODON_CHR = '/Game/PrimalEarth/Dinos/Troodon/Troodon_Character_BP.Troodon_Character_BP_C'
DODO_CHR = '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP.Dodo_Character_BP_C'
DODO_AB_CHR = '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP_Aberrant.Dodo_Character_BP_Aberrant_C'
DEINO_CHR = '/Game/PrimalEarth/Dinos/Raptor/Uberraptor/Deinonychus_Character_BP.Deinonychus_Character_BP_C'
X_DRAGON_CHR = '/Game/Genesis/Dinos/BiomeVariants/Volcano_Dragon/Volcanic_Dragon_Character_BP.Volcanic_Dragon_Character_BP_C'
DRAGON_BOSS_CHR = '/Game/PrimalEarth/Dinos/Dragon/Dragon_Character_BP_Boss.Dragon_Character_BP_Boss_C'


@pytest.fixture(name='config', scope='module')
def fixture_config() -> ConfigFile:
    config = get_global_config()
    assert '1821554891' in config.mods, "PurloviaTEST must be in config to run these tests"
    config.settings.SkipGit = True
    config.settings.SkipInstall = True
    return config


@pytest.fixture(name='arkman', scope='module')
def fixture_arkman(config: ConfigFile) -> ArkSteamManager:
    arkman = ArkSteamManager(config=config)
    return arkman


@pytest.fixture(name='loader', scope='module')
def fixture_loader(arkman: ArkSteamManager) -> AssetLoader:
    loader = arkman.getLoader()
    return loader


@pytest.fixture(name='hierarchy', scope='module')
def fixture_hierarchy(arkman: ArkSteamManager, config: ConfigFile):
    initialise_hierarchy(arkman, config)


@pytest.fixture(name='internal_hierarchy', scope='module')
def fixture_internal_hierarchy():
    ue.hierarchy.tree.clear()
    ue.hierarchy.load_internal_hierarchy(HIERARCHY_FILENAME)


@pytest.fixture(name='dodos', scope='module')
def fixture_dodos(loader: AssetLoader, internal_hierarchy):  # pylint: disable=unused-argument
    # Scan the Dodo directory
    ue.hierarchy.explore_path('/Game/PrimalEarth/Dinos/Dodo', loader, set())


@pytest.fixture(name='troodon', scope='module')
def fixture_troodon(loader: AssetLoader, internal_hierarchy):  # pylint: disable=unused-argument
    # Scan the Troondon asset
    ue.hierarchy.explore_asset(TROODON_CHR, loader)


@pytest.fixture(name='test_hierarchy', scope='module')
def fixture_test_hierarchy(loader: AssetLoader, internal_hierarchy):  # pylint: disable=unused-argument
    # Scan the test mod's directory
    ue.hierarchy.explore_path('/Game/Mods/1821554891/', loader, set())


@pytest.fixture(name='ark_types', scope='module')
def fixture_ark_types(loader: AssetLoader, internal_hierarchy):  # pylint: disable=unused-argument
    # Scan just a few Ark core types
    ue.hierarchy.explore_asset(DCSC_CLS, loader)


@pytest.fixture(name='scan_and_load', scope='module')
def fixture_scan_and_load(loader: AssetLoader, ark_types):  # pylint: disable=unused-argument
    def _scan_and_load(cls_name: str):
        cls = loader.load_class(cls_name)
        ue.hierarchy.explore_asset(cls.asset.assetname, loader)
        return cls

    return _scan_and_load


ScanLoadFn = Callable[[str], ExportTableItem]
