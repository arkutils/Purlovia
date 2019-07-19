from pathlib import Path

from pytest import fixture  # type: ignore

from .loader import AssetLoader, ModResolver


class DummyLoader(ModResolver):
    def get_name_from_id(self, modid: str) -> str:
        raise NotImplementedError

    def get_id_from_name(self, name: str) -> str:
        raise NotImplementedError


@fixture
def loader():
    l = AssetLoader(DummyLoader(), assetpath='./output')
    return l


def test_clean_asset_name(loader):
    base = loader.asset_path
    assert loader.clean_asset_name('Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide') == \
        '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'
    assert loader.clean_asset_name('/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide.uasset') == \
        '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'
    assert loader.clean_asset_name('/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide.DinoCharacterStatusComponent_BP_FlyerRide_C') == \
        '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'
    assert loader.clean_asset_name('/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide') == \
        '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'


def test_convert_asset_name_to_path(loader):
    base = loader.asset_path
    assert loader.convert_asset_name_to_path('One') == f'{base}\\One.uasset'
    assert loader.convert_asset_name_to_path('\\One') == f'{base}\\One.uasset'
    assert loader.convert_asset_name_to_path('\\One\\') == f'{base}\\One.uasset'
    assert loader.convert_asset_name_to_path('One\\') == f'{base}\\One.uasset'
    assert loader.convert_asset_name_to_path('One\\Two') == f'{base}\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('\\One\\Two') == f'{base}\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('\\One\\Two\\') == f'{base}\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('Game\\One') == f'{base}\\Content\\One.uasset'
    assert loader.convert_asset_name_to_path('\\Game\\One') == f'{base}\\Content\\One.uasset'
    assert loader.convert_asset_name_to_path('\\Game\\One\\') == f'{base}\\Content\\One.uasset'
    assert loader.convert_asset_name_to_path('Game\\One\\Two') == f'{base}\\Content\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('\\Game\\One\\Two') == f'{base}\\Content\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('\\Game\\One\\Two\\') == f'{base}\\Content\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('/One') == f'{base}\\One.uasset'
    assert loader.convert_asset_name_to_path('/One/') == f'{base}\\One.uasset'
    assert loader.convert_asset_name_to_path('Game/One/Two') == f'{base}\\Content\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('Game/One/Two/') == f'{base}\\Content\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('/Game/One/Two/') == f'{base}\\Content\\One\\Two.uasset'
