from pathlib import Path
from typing import Callable, List, Tuple

import pytest

from ue.loader import AssetLoader

from .common import MockCacheManager, MockModResolver

DATA_PATH = str(Path(__file__).parent / 'data' / 'loader_find_assetnames')

DATA_FILES = ['/top1', '/a/a1', '/b/b1', '/b/b2', '/b/ba/ba1', '/b/ba/ba2']


@pytest.fixture(name='simple_loader', scope='module')
def fixture_simple_loader() -> AssetLoader:
    loader = AssetLoader(
        assetpath=DATA_PATH,
        modresolver=MockModResolver(),
        cache_manager=MockCacheManager(),
        rewrites={},
        mod_aliases={},
    )
    return loader


def filter_names(predicate: Callable[[str], bool]) -> Tuple[List[str], List[str]]:
    normal = [name for name in DATA_FILES if predicate(name)]
    inverted = [name for name in DATA_FILES if not predicate(name)]
    return (normal, inverted)


def gather_results(loader: AssetLoader, path: str, **kwargs) -> Tuple[List[str], List[str]]:
    kwargs.setdefault('extension', ['.txt'])
    if 'invert' in kwargs:
        raise ValueError('invert cannot appear in kwargs')
    normal = list(loader.find_assetnames(path, **kwargs))
    inverted = list(loader.find_assetnames(path, **kwargs, invert=True))
    return (normal, inverted)


def test_find_assetnames_all(simple_loader: AssetLoader):
    result_normal, result_inverted = gather_results(simple_loader, '/')
    expected_normal, expected_inverted = filter_names(lambda path: True)
    assert result_normal == expected_normal
    assert result_inverted == expected_inverted


def test_find_assetnames_in_a(simple_loader: AssetLoader):
    result_normal, result_inverted = gather_results(simple_loader, '/a')
    expected_normal, expected_inverted = filter_names(lambda path: path.startswith('/a/'))
    assert result_normal == expected_normal
    assert result_inverted == []  # because custom path


def test_find_assetnames_excluding_b(simple_loader: AssetLoader):
    result_normal, result_inverted = gather_results(simple_loader, '/', exclude=['/b/.*'])
    expected_normal, expected_inverted = filter_names(lambda path: not path.startswith('/b/'))
    assert result_normal == expected_normal
    assert result_inverted == expected_inverted


def test_find_assetnames_excluding_b_force_include_ba(simple_loader: AssetLoader):
    result_normal, result_inverted = gather_results(simple_loader, '/', include=['/b/ba/.*'], exclude=['/b/.*'])
    expected_normal, expected_inverted = filter_names(lambda path: path.startswith('/b/ba') or not path.startswith('/b/'))
    assert result_normal == expected_normal
    assert result_inverted == expected_inverted


def test_find_assetnames_excluding_all_force_include_ba(simple_loader: AssetLoader):
    result_normal, result_inverted = gather_results(simple_loader, '/', include=['/b/ba/.*'], exclude=['.*'])
    expected_normal, expected_inverted = filter_names(lambda path: path.startswith('/b/ba'))
    assert result_normal == expected_normal
    assert result_inverted == expected_inverted
