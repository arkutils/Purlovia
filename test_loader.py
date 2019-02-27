import loader


def test_clean_asset_name():
    assert loader.clean_asset_name('/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide') == \
        'Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP_FlyerRide'


def test_convert_asset_name_to_path():
    loader.set_asset_path('BASE')
    assert loader.convert_asset_name_to_path('One') == 'BASE\\One.uasset'
    assert loader.convert_asset_name_to_path('\\One') == 'BASE\\One.uasset'
    assert loader.convert_asset_name_to_path('\\One\\') == 'BASE\\One.uasset'
    assert loader.convert_asset_name_to_path('One\\') == 'BASE\\One.uasset'
    assert loader.convert_asset_name_to_path('One\\Two') == 'BASE\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('\\One\\Two') == 'BASE\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('\\One\\Two\\') == 'BASE\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('Game\\One') == 'BASE\\Content\\One.uasset'
    assert loader.convert_asset_name_to_path('\\Game\\One') == 'BASE\\Content\\One.uasset'
    assert loader.convert_asset_name_to_path('\\Game\\One\\') == 'BASE\\Content\\One.uasset'
    assert loader.convert_asset_name_to_path('Game\\One\\Two') == 'BASE\\Content\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('\\Game\\One\\Two') == 'BASE\\Content\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('\\Game\\One\\Two\\') == 'BASE\\Content\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('/One') == 'BASE\\One.uasset'
    assert loader.convert_asset_name_to_path('/One/') == 'BASE\\One.uasset'
    assert loader.convert_asset_name_to_path('Game/One/Two') == 'BASE\\Content\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('Game/One/Two/') == 'BASE\\Content\\One\\Two.uasset'
    assert loader.convert_asset_name_to_path('/Game/One/Two/') == 'BASE\\Content\\One\\Two.uasset'
