from typing import List, Optional, Tuple

import pytest
from pydantic import BaseModel, Field

from ue.properties import BoolProperty, FloatProperty, IntProperty, NameProperty, StringProperty
from ue.utils import sanitise_output


class TypedModel(BaseModel):
    str_field: Optional[str]
    int_field: Optional[int]
    bool_field: Optional[bool]
    float_field: Optional[float]

    class Config:
        extras = 'forbid'
        # arbitrary_types_allowed = True


def test_float_fields():
    '''Ensure FloatProperty can be used in `float` typed fields.'''
    model = TypedModel()
    value = FloatProperty.create(2.0)
    model.float_field = value
    output = model.dict()
    assert type(output['float_field']) == FloatProperty


def test_int_fields():
    '''Ensure IntProperty can be used in `int` typed fields.'''
    model = TypedModel()
    value = IntProperty.create(200)
    model.int_field = value
    output = model.dict()
    assert type(output['int_field']) == IntProperty


def test_bool_fields():
    '''Ensure BoolProperty can be used in `bool` typed fields.'''
    model = TypedModel()
    value = BoolProperty.create(True)
    model.bool_field = value
    output = model.dict()
    assert type(output['bool_field']) == BoolProperty


def test_str_fields():
    '''Ensure StringProperty can be used in `str` typed fields.'''
    model = TypedModel()
    value = StringProperty.create("stringy")
    model.str_field = value
    output = model.dict()
    assert type(output['str_field']) == StringProperty


def test_sanitising_float():
    '''Ensure UE values in models are converted properly for export.'''
    model = TypedModel()
    model.float_field = FloatProperty.create(1.0000001)
    result = sanitise_output(model.dict())
    assert result['float_field'] == 1.0
