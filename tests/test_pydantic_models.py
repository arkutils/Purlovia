from typing import Optional, Tuple

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


def test_to_json():
    rng = MinMaxRange(__root__=(1, 2))
    assert rng.json() == '[1.0, 2.0]'


@pytest.mark.xfail(
    reason="pydantic is currently broken for embedded non-dict BaseModels: https://github.com/samuelcolvin/pydantic/issues/1287")
def test_to_json_embedded():
    rng = MinMaxRange(__root__=(1, 2))
    crate = LootCrate(levelReq=rng)
    assert crate.json() == '{"levelReq": [1.0, 2.0]}'
