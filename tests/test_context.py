import pytest  # type: ignore

from .common import *


@pytest.mark.requires_game
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


@pytest.mark.requires_game
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


@pytest.mark.requires_game
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


@pytest.mark.requires_game
def test_no_properties_without_link(loader: AssetLoader):
    loader.wipe_cache()
    with ue_parsing_context(link=False, properties=True):
        asset = loader[ASSETNAME]
        assert not asset.has_properties


@pytest.mark.requires_game
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
