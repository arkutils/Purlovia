from pathlib import Path

from tests.common import fixture_tempdir  # noqa: F401

from .cachefile import cache_data

EXTENSIONS = ('.hash', '.pickle')


def get_cached_data(key, _simple_data_fn, path: Path, name='data', force=False):
    global fn_calls
    fn_calls = 0
    result = cache_data(key, path / name, _simple_data_fn, force_regenerate=force)
    return (result, fn_calls)


def test_cached_data_generates_and_stores_data(tempdir: Path):
    key = dict(version=1)
    expected_result = _simple_data_fn(key)

    result, calls = get_cached_data(key, _simple_data_fn, tempdir)
    assert result == expected_result
    assert calls == 1

    # Ensure it generated the correct files
    assert (tempdir / 'data.hash').is_file()
    assert (tempdir / 'data.pickle').is_file()


def test_cached_data_fetches_from_cache(tempdir: Path):
    key = dict(version=1)
    expected_result = _simple_data_fn(key)

    # Run once, expecting the data to be generated
    result, calls = get_cached_data(key, _simple_data_fn, tempdir)
    assert result == expected_result
    assert calls == 1

    # Run again, expecting the data to come from the cache
    result, calls = get_cached_data(key, _simple_data_fn, tempdir)
    assert result == expected_result
    assert calls == 0


def test_cached_data_cache_invalided_on_key_change(tempdir: Path):
    key = dict(version=1)
    expected_result = _simple_data_fn(key)

    # Run once, expecting the data to be generated
    result, calls = get_cached_data(key, _simple_data_fn, tempdir)
    assert result == expected_result
    assert calls == 1

    # Modify the key, therefore invalidating the cache
    key['version'] = 2
    expected_new_result = _simple_data_fn(key)
    assert expected_result != expected_new_result  # for test validity

    # Run again, expecting the data to be generated once again
    result, calls = get_cached_data(key, _simple_data_fn, tempdir)
    assert result == expected_new_result
    assert calls == 1


def test_cached_data_allow_force_regerenate(tempdir: Path):
    key = dict(version=1)
    expected_result = _simple_data_fn(key)

    # Run once, expecting the data to be generated
    result, calls = get_cached_data(key, _simple_data_fn, tempdir)
    assert result == expected_result
    assert calls == 1

    # Run again with the flag, expecting the data to be generated again
    result, calls = get_cached_data(key, _simple_data_fn, tempdir, force=True)
    assert result == expected_result
    assert calls == 1


fn_calls = 0


def _simple_data_fn(key):
    global fn_calls
    fn_calls += 1
    print("Generation function called")
    return str(key) * 10
