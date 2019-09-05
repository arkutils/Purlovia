from typing import Iterable

import pytest
from pytest_mock import MockFixture

from ark.export_asb.species_discovery import SpeciesTester
from automate.ark import ArkSteamManager
from ue.asset import UAsset
from ue.gathering import discover_inheritance_chain
from ue.loader import AssetLoader

from .discovery import AssetTester, Discoverer


class PGDTester(AssetTester):
    @classmethod
    def get_category_name(cls) -> str:
        return "pgd"

    @classmethod
    def get_file_extensions(cls) -> Iterable[str]:
        return (".uasset", )

    @classmethod
    def get_requires_properties(cls) -> bool:
        return False

    def is_a_fast_match(self, mem: bytes) -> bool:
        return b'Default__PrimalGameData_BP_C' in mem

    def is_a_full_match(self, asset: UAsset) -> bool:
        assert asset.default_class

        # Inefficient, for testing only!
        # Uncached, and collects the entire chain even if the target is already found.
        parents = discover_inheritance_chain(asset.default_class)
        return '/Game/PrimalEarth/CoreBlueprints/PrimalGameData_BP.PrimalGameData_BP_C' in parents


@pytest.fixture(name='loader')
def fixture_loader() -> AssetLoader:
    arkman = ArkSteamManager()
    loader = arkman.createLoader()
    return loader


@pytest.fixture(name='testmod_assetpath')
def fixture_testmod_assetpath():
    return '/Game/Mods/PurloviaTEST'


@pytest.mark.requires_game
def test_run_with_no_testers(loader: AssetLoader, testmod_assetpath: str):
    d = Discoverer(loader)
    with pytest.raises(Exception):
        d.run(testmod_assetpath)


@pytest.mark.requires_game
def test_mod_with_pgd_tester(loader: AssetLoader, testmod_assetpath: str, mocker: MockFixture):
    d = Discoverer(loader)

    tester = PGDTester()
    d.register_asset_tester(tester)

    fast_spy = mocker.spy(tester, 'is_a_fast_match')
    full_spy = mocker.spy(tester, 'is_a_full_match')

    results = d.run(testmod_assetpath)

    assert results and 'pgd' in results
    assert results['pgd'] == ['/Game/Mods/PurloviaTEST/PrimalGameData_BP_PurloviaTEST']

    assert fast_spy.call_count > 1
    assert full_spy.call_count == 1
