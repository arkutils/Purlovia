from typing import Optional

from ue.base import UEBase


def get_clean_namespaced_name(ns: UEBase, name: UEBase) -> str:
    ns_str = get_clean_name(ns, None)
    name_str = get_clean_name(name, '<unknown>')
    if ns_str:
        return f'{ns_str}::{name_str}'

    return name_str  # type: ignore


def get_clean_name(obj: UEBase, fallback: str = None) -> Optional[str]:
    if obj is None:
        return fallback
    elif obj.__class__.__name__ in ('NameIndex', 'StringProperty'):
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
