from collections import defaultdict

from ue.asset import UAsset
from ue.utils import get_clean_name


def gather_properties(asset: UAsset, props=None):
    if props is None:
        props = defaultdict(lambda: defaultdict(lambda: list()))

    # Gather content from parent class
    parentpkgname = asset.findParentPackageForExport(asset.default_export)
    if parentpkgname and not parentpkgname.strip('/').lower().startswith('script'):
        parentpkg = asset.loader[parentpkgname]
        gather_properties(parentpkg, props)

    # Gather content from sub-components first so we can override later
    for subpkgname in asset.findSubComponents():
        subpkg = asset.loader[subpkgname]
        gather_properties(subpkg, props)

    if not asset.default_export or not asset.default_export.properties:
        return

    # Insert another entry into props for each property here
    for prop in asset.default_export.properties.values:
        propname = get_clean_name(prop.header.name)
        propindex = prop.header.index or 0
        props[propname][propindex].append(prop.value)

    return props


def clean_value(value, fallback=None):
    if value is None or isinstance(value, (int, str, bool)):
        return value
    if isinstance(value, float) and value == int(value):
        return int(value)
    if isinstance(value, float):
        return value
    if value.__class__.__name__ == 'FloatProperty':
        return clean_value(value.rounded_value)
    if value.__class__.__name__ in ('StringProperty', 'NameIndex'):
        return get_clean_name(value)
    if value.__class__.__name__ in ('ByteProperty', 'IntProperty', 'BoolProperty'):
        return value.value
    if fallback:
        return fallback
    raise ValueError("Don't know how to handle a " + value.__class__.__name__)


def clean_value_str(value, fallback=None):
    if value is None or isinstance(value, (int, str, bool)):
        return str(value)
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    if isinstance(value, float):
        return str(value)
    if value.__class__.__name__ == 'FloatProperty':
        return clean_value_str(value.rounded_value)
    if value.__class__.__name__ in ('StringProperty', 'NameIndex'):
        return get_clean_name(value)
    if value.__class__.__name__ in ('ByteProperty', 'IntProperty', 'BoolProperty'):
        return str(value.value)
    if fallback:
        return fallback
    raise ValueError("Don't know how to handle a " + value.__class__.__name__)


def stat_value(props, name, index, fallback):
    values = props[name][index]
    if values:
        return clean_value(values[-1])
    if isinstance(fallback, (list, tuple)):
        fallback = fallback[index]
    return clean_value(fallback)


def flatten(props):
    result = dict((pk, dict((ik, iv[-1]) for ik, iv in pv.items())) for pk, pv in props.items())
    return result


def flatten_to_strings(props):
    result = dict((pk, dict((ik, clean_value_str(iv[-1], '<snip>')) for ik, iv in pv.items())) for pk, pv in props.items())
    return result
