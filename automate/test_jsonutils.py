import json

from .jsonutils import _format_json


def prop(data):
    '''
    Generate JSON for just the given data, when used as a property in a dict.
    The data is inserted into a dict but this dict is removed from the output,
    leaving just the formatted data.
    '''
    inp = dict(_=data)
    out = _format_json(inp, pretty=True)

    # Parse the json output again to ensure it matches
    assert inp == json.loads(out)

    # Strip out the container dict and first level of indent
    lines = out.split('\n')
    lines = lines[1:-1]
    lines[0] = lines[0][5:]
    out = '\n'.join(line[1:] for line in lines)

    return out


def test_dict_lone_values():
    assert prop(dict(p=12345)) == '{ "p": 12345 }'
    assert prop(dict(p="abc")) == '{ "p": "abc" }'
    assert prop(dict(p=None)) == '{ "p": null }'
    assert prop(dict(p=True)) == '{ "p": true }'
    assert prop(dict(p=True)) == '{ "p": true }'


def test_dict_unknown_two_values():
    assert prop(dict(p=12345, q=67890)) == '{\n\t"p": 12345,\n\t"q": 67890\n}'
    assert prop(dict(p="abc", q="def")) == '{\n\t"p": "abc",\n\t"q": "def"\n}'
    assert prop(dict(p=None, q=None)) == '{\n\t"p": null,\n\t"q": null\n}'
    assert prop(dict(p=True, q=False)) == '{\n\t"p": true,\n\t"q": false\n}'


def test_dict_known_two_values():
    assert prop(dict(a=12345, b=67890)) == '{ "a": 12345, "b": 67890 }'
    assert prop(dict(a="abc", b="def")) == '{ "a": "abc", "b": "def" }'
    assert prop(dict(a=None, b=None)) == '{ "a": null, "b": null }'
    assert prop(dict(a=True, b=False)) == '{ "a": true, "b": false }'


def test_array_ints():
    # One-line
    assert prop(list(range(1))) == '[ 0 ]'
    assert prop(list(range(3))) == '[ 0, 1, 2 ]'
    assert prop(list(range(5))) == '[ 0, 1, 2, 3, 4 ]'
    assert prop(list(range(13))) == '[ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 ]'

    # Wrapped  (in bulk)
    assert prop(list(range(14))) == '[\n\t0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, \n\t13\n]'


def test_array_strings():
    # One-line
    assert prop(["one"]) == '[ "one" ]'
    assert prop(["one", "two"]) == '[ "one", "two" ]'
    assert prop(["one", "two", "three"]) == '[ "one", "two", "three" ]'
    assert prop(["one", "two", "three", "four"]) == '[ "one", "two", "three", "four" ]'

    # Wrapped
    assert prop(["one", "two", "three", "four", "five"]) == \
        '[\n\t"one",\n\t"two",\n\t"three",\n\t"four",\n\t"five"\n]'


def test_array_bools():
    # One-line
    assert prop([True]) == '[ true ]'
    assert prop([True, False]) == '[ true, false ]'
    assert prop([True, False, True]) == '[ true, false, true ]'
    assert prop([True] * 11) == '[ ' + 'true, '*10 + 'true ]'
    assert prop([True] * 12) == '[ ' + 'true, '*11 + 'true ]'
    assert prop([True] * 13) == '[ ' + 'true, '*12 + 'true ]'
    assert prop([False] * 13) == '[ ' + 'false, '*12 + 'false ]'

    # Wrapped
    assert prop([True] * 14) == '[\n\t' + 'true, '*13 + '\n\ttrue\n]'
    assert prop([False] * 14) == '[\n\t' + 'false, '*13 + '\n\tfalse\n]'


