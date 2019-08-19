from typing import *

import pytest

from .proxy import UEProxyStructure, proxy_for_type, ueints

# pylint: disable=singleton-comparison  # to ignore `var == False`
# pylint: disable=redefined-outer-name  # to allow fixture use


@pytest.fixture
def simple_proxy():
    class SimpleProxy(UEProxyStructure, uetype="DummyType1"):
        IntField = ueints(90032221)

    proxy: SimpleProxy = proxy_for_type('DummyType1')
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


def test_has_override(simple_proxy):
    class Proxy1(UEProxyStructure, uetype="DummyType1"):
        IntField = ueints(90032221)

    simple_proxy: Proxy1 = proxy_for_type('DummyType1')

    assert simple_proxy.has_override('IntField', 0) == False
    assert simple_proxy.has_override('IntField', 1) == False

    simple_proxy.update({'IntField': ueints(3141)})

    assert simple_proxy.has_override('IntField', 0) == True
    assert simple_proxy.has_override('IntField', 1) == False


def test_unspecified_fields(simple_proxy):
    class Proxy1(UEProxyStructure, uetype="DummyType1"):
        IntField = ueints(90032221)

    simple_proxy: Proxy1 = proxy_for_type('DummyType1')

    assert simple_proxy.has_override('IntField', 0) == False
    assert simple_proxy.has_override('OtherField', 0) == False

    simple_proxy.update({'OtherField': ueints(3141)})

    assert simple_proxy.has_override('OtherField', 0) == True
    assert simple_proxy.has_override('IntField', 1) == False
