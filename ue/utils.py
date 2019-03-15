from ue.base import UEBase


def get_clean_namespaced_name(ns: UEBase, name: UEBase) -> str:
    ns = get_clean_name(ns, None)
    name = get_clean_name(name, '<unknown>')
    if ns:
        return f'{ns}::{name}'

    return name


def get_clean_name(obj: UEBase, fallback: str = None) -> str:
    if obj is None:
        return fallback
    elif obj.__class__.__name__ in ('NameIndex', 'StringProperty'):
        value = str(obj)
        return fallback if value == 'None' else value
    elif obj.__class__.__name__ in ('ObjectIndex', 'ObjectProperty'):
        return get_clean_name(obj.value, fallback)
    elif obj.__class__.__name__ in ('ImportTableItem', 'ExportTableItem'):
        return get_clean_name(obj.name, fallback)

    return fallback


def get_property(export, name) -> UEBase:
    for prop in export.properties:
        if str(prop.header.name) == name:
            return prop.value

    return None
