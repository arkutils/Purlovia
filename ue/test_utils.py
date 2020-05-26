import pytest
from pydantic import BaseModel

from .properties import FloatProperty
from .utils import sanitise_output

# These make sense for testing
# pylint: disable=literal-comparison
# pylint: disable=unidiomatic-typecheck


class SubItem(BaseModel):
    c: FloatProperty


class Item(BaseModel):
    a: str
    b: SubItem


class Formattable:
    stuff: float

    def format_for_json(self):
        return self.stuff + 1


class Unformattable:
    stuff: float


@pytest.fixture(name="simple_model", scope="module")
def fixture_simple_model() -> Item:
    return Item(a='string', b=SubItem(c=FloatProperty.create(1.0)))


def test_sanitise_floats():
    assert sanitise_output(1.0) is 1
    assert sanitise_output(1.00000000001) is 1
    assert sanitise_output(1.0001) == pytest.approx(1.0001)

    assert sanitise_output([1.0]) == [1]
    assert sanitise_output({1.0: 2.0}) == {1: 2}


def test_sanitise_float_properties():
    assert sanitise_output(FloatProperty.create(1.0)) is 1
    assert sanitise_output(FloatProperty.create(1.00000000001)) is 1
    assert sanitise_output(FloatProperty.create(1.0001)) == pytest.approx(1.0001)

    assert sanitise_output([FloatProperty.create(1.0)]) == [1]
    assert sanitise_output({1.0: FloatProperty.create(2.0)}) == {1: 2}


def test_sanitise_models(simple_model: Item):
    output = sanitise_output(simple_model)
    assert output['a'] == 'string'
    assert output['b']['c'] is 1


def test_sanitise_formattable():
    f = Formattable()
    f.stuff = 1.0
    output = sanitise_output(f)
    assert output is 2


def test_sanitise_unformattable():
    f = Unformattable()
    f.stuff = 1.0
    with pytest.raises(TypeError):
        _ = sanitise_output(f)
