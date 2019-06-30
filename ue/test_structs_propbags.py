import pytest  # type: ignore
from .testutils import *

EMPTY_COLORS = dict(name=None, values=None)

DEFAULT_COLORS = dict(name=None,
                      values=('Light Green', 'Light Grey', 'Light Brown', 'Light Orange', 'Light Yellow', 'Light Red',
                              'Dark Grey', 'Brown', 'Black', 'Dark Green', 'Dark Red'))


@pytest.mark.uses_copyright_material
def test_DinoColorSetGeneric():
    asset = load_asset('PrimalEarth/CoreBlueprints/DinoColorSetGeneric')
    props = asset.default_export.properties
    colors = parse_colors(props)
    assert colors[0] == DEFAULT_COLORS
    assert colors[1] == DEFAULT_COLORS
    assert colors[2] == DEFAULT_COLORS
    assert colors[3] == DEFAULT_COLORS
    assert colors[4] == DEFAULT_COLORS


@pytest.mark.uses_copyright_material
def test_DinoColorSet_Baryonyx():
    asset = load_asset('PrimalEarth/CoreBlueprints/DinoColorSet_Baryonyx')
    props = asset.default_export.properties
    colors = parse_colors(props)
    assert colors[0] and colors[0]['name'] == 'Body'
    assert colors[0]['values'][0] == 'Dino Dark Orange' and colors[0]['values'][-1] == 'Black'
    assert colors[1] and colors[1]['name'] == 'Top Fins'
    assert colors[1]['values'][0] == 'Dino Light Yellow' and colors[1]['values'][-1] == 'Black'
    assert colors[2] == EMPTY_COLORS
    assert colors[3] == EMPTY_COLORS
    assert colors[4] and colors[4]['name'] == 'Top Stripes'
    assert colors[4]['values'][0] == 'Dino Dark Grey' and colors[4]['values'][-1] == 'Dark Grey'
    assert colors[5] and colors[5]['name'] == 'Underbelly'
    assert colors[5]['values'][0] == 'BigFoot0' and colors[5]['values'][-1] == 'Light Grey'


@pytest.mark.uses_copyright_material
def test_DinoColorSet_PolarBear():
    asset = load_asset('PrimalEarth/CoreBlueprints/DinoColorSet_PolarBear')
    props = asset.default_export.properties
    colors = parse_colors(props)
    assert colors[0] == dict(name=None, values=('White', ))
    assert colors[1] == dict(name=None, values=('White', ))
    assert colors[2] == dict(name=None, values=('White', ))
    assert colors[3] == dict(name=None, values=('White', ))
    assert colors[4] == dict(name=None, values=('White', ))
    assert colors[5] == dict(name=None, values=('White', ))


@pytest.mark.uses_copyright_material
def test_DinoColorSet_Raptor_Corrupt():
    asset = load_asset('Extinction/Dinos/Corrupt/DinoColorSet_Raptor_Corrupt')
    props = asset.default_export.properties
    colors = parse_colors(props)
    assert colors[0] and colors[0]['name'] == 'Dark Muted'
    assert colors[0]['values'][0] == 'Light Orange' and colors[0]['values'][-1] == 'DragonFire'
    assert colors[1] and colors[1]['name'] == 'Light All -oe'
    assert colors[1]['values'][0] == 'Light Orange' and colors[1]['values'][-1] == 'WyvernBlue1'
    assert 2 not in colors
    assert colors[3] and colors[3]['name'] == 'All Muted -w'
    assert colors[3]['values'][0] == 'Light Orange' and colors[3]['values'][-1] == 'WyvernBlue1'
    assert colors[4] and colors[4]['name'] == 'Light All -oek'
    assert colors[4]['values'][0] == 'Dark Grey' and colors[4]['values'][-1] == 'WyvernPurple0'
    assert colors[5] and colors[5]['name'] == 'Light Muted'
    assert colors[5]['values'][0] == 'Light Orange' and colors[5]['values'][-1] == 'DragonFire'


@pytest.mark.uses_copyright_material
def test_DinoColorSet_Apex__PrimalFear():
    asset = load_asset('Mods/839162288/ColorSets/DinoColorSet_Apex')
    props = asset.default_export.properties
    colors = parse_colors(props)
    assert colors[0] and colors[0]['name'] == 'Alpha1'
    assert colors[0]['values'][0] == 'ApexRed1' and colors[0]['values'][-1] == 'Black'
    assert colors[1] and colors[1]['name'] == 'Alpha1'
    assert colors[1]['values'][0] == 'ApexRed1' and colors[1]['values'][-1] == 'Celestial3'
    assert colors[2] and colors[2]['name'] == 'Alpha1'
    assert colors[2]['values'][0] == 'ApexRed1' and colors[2]['values'][-1] == 'Celestial3'
    assert colors[3] and colors[3]['name'] == 'Alpha1'
    assert colors[3]['values'][0] == 'ApexRed1' and colors[3]['values'][-1] == 'Black'
    assert colors[4] and colors[4]['name'] == 'Alpha1'
    assert colors[4]['values'][0] == 'ApexRed1' and colors[4]['values'][-1] == 'Celestial3'
    assert colors[5] and colors[5]['name'] == 'Alpha1'
    assert colors[5]['values'][0] == 'ApexRed1' and colors[5]['values'][-1] == 'Celestial3'