def test_array_nulls():
    # One-line
    assert prop([None]) == '[ null ]'
    assert prop([None, None]) == '[ null, null ]'

    # We do not want nulls in stat arrays to be combined
    assert prop([
        [1200, 0.1, 0.1, 0, 0.15],
        None,
        None,
        [170, 0.02, 0.04, 0, 0],
    ]) == '[\n\t[ 1200, 0.1, 0.1, 0, 0.15 ],\n\tnull,\n\tnull,\n\t[ 170, 0.02, 0.04, 0, 0 ]\n]'


def test_item_weights():
    assert prop([0.05, "PrimalItem_WeaponBola_AETranq_C"]) == '[ 0.05, "PrimalItem_WeaponBola_AETranq_C" ]'
    assert prop([0.05, None]) == '[ 0.05, null ]'

    # In a dict
    assert prop(dict(items=[
        [0.05, "PrimalItem_WeaponBola_AETranq_C"],
        [0.05, None],
    ])) == '''{
\t"items": [
\t\t[ 0.05, "PrimalItem_WeaponBola_AETranq_C" ],
\t\t[ 0.05, null ]
\t]
}'''


def test_color_entry():
    # Color entries are compressed to a single line
    assert prop(["Light Grey", [0.581026, 0.6, 0.59417, 0.0]]) == \
        '[ "Light Grey", [ 0.581026, 0.6, 0.59417, 0.0 ] ]'


def test_optional_fields():
    assert prop(dict(lat=1)) == '{ "lat": 1 }'
    assert prop(dict(lat=1, long=2)) == '{ "lat": 1, "long": 2 }'


def test_original_tests():
    '''
    Reproduces the old monolithic test.
    This should only be treated as an easy way to spot changes.
    '''
    test_data = dict(
        lone_int_field=dict(a=13245),
        lone_str_field=dict(a="abc"),
        lone_null_field=dict(a=None),
        lone_float_field=dict(a=13245.1345),
        lone_big_float_field=dict(a=-9E18),
        lone_long_field=dict(a="A longer string " * 4),
        lone_longer_field=dict(a="A longer string " * 8),
        two_fields=dict(a=123, c=457),
        color_array=[0.1, 1, -9E18],
        long_number_array=[0.1, 1, -9E18] * 2,
        longer_number_array=[0.1, 1, -9E18] * 6,
        str_array=["one"],
        str_big_array=["one two three four five"],
        long_str_array=["one 1", "two 2", "three 3"],
        longer_str_array=["one", "two", "three"] * 2,
        long_str_big_array=["one" * 8, "two" * 8, "three" * 8],
        plain_xyz=dict(x=1436325.5, y=532476.132, z=-32450),
        plain_latlon=dict(lat=20.45643, lon=56.32451),
        xyz_latlon=dict(a="hello", x=1436325.5, y=532476.132, z=-32450, lat=20.45643, lon=56.32451, b=435.1),
        xyz_latlong=dict(a="hello", x=1436325.5, y=532476.132, z=-32450, lat=20.45643, long=56.32451, b=435.1),
        color_data=[
            ["Cyan", [0.0, 1.0, 1.0, 0.0]],
            ["Magenta", [1.0, 0.0, 1.0, 0.0]],
            ["Light Green", [0.5325, 1.0, 0.5, 0.0]],
            ["Light Grey", [0.581026, 0.6, 0.59417, 0.0]],
        ],
        item_weights={
            'items': [
                [0.05, "PrimalItem_WeaponMetalHatchet_C"],
                [0.05, "PrimalItem_WeaponMetalPick_C"],
                [0.05, "PrimalItem_WeaponSickle_C"],
                [0.05, "PrimalItemAmmo_Grapple_C"],
                [0.05, "PrimalItemWeapon_EternalSpyglass_C"],
                [0.05, "PrimalItem_WeaponSickle_AEStone_C"],
                [0.05, "PrimalItem_WeaponStoneHatchet_AE_C"],
                [0.05, "PrimalItem_WeaponStonePick_AE_C"],
                [0.05, "PrimalItem_WeaponBola_AETranq_C"],
                [0.05, None],
                [1, None],
            ]
        },
        qty=dict(min=1, max=2),
        qty_pow=dict(min=1, max=2, pow=3),
    )

    result = _format_json(test_data, pretty=True)

    # Clean up the expected data, which the editor messes with
    expected = ORIGINAL_TEST_OUTPUT.replace('    ', '\t')  # 4 space -> tab
    expected = expected.replace('⎕', ' ')  # ⎕ -> space

    assert result == expected


