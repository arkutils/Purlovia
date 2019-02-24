from pytest import approx
import pytest

import structfinder

def find(values, fmt, data, before=0, after=0):
    '''
    Wrap the find_values_in_binary generator and return as a list.
    '''
    pad_before = '00 '*before
    pad_after = ' 00'*after
    data = pad_before + data + pad_after
    return list(structfinder.find_values_in_binary(values, fmt, bytes.fromhex(data)))

@pytest.fixture(scope='function', params=[0,1,2,3])
def before(request):
    '''
    A number of bytes to use as an offset.
    '''
    yield request.param

@pytest.fixture(scope='function', params=[0,1,2,3])
def after(request):
    '''
    A number of bytes to use as a postfix.
    '''
    yield request.param


def test_single_word_with_manual_padding():
    assert find([0x0D0C0B0A], 'i', '0A 0B 0C 0D') == [(0, (0x0D0C0B0A,), False)]
    assert find([0x0D0C0B0A], 'i', '0A 0B 0C 0D 00') == [(0, (0x0D0C0B0A,), False)]
    assert find([0x0D0C0B0A], 'i', '00 0A 0B 0C 0D') == [(1, (0x0D0C0B0A,), False)]
    assert find([0x0D0C0B0A], 'i', '00 0A 0B 0C 0D 00') == [(1, (0x0D0C0B0A,), False)]

# Below tests are all repeated with padding bytes before and after
# to ensure they work at different offsets and with data following

def test_single_byte(before, after):
    assert find([10], 'b', '0A', before, after) == [(before, (10,), False)]

def test_two_byte_sequence(before, after):
    assert find([10,11], 'b', '0A 0B', before, after) == [(before, (10,11), False)]

def test_two_byte_sequence_with_partial_match(before, after):
    assert find([10,11], 'b', '0A 0A 0B', before, after) == [(1+before, (10,11), False)]

def test_single_word(before, after):
    assert find([0x0D0C0B0A], 'i', '0A 0B 0C 0D', before, after) == [(before, (0x0D0C0B0A,), False)]

def test_single_float(before, after):
    assert find([10], 'f', '00 00 20 41', before, after) == [(before, (10,), False)]

def test_two_float_sequence(before, after):
    assert find([10,11], 'f', '00 00 20 41 00 00 30 41', before, after) == [(before, (10,11), False)]

def test_float_margins():
    assert find([1000.1], 'f', '66 06 7A 44') == [(0, (1000.0999755859375,), False)] # 1000.1
    assert find([1000.1], 'f', '67 06 7A 44') == [(0, (1000.1000366210938,), False)] # 1000.10001
    assert find([1000.1], 'f', '68 06 7A 44') == [(0, (1000.10009765625,), False)]   # 1000.1001
    assert find([1000.1], 'f', '77 06 7A 44') == [] # 1000.101 - too far away
    assert find([1000.1], 'f', '0A 07 7A 44') == [] # 1000.11 - too far away

