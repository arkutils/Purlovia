import os
import struct
from copy import deepcopy
from functools import reduce
from collections import defaultdict
from types import SimpleNamespace as Bag

from dict_utils import merge

import hexutils, uasset

_asset_basepath = None
_loaded_assets = {}

__all__ = [
    'get_asset',
    'wipe_assets',
    'ensure_dependencies',
    'load_raw_asset_from_file',
    'load_and_parse_file',
    'load_raw_asset',
]


def load_config():
    import configparser
    config = configparser.ConfigParser()
    config.read('user.ini')
    config['parser']['assetpath'] = '.'
    config.read('user.ini')
    asset_path = config['parser']['assetpath']
    print("Using asset path: " + asset_path)
    set_asset_path(asset_path)


def set_asset_path(basepath):
    global _asset_basepath
    _asset_basepath = basepath


def clean_asset_name(name):
    name = name.strip().replace('\\', '/')
    name = name.strip('/')
    if name.lower().endswith('.uasset'): name = name[:-7]
    name = name.strip('/')
    return name


def convert_asset_name_to_path(name):
    name = clean_asset_name(name)
    parts = name.split('/')
    if parts[0].lower() == 'game': parts[0] = 'Content'
    fullname = os.path.join(_asset_basepath, *parts) + '.uasset'
    return fullname


def load_raw_asset_from_file(filename):
    print("Loading file:", filename)
    if not os.path.isabs(filename):
        filename = os.path.join(_asset_basepath, filename)
    mem = hexutils.load_file_into_memory(filename)
    return mem


def load_raw_asset(name):
    name = clean_asset_name(name)
    print("Loading asset:", name)
    filename = convert_asset_name_to_path(name)
    mem = hexutils.load_file_into_memory(filename)
    return mem


def load_and_parse_file(filename):
    mem = load_raw_asset_from_file(filename)
    asset = uasset.decode_asset(mem)
    return asset


def get_asset(name):
    name = clean_asset_name(name)
    try:
        return _loaded_assets[name]
    except KeyError:
        pass

    mem = load_raw_asset(name)
    asset = uasset.decode_asset(mem)
    asset.name = name
    _loaded_assets[name] = asset
    return asset


def wipe_assets():
    global _loaded_assets
    _loaded_assets.clear()


def ensure_dependencies(asset):
    parent_name = uasset.find_external_source_of_export(asset, asset.default_export)
    if parent_name and 'UObject' not in parent_name:
        parent = get_asset(parent_name)
        ensure_dependencies(parent)


def merged_properties(asset):
    classes = [asset]
    while True:
        parent_name = uasset.find_external_source_of_export(asset, asset.default_export)
        if not parent_name or 'UObject' in parent_name:
            break
        parent = get_asset(parent_name)
        classes.append(parent)
        asset = parent

    combined_props = {}
    for cls in reversed(classes):
        merge(combined_props, cls.props)

    return combined_props


# This happens once when the module is first loaded
load_config()
