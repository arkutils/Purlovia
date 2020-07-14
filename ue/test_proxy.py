from typing import Mapping, Optional

import pytest

from .proxy import UEProxyStructure, get_proxy_for_exact_type, ueints

# pylint: disable=singleton-comparison  # to ignore `var == False`
# pylint: disable=redefined-outer-name  # to allow fixture use


@pytest.fixture(name='simple_proxy')
def fixture_simple_proxy():
    class SimpleProxy(UEProxyStructure, uetype="DummyType1"):
        IntField = ueints(90032221)

    proxy: Optional[SimpleProxy] = get_proxy_for_exact_type('DummyType1')
    assert proxy
    return proxy


def test_define_class_without_uetype():
    with pytest.raises(TypeError, match="uetype"):

        class Proxy1(UEProxyStructure):  # pylint: disable=unused-variable
            pass


def test_define_empty_class():
    class Proxy1(UEProxyStructure, uetype="DummyType1"):  # pylint: disable=unused-variable
        pass


def test_define_class_with_types():
    class Proxy1(UEProxyStructure, uetype="DummyType1"):  # pylint: disable=unused-variable
        IntField: Mapping[int, float]


def test_define_class_with_data():
    class Proxy1(UEProxyStructure, uetype="DummyType1"):  # pylint: disable=unused-variable
        IntField = ueints(90032221)


def test_define_subclass_without_uetype():
    class Proxy1(UEProxyStructure, uetype="DummyType1"):  # pylint: disable=unused-variable
        pass

    with pytest.raises(TypeError, match="uetype"):

        class SubProxy1(Proxy1):  # pylint: disable=unused-variable
            pass


def test_define_subclass():
    class Proxy1(UEProxyStructure, uetype="DummyType1"):  # pylint: disable=unused-variable
        pass

    class SubProxy1(Proxy1, uetype="DummyType2"):  # pylint: disable=unused-variable
        pass


def test_simple_usage(simple_proxy):
    assert simple_proxy.IntField[0] == 90032221
    with pytest.raises(KeyError):
        _ = simple_proxy.IntField[1]

    simple_proxy.update({'IntField': ueints(3141)})
    assert simple_proxy.IntField[0] == 3141


def test_has_override():
    class Proxy1(UEProxyStructure, uetype="DummyType1"):
        IntField = ueints(90032221)

    proxy: Optional[Proxy1] = get_proxy_for_exact_type('DummyType1')

    assert proxy
    assert proxy.has_override('IntField', 0) is False
    assert proxy.has_override('IntField', 1) is False

    proxy.update({'IntField': ueints(3141)})

    assert proxy.has_override('IntField', 0) is True
    assert proxy.has_override('IntField', 1) is False


def test_unspecified_fields():
    class Proxy1(UEProxyStructure, uetype="DummyType1"):
        IntField = ueints(90032221)

    proxy: Optional[Proxy1] = get_proxy_for_exact_type('DummyType1')

    assert proxy
    assert proxy.has_override('IntField', 0) is False
    assert proxy.has_override('OtherField', 0) is False

    proxy.update({'OtherField': ueints(3141)})

    assert proxy.has_override('OtherField', 0) is True
    assert proxy.has_override('IntField', 1) is False
