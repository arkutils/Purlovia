import os
from glob import iglob
from itertools import chain
from pathlib import Path
from tempfile import gettempdir

from pytest_mock import MockFixture  # type: ignore

from .cachefile import cache_data

TMP = Path(gettempdir())
PREFIX = 'purlovia_cachetest'
EXTENSIONS = ('.hash', '.pickle')


def teardown_function():
    # Remove all related files from tmp
    for filename in chain(*[iglob(str(TMP / f'{PREFIX}*{ext}')) for ext in EXTENSIONS]):
        os.remove(filename)


def get_cached_data(key, _simple_data_fn, mocker: MockFixture, name='data', force=False):
    data_fn_mock = mocker.Mock(wraps=_simple_data_fn, name='_simple_data_fn')
    result = cache_data(key, TMP / (PREFIX+'_'+name), data_fn_mock, force_regenerate=force)
    return (result, data_fn_mock.call_count)


def test_cached_data_generates_and_stores_data(mocker: MockFixture):
    key = dict(version=1)
    expected_result = _simple_data_fn(key)

    result, calls = get_cached_data(key, _simple_data_fn, mocker)
    assert result == expected_result
    assert calls == 1

    # Ensure it generated the correct files
    assert (TMP / f'{PREFIX}_data.hash').is_file()
    assert (TMP / f'{PREFIX}_data.pickle').is_file()


def test_cached_data_fetches_from_cache(mocker: MockFixture):
    key = dict(version=1)
    expected_result = _simple_data_fn(key)

    # Run once, expecting the data to be generated
    result, calls = get_cached_data(key, _simple_data_fn, mocker)
    assert result == expected_result
    assert calls == 1

    # Run again, expecting the data to come from the cache
    result, calls = get_cached_data(key, _simple_data_fn, mocker)
    assert result == expected_result
    assert calls == 0


def test_cached_data_cache_invalided_on_key_change(mocker: MockFixture):
    key = dict(version=1)
    expected_result = _simple_data_fn(key)

    # Run once, expecting the data to be generated
    result, calls = get_cached_data(key, _simple_data_fn, mocker)
    assert result == expected_result
    assert calls == 1

    # Modify the key, therefore invalidating the cache
    key['version'] = 2
    expected_new_result = _simple_data_fn(key)
    assert expected_result != expected_new_result  # for test validity

    # Run again, expecting the data to be generated once again
    result, calls = get_cached_data(key, _simple_data_fn, mocker)
    assert result == expected_new_result
    assert calls == 1


def test_cached_data_allow_force_regerenate(mocker: MockFixture):
    key = dict(version=1)
    expected_result = _simple_data_fn(key)

    # Run once, expecting the data to be generated
    result, calls = get_cached_data(key, _simple_data_fn, mocker)
    assert result == expected_result
    assert calls == 1

    # Run again with the flag, expecting the data to be generated again
    result, calls = get_cached_data(key, _simple_data_fn, mocker, force=True)
    assert result == expected_result
    assert calls == 1


def _simple_data_fn(key):
    return str(key) * 10
