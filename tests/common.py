from typing import *

import pytest  # type: ignore

from automate.ark import ArkSteamManager
from config import ConfigFile, get_global_config
from ue.asset import ExportTableItem, UAsset
from ue.context import ParsingContext, get_ctx, ue_parsing_context
from ue.loader import AssetLoader

ASSETNAME = '/Game/Mods/1821554891/PrimalGameData_BP_PurloviaTEST'


@pytest.fixture(name='config')
def fixture_config() -> ConfigFile:
    config = get_global_config()
    assert '1821554891' in config.mods, "PurloviaTEST must be in config to run these tests"
    config.settings.SkipGit = True
    config.settings.SkipInstall = True
    return config


@pytest.fixture(name='loader')
def fixture_loader(config: ConfigFile) -> AssetLoader:
    arkman = ArkSteamManager(config=config)
    loader = arkman.getLoader()
    return loader
