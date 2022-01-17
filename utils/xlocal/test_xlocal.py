from __future__ import with_statement

import pytest

from . import xlocal as xlocal_import


@pytest.fixture(name='xlocal')
def fixture_xlocal():
    return xlocal_import()


def test_scoping(xlocal):

    def f():
        assert xlocal.x == 3

    with xlocal(x=3):
        f()

    assert not hasattr(xlocal, 'x')
    pytest.raises(AttributeError, f)

    # Check no garbage left over
    assert not xlocal._storage  # pylint: disable=protected-access


def test_defaults():
    with_defaults = xlocal_import(x=1, y=2)
    assert with_defaults.x == 1 and with_defaults.y == 2

    with with_defaults(x=11):
        assert with_defaults.x == 11 and with_defaults.y == 2

    assert with_defaults.x == 1 and with_defaults.y == 2


def test_stacking(xlocal):
    with xlocal(x=5):
        assert xlocal.x == 5
        with xlocal(x=3):
            assert xlocal.x == 3
        assert xlocal.x == 5

    assert not hasattr(xlocal, 'x')


def test_is_immutable(xlocal):
    with xlocal(y=3):
        assert xlocal.y == 3
        pytest.raises(AttributeError, lambda: delattr(xlocal, 'y'))
        pytest.raises(AttributeError, lambda: setattr(xlocal, 'y', 4))

    assert not hasattr(xlocal, 'y')
    pytest.raises(AttributeError, lambda: setattr(xlocal, 'x', None))
    pytest.raises(AttributeError, lambda: setattr(xlocal, 'x', 5))


def test_undostack(xlocal):
    with xlocal(x=5):
        with xlocal(x=3, y=10):
            assert xlocal.x == 3 and xlocal.y == 10

            with xlocal(x=13, y=110):
                assert xlocal.x == 13 and xlocal.y == 110

            assert xlocal.x == 3 and xlocal.y == 10

            with xlocal(y=110, x=13):
                assert xlocal.x == 13 and xlocal.y == 110

            assert xlocal.x == 3 and xlocal.y == 10

        assert xlocal.x == 5 and not hasattr(xlocal, 'y')

        with xlocal(y=10, x=3):
            assert xlocal.x == 3 and xlocal.y == 10

            with xlocal(y=110, x=13):
                assert xlocal.x == 13 and xlocal.y == 110

            assert xlocal.x == 3 and xlocal.y == 10

            with xlocal(x=13, y=110):
                assert xlocal.x == 13 and xlocal.y == 110

            assert xlocal.x == 3 and xlocal.y == 10

        assert xlocal.x == 5 and not hasattr(xlocal, 'y')

    assert not hasattr(xlocal, 'x')