ORIGINAL_TEST_OUTPUT = '''{
    "lone_int_field": { "a": 13245 },
    "lone_str_field": { "a": "abc" },
    "lone_null_field": { "a": null },
    "lone_float_field": { "a": 13245.1345 },
    "lone_big_float_field": { "a": -9e+18 },
    "lone_long_field": { "a": "A longer string A longer string A longer string A longer string " },
    "lone_longer_field": {
        "a": "A longer string A longer string A longer string A longer string A longer string A longer string A longer string A longer string "
    },
    "two_fields": {
        "a": 123,
        "c": 457
    },
    "color_array": [ 0.1, 1, -9e+18 ],
    "long_number_array": [ 0.1, 1, -9e+18, 0.1, 1, -9e+18 ],
    "longer_number_array": [
        0.1, 1, -9e+18, 0.1, 1, -9e+18, 0.1, 1, -9e+18, 0.1, 1, -9e+18, 0.1,⎕
        1, -9e+18, 0.1, 1, -9e+18
    ],
    "str_array": [ "one" ],
    "str_big_array": [ "one two three four five" ],
    "long_str_array": [ "one 1", "two 2", "three 3" ],
    "longer_str_array": [
        "one",
        "two",
        "three",
        "one",
        "two",
        "three"
    ],
    "long_str_big_array": [
        "oneoneoneoneoneoneoneone",
        "twotwotwotwotwotwotwotwo",
        "threethreethreethreethreethreethreethree"
    ],
    "plain_xyz": { "x": 1436325.5, "y": 532476.132, "z": -32450 },
    "plain_latlon": { "lat": 20.45643, "lon": 56.32451 },
    "xyz_latlon": {
        "a": "hello",
        "x": 1436325.5, "y": 532476.132, "z": -32450,
        "lat": 20.45643, "lon": 56.32451,
        "b": 435.1
    },
    "xyz_latlong": {
        "a": "hello",
        "x": 1436325.5, "y": 532476.132, "z": -32450,
        "lat": 20.45643, "long": 56.32451,
        "b": 435.1
    },
    "color_data": [
        [ "Cyan", [ 0.0, 1.0, 1.0, 0.0 ] ],
        [ "Magenta", [ 1.0, 0.0, 1.0, 0.0 ] ],
        [ "Light Green", [ 0.5325, 1.0, 0.5, 0.0 ] ],
        [ "Light Grey", [ 0.581026, 0.6, 0.59417, 0.0 ] ]
    ],
    "item_weights": {
        "items": [
            [ 0.05, "PrimalItem_WeaponMetalHatchet_C" ],
            [ 0.05, "PrimalItem_WeaponMetalPick_C" ],
            [ 0.05, "PrimalItem_WeaponSickle_C" ],
            [ 0.05, "PrimalItemAmmo_Grapple_C" ],
            [ 0.05, "PrimalItemWeapon_EternalSpyglass_C" ],
            [ 0.05, "PrimalItem_WeaponSickle_AEStone_C" ],
            [ 0.05, "PrimalItem_WeaponStoneHatchet_AE_C" ],
            [ 0.05, "PrimalItem_WeaponStonePick_AE_C" ],
            [ 0.05, "PrimalItem_WeaponBola_AETranq_C" ],
            [ 0.05, null ],
            [ 1, null ]
        ]
    },
    "qty": { "min": 1, "max": 2 },
    "qty_pow": { "min": 1, "max": 2, "pow": 3 }
}'''
