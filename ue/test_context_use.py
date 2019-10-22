from typing import Iterable

import pytest

from automate.ark import ArkSteamManager
from config import ConfigFile, get_global_config
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
    loader = arkman.createLoader()
    return loader


def test_defaults(loader: AssetLoader):
    loader.wipe_cache()
    asset = loader[ASSETNAME]
    assert asset.is_linked
    assert asset.has_properties
    assert not asset.has_bulk_data

    loader.wipe_cache()
    with ue_parsing_context():
        asset = loader[ASSETNAME]
        assert asset.is_linked
        assert asset.has_properties
        assert not asset.has_bulk_data


def test_linking(loader: AssetLoader):
    loader.wipe_cache()
    with ue_parsing_context(link=False):
        asset = loader[ASSETNAME]
        assert not asset.is_linked

        # Check asset is re-parsed when more data is requested
        with ue_parsing_context(link=True):
            asset = loader[ASSETNAME]
            assert asset.is_linked

    loader.wipe_cache()
    with ue_parsing_context(link=True):
        asset = loader[ASSETNAME]
        assert asset.is_linked


def test_properties(loader: AssetLoader):
    loader.wipe_cache()
    with ue_parsing_context(properties=False):
        asset = loader[ASSETNAME]
        assert not asset.has_properties

        # Check asset is re-parsed when more data is requested
        with ue_parsing_context(properties=True):
            asset = loader[ASSETNAME]
            assert asset.has_properties

    loader.wipe_cache()
    with ue_parsing_context(properties=True):
        asset = loader[ASSETNAME]
        assert asset.has_properties


def test_no_properties_without_link(loader: AssetLoader):
    loader.wipe_cache()
    with ue_parsing_context(link=False, properties=True):
        asset = loader[ASSETNAME]
        assert not asset.has_properties


def test_bulk_data(loader: AssetLoader):
    loader.wipe_cache()
    with ue_parsing_context(bulk_data=False):
        asset = loader[ASSETNAME]
        assert not asset.has_bulk_data

        # Check asset is re-parsed when more data is requested
        with ue_parsing_context(bulk_data=True):
            asset = loader[ASSETNAME]
            assert asset.has_bulk_data

    loader.wipe_cache()
    with ue_parsing_context(bulk_data=True):
        asset = loader[ASSETNAME]
        assert asset.has_bulk_data
