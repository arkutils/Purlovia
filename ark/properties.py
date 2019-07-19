from collections import defaultdict
from typing import Dict, List, Optional, Tuple

import ark.asset
import ark.tree
from ark.tree import inherits_from
from ue.asset import ExportTableItem, UAsset
from ue.coretypes import UEBase
from ue.utils import get_clean_name, get_property

from .common import *

PriorityPropDict = Dict[str, Dict[int, List[UEBase]]]


def extract_properties_from_export(export, props: PriorityPropDict, recurse=False):
    '''Restricted version of gather_properties that only act on a single export (and optionally its parents).'''
    if recurse:
        parent = ark.tree.get_parent_of_export(export)
        if parent:
            extract_properties_from_export(parent, props, recurse=recurse)

    for prop in export.properties.values:
        propname = get_clean_name(prop.header.name)
        if propname:
            propindex = prop.header.index or 0
            props[propname][propindex].append(prop.value)


def gather_properties(asset: UAsset, props: Optional[PriorityPropDict] = None, report=False):
    assert asset and asset.loader

    dcscs: List[Tuple[int, ExportTableItem]] = list()
    the_dcsc = asset.loader.load_class(DCSC_CLS)
    props = props or defaultdict(lambda: defaultdict(list))

    if report: print('\nGathering props from hierarchy (skipping DCSCs):')
    gather_properties_internal(asset, props, dcscs, the_dcsc, report=report, depth=0)

    # Order the DCSCs by CharacterStatusComponentPriority value, descending
    # Python's sort is stable, so it will maintain the gathered order of exports with identical priorities (e.g. Deinonychus)
    dcscs.sort(key=lambda p: -p[0])

    if report: print('\nApplying ordered DCSCs:')
    for pri, export in reversed(dcscs):
        if report: print(f'DCSC pri={pri} {export.fullname}')
        extract_properties_from_export(export, props, recurse=True)

    return props


def gather_properties_internal(asset: UAsset,
                               props: PriorityPropDict,
                               dcscs: List[Tuple[int, ExportTableItem]],
                               dcsc,
                               report=False,
                               depth=0):
    assert asset and asset.loader
    if report:
        indent = '|   ' * depth
        print(indent + asset.name)

    parent = ark.tree.get_parent_of_export(asset.default_class)
    if parent and parent.asset.assetname != asset.assetname and not ark.tree.export_inherits_from(parent, dcsc):
        # Recurse upwards before collecting properties on the way back down
        parentpkg = parent.asset
        gather_properties_internal(parentpkg, props, dcscs, dcsc, report=report, depth=depth + 1)

    if report: print(f'{indent}gathering props from {asset.default_export and asset.default_export.fullname}')
    extract_properties_from_export(asset.default_export, props)

    # Gather properties from sub-components
    for subcomponent in ark.asset.findSubComponentExports(asset):
        if report: print(f'{indent}|   subcomponent: {subcomponent.fullname}')
        if ark.tree.export_inherits_from(subcomponent, dcsc):
            pri = int(clean_value(get_property(subcomponent, "CharacterStatusComponentPriority") or 0))
            if report: print(f'{indent}|   (postponing dcsc: priority={pri})')
            dcscs.append((pri, subcomponent))
        else:
            if report: print(f'{indent}|   (gather properties)')
            extract_properties_from_export(subcomponent, props)

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
    if value.__class__.__name__ in ('StringProperty', 'NameIndex', 'NameProperty'):
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
    if value.__class__.__name__ in ('StringProperty', 'NameIndex', 'NameProperty'):
        return get_clean_name(value)
    if value.__class__.__name__ in ('ByteProperty', 'IntProperty', 'BoolProperty'):
        return str(value.value)
    if fallback:
        return fallback
    raise ValueError("Don't know how to handle a " + value.__class__.__name__)


def stat_value(props, name, index, fallback=None):
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
