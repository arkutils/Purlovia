from typing import List, Optional, Tuple

import pytest
from pydantic import BaseModel


class MinMaxRange(BaseModel):
    __root__: Tuple[float, float]

    class Config:
        title = "Range (min, max)"


class LootCrate(BaseModel):
    levelReq: Optional[MinMaxRange]

    class Config:
        title = "A loot crate"


class Container(BaseModel):
    loots: List[LootCrate]


def test_to_json():
    rng = MinMaxRange(__root__=(1, 2))
    assert rng.json() == '[1.0, 2.0]'


@pytest.mark.xfail(
    reason="pydantic is currently broken for embedded non-dict BaseModels: https://github.com/samuelcolvin/pydantic/issues/1287")
def test_to_json_embedded():
    rng = MinMaxRange(__root__=(1, 2))
    crate = LootCrate(levelReq=rng)
    assert crate.json() == '{"levelReq": [1.0, 2.0]}'


def test_fetching_list_subtype():
    '''We rely on some internal pydantic fields - test that still works.'''
    assert hasattr(Container, '__fields__')
    assert 'loots' in Container.__fields__
    field = Container.__fields__['loots']
    assert hasattr(field, 'outer_type_')
    assert hasattr(field, 'type_')
    assert field.outer_type_ == List[LootCrate]
    assert field.type_ == LootCrate
