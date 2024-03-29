import os.path

from pytest import fixture  # type: ignore

from tests.common import MockModResolver

from .loader import AssetLoader


@fixture
def loader():
    loader = AssetLoader(modresolver=MockModResolver(), assetpath='./output')
    return loader


def test_clean_asset_name(loader):
    _ = loader.asset_path
    assert loader.clean_asset_name('Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide') == \
        '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'
    assert loader.clean_asset_name('/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide.uasset') == \
        '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'
    assert loader.clean_asset_name('/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide' +
        '.DinoCharacterStatusComponent_BP_FlyerRide_C') == \
        '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'
    assert loader.clean_asset_name('/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide') == \
        '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'


def test_convert_asset_name_to_path(loader):
    s = os.path.sep
    base = loader.asset_path

    def convert(name: str):
        return str(loader.convert_asset_name_to_path(name, check_exists=False))

    assert convert('One') == f'{base}{s}One.uasset'
    assert convert('\\One') == f'{base}{s}One.uasset'
    assert convert('\\One\\') == f'{base}{s}One.uasset'
    assert convert('One\\') == f'{base}{s}One.uasset'
    assert convert('One\\Two') == f'{base}{s}One{s}Two.uasset'
    assert convert('\\One\\Two') == f'{base}{s}One{s}Two.uasset'
    assert convert('\\One\\Two\\') == f'{base}{s}One{s}Two.uasset'
    assert convert('Game\\One') == f'{base}{s}Content{s}One.uasset'
    assert convert('\\Game\\One') == f'{base}{s}Content{s}One.uasset'
    assert convert('\\Game\\One\\') == f'{base}{s}Content{s}One.uasset'
    assert convert('Game\\One\\Two') == f'{base}{s}Content{s}One{s}Two.uasset'
    assert convert('\\Game\\One\\Two') == f'{base}{s}Content{s}One{s}Two.uasset'
    assert convert('\\Game\\One\\Two\\') == f'{base}{s}Content{s}One{s}Two.uasset'
    assert convert('/One') == f'{base}{s}One.uasset'
    assert convert('/One/') == f'{base}{s}One.uasset'
    assert convert('Game/One/Two') == f'{base}{s}Content{s}One{s}Two.uasset'
    assert convert('Game/One/Two/') == f'{base}{s}Content{s}One{s}Two.uasset'
    assert convert('/Game/One/Two/') == f'{base}{s}Content{s}One{s}Two.uasset'
