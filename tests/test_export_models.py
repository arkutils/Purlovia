import math
import operator
from numbers import Number, Real
from typing import Any, Dict, List, Optional, Tuple

import pytest
from pydantic import BaseModel, Field, ValidationError

from ue.properties import BoolProperty, FloatProperty, IntProperty, StringProperty
from ue.utils import clean_float, sanitise_output

# pylint: disable=unidiomatic-typecheck  # this form is correct for testing


class UETypedModel(BaseModel):
    str_prop_field: Optional[StringProperty]
    int_prop_field: Optional[IntProperty]
    bool_prop_field: Optional[BoolProperty]
    float_prop_field: Optional[FloatProperty]

    str_field: Optional[str]
    int_field: Optional[int]
    bool_field: Optional[bool]
    float_field: Optional[float]

    class Config:
        validate_assignment = True


TEST_PROP_PARAMS = [
    (StringProperty, "str_prop_field", "abc", "abc"),
    (IntProperty, "int_prop_field", 123, 123),
    (BoolProperty, "bool_prop_field", True, True),
    (FloatProperty, "float_prop_field", 1, 1),
    (FloatProperty, "float_prop_field", 1.000001, 1.000001),
    (FloatProperty, "float_prop_field", 1.0000001, 1.0),
]


@pytest.mark.parametrize("field_type,field_name,value,target", TEST_PROP_PARAMS)
def test_field_prop_as_attr(field_type, field_name, value, target):
    '''
    Ensure UE values in models are accepted and converted
    correctly, when set after creation.'''
    # Setup
    model = UETypedModel()
    create_fn = getattr(field_type, 'create')
    field_value = create_fn(value)

    # Set the model's field
    setattr(model, field_name, field_value)
    assert getattr(model, field_name) is field_value

    # Convert model to dict, verify field is untouched
    output = model.dict()
    assert output[field_name] is field_value

    # Sanitise model, verify field is converted as expected
    result = sanitise_output(output)
    field_result = result[field_name]
    assert field_result == target


@pytest.mark.parametrize("field_type,field_name,value,target", TEST_PROP_PARAMS)
def test_field_prop_in_constructor(field_type, field_name, value, target):
    '''
    Ensure UE values in models are accepted and converted
    correctly, when set in the constructor.
    '''
    # Setup
    create_fn = getattr(field_type, 'create')
    field_value = create_fn(value)
    kwargs = {field_name: field_value}

    # Create model with field in constructor
    model = UETypedModel(**kwargs)

    # Convert model to dict, verify field is untouched
    output = model.dict()
    assert output[field_name] is field_value

    # Sanitise model, verify field is converted as expected
    result = sanitise_output(output)
    field_result = result[field_name]
    assert field_result == target


@pytest.mark.parametrize("field_name,schema_type", [
    ("str_prop_field", "string"),
    ("int_prop_field", "integer"),
    ("bool_prop_field", "boolean"),
    ("float_prop_field", "number"),
])
def test_scheme_output(field_name, schema_type):
    '''Ensure the UE types have schema output support.'''
    schema = UETypedModel.schema()
    assert schema['properties'][field_name]['type'] == schema_type


def test_props_in_plain_fields():
    v = FloatProperty.create(1.0000001)

    # put it in the non-property field
    with pytest.raises(ValidationError):
        model = UETypedModel()
        model.float_field = v

    # put it in the constructor
    with pytest.raises(ValidationError):
        model = UETypedModel(float_field = v)


def test_plain_values_in_prop_fields():
    v = 1.0000001

    # put it in the property field
    with pytest.raises(ValidationError):
        model = UETypedModel()
        model.float_prop_field = v

    # put it in the constructor
    with pytest.raises(ValidationError):
        model = UETypedModel(float_prop_field = v)
