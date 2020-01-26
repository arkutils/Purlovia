import json
from typing import Optional

from ue.base import UEBase

__all__ = [
    'get_clean_namespaced_name',
    'get_clean_name',
    'get_property',
    'property_serialiser',
    'sanitise_output',
    'clean_float',
    'clean_double',
]


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


def property_serialiser(obj):
    if hasattr(obj, 'format_for_json'):
        return obj.format_for_json()

    if isinstance(obj, UEBase):
        return str(obj)

    return json._default_encoder.default(obj)  # pylint: disable=protected-access


def sanitise_output(data):
    '''
    Prepare data for output as JSON, removing references to the UE tree so they can be freed.
    '''
    # Convert anything with a format_for_json method
    fmt = getattr(data, 'format_for_json', None)
    if fmt:
        data = fmt()

    if isinstance(data, UEBase):
        raise TypeError("Found UEBase item in output data without conversion method")

    # Recurse into dicts
    if isinstance(data, dict):
        return {k: sanitise_output(v) for k, v in data.items()}

    # Recurse into list-likes
    if isinstance(data, (list, tuple)):
        return [sanitise_output(v) for v in data]

    return data


def clean_float(value):
    '''Round to 7 significant figures. Should be used for outputting all single-precision float data.'''
    if value is None:
        return None
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
    value = float(format(value, '.9g'))
    int_value = int(value)
    if value == int_value:
        return int_value
    else:
        return value
