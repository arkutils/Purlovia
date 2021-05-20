from math import isinf
from typing import Optional

from ue.base import UEBase

try:
    from pydantic import BaseModel
    have_pydantic = True
except ImportError:
    have_pydantic = False

__all__ = [
    'get_leaf_from_assetname',
    'get_clean_namespaced_name',
    'get_clean_name',
    'get_property',
    'sanitise_output',
    'clean_float',
    'clean_double',
]


def get_leaf_from_assetname(name: str) -> str:
    # Remove class name, if present
    if '.' in name:
        name = name[:name.index('.')]

    return name[name.rfind('/') + 1:]


def get_assetpath_from_assetname(assetname: str) -> str:
    return assetname[:assetname.rfind('/')]


def get_clean_namespaced_name(ns: UEBase, name: UEBase) -> str:
    ns_str = get_clean_name(ns, None)
    name_str = get_clean_name(name, '<unknown>')
    if ns_str:
        return f'{ns_str}::{name_str}'

    return name_str  # type: ignore


def get_clean_name(obj: UEBase, fallback: str = None) -> Optional[str]:
    if obj is None:
        return fallback
    elif obj.__class__.__name__ in ('NameIndex', 'StringProperty', 'NameProperty'):
        value = str(obj).strip()
        return fallback if value == 'None' else value
    elif obj.__class__.__name__ in ('ObjectIndex', 'ObjectProperty'):
        return get_clean_name(obj.value, fallback)
    elif obj.__class__.__name__ in ('ImportTableItem', 'ExportTableItem'):
        return get_clean_name(obj.name, fallback)

    return fallback


def get_property(export, name) -> Optional[UEBase]:
    for prop in export.properties:
        if str(prop.header.name) == name:
            return prop.value

    return None


def sanitise_output(node):
    '''
    Prepare data for output as JSON, removing references to the UE tree so they can be freed.
    '''
    if node is None:
        return None

    if isinstance(node, (int, str)):
        return node

    if isinstance(node, float):
        return clean_double(node)

    format_for_json = getattr(node, 'format_for_json', None)
    if format_for_json:
        return sanitise_output(format_for_json())

    if have_pydantic and isinstance(node, BaseModel):
        return sanitise_output(node.dict(exclude_defaults=True, by_alias=True))

    skip_level_name = getattr(node, 'skip_level_field', None)
    if skip_level_name:
        sub_node = node.field_values.get(skip_level_name, None)
        if sub_node is not None:
            return sanitise_output(sub_node)

    if isinstance(node, UEBase):
        fields = getattr(node, 'field_order', None) or node.field_values.keys()
        return {name: sanitise_output(node.field_values[name]) for name in fields}

    if isinstance(node, (list, tuple)):
        return [sanitise_output(value) for value in node]

    if isinstance(node, dict):
        return {sanitise_output(k): sanitise_output(v) for k, v in node.items()}

    raise TypeError(f"Unexpected node type {type(node)}")


def clean_float(value):
    '''Round to 7 significant figures. Should be used for outputting all single-precision float data.'''
    if value is None:
        return None
    if isinf(value):
        return value
    value = float(format(value, '.7g'))
    int_value = int(value)
    if value == int_value:
        return int_value
    else:
        return value


def clean_double(value):
    '''Round to 9 significant figures. Should be used for outputting all double-precision float data.'''
    if value is None:
        return None
    if isinf(value):
        return value
    value = float(format(value, '.9g'))
    int_value = int(value)
    if value == int_value:
        return int_value
    else:
        return value
