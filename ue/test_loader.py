from pathlib import Path
from pytest import fixture
from .loader import AssetLoader, ModResolver


class DummyLoader(ModResolver):
    def get_name_from_id(self, modid: int) -> str:
        raise NotImplementedError

    def get_id_from_name(self, name: str) -> int:
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
    assert loader.clean_asset_name('/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide') == \
        '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'
    assert loader.clean_asset_name(f'{base}/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide') == \
        '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'
    assert loader.clean_asset_name(str(Path(f'{base}/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'))) == \
        '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'
    assert loader.clean_asset_name(str(Path(f'{base}\\Game\\PrimalEarth\\CoreBlueprints\\DinoCharacterStatusComponent_BP_FlyerRide'))) == \
        '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'
    assert loader.clean_asset_name(str(Path(f'{base}/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide').absolute())) == \
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
    assert loader.convert_asset_name_to_path(f'{base}\\One') == f'{base}\\One.uasset'
    assert loader.convert_asset_name_to_path(f'{base.absolute()}\\One') == f'{base}\\One.uasset'
    assert loader.convert_asset_name_to_path(f'{base.absolute()}/One') == f'{base}\\One.uasset'
    assert loader.convert_asset_name_to_path(f'{base.absolute().resolve()}\\One') == f'{base}\\One.uasset'
    assert loader.convert_asset_name_to_path(f'{base.absolute().resolve()}/One') == f'{base}\\One.uasset'
