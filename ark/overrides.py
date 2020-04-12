import re
from collections.abc import MutableMapping as Map
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import *

import yaml
from pydantic import BaseModel

__all__ = [
    'ColorRegionSettings',
    'OverrideSettings',
    'OverridesFile',
    'get_overrides_for_species',
    'get_overrides_for_map',
    'get_overrides_for_mod',
    'get_overrides_global',
    'any_regexes_match',
]

OVERRIDE_FILENAME = 'config/overrides.yaml'


class ColorRegionSettings(BaseModel):
    capitalize: Optional[bool] = None
    default_name: Optional[str] = None
    nullify_name_regexes: Dict[str, str] = dict()
    useless_name_regexes: Dict[str, str] = dict()
    region_names: Dict[int, Optional[str]] = dict()


class MapBoundariesSettings(BaseModel):
    border_top: float = 7.2
    border_left: float = 7.2
    border_right: float = 92.8
    border_bottom: float = 92.8


class OverrideSettings(BaseModel):
    skip_export: Optional[bool] = False

    # Variants, currently only applying to species
    add_variants: Dict[str, bool] = dict()
    remove_variants: Dict[str, bool] = dict()
    variant_renames: Dict[str, str] = dict()
    classname_variant_parts: Dict[str, bool] = dict()
    pathname_variant_parts: Dict[str, bool] = dict()
    variants_to_skip_export: Dict[str, bool] = dict()
    variants_to_skip_export_asb: Dict[str, bool] = dict()
    variants_to_remove_name_parts: Dict[str, str] = dict()

    # Species
    color_regions: ColorRegionSettings = ColorRegionSettings()
    descriptive_name: Optional[str]

    # Maps
    svgs: MapBoundariesSettings = MapBoundariesSettings()


class OverridesFile(BaseModel):
    defaults: OverrideSettings = OverrideSettings()
    mods: Dict[str, OverrideSettings] = dict()
    species: Dict[str, OverrideSettings] = dict()
    maps: Dict[str, OverrideSettings] = dict()


DEFAULT_COLORREGIONSETTINGS = ColorRegionSettings(
    capitalize=True,
    default_name='Unknown',
).dict(exclude_unset=True)

DEFAULT_OVERRIDES = OverridesFile(
    defaults=OverrideSettings(**DEFAULT_COLORREGIONSETTINGS),
    mods=dict(),
    species=dict(),
    maps=dict(),
).dict(exclude_unset=True)


@lru_cache()
def _load_overrides() -> OverridesFile:
    with open(OVERRIDE_FILENAME) as f:
        raw_data = yaml.safe_load(f)

    data = OverridesFile(**raw_data)
    return data


@lru_cache(maxsize=1)
def _get_overrides_global_dict() -> Dict:
    config_file = _load_overrides()
    settings: Dict[str, Any] = dict()
    nested_update(settings, DEFAULT_OVERRIDES)
    nested_update(settings, config_file.defaults.dict(exclude_unset=True))
    return settings


@lru_cache(maxsize=1)
def get_overrides_global() -> OverrideSettings:
    settings = _get_overrides_global_dict()
    return OverrideSettings(**settings)


@lru_cache(maxsize=10)
def _get_overrides_for_mod_dict(modid: str) -> Dict:
    modid = modid or ''
    config_file = _load_overrides()
    settings: Dict[str, Any] = dict()
    nested_update(settings, _get_overrides_global_dict())
    nested_update(settings, config_file.mods.get(modid, OverrideSettings()).dict(exclude_unset=True))
    return settings


@lru_cache(maxsize=10)
def get_overrides_for_mod(modid: str) -> OverrideSettings:
    modid = modid or ''
    settings: Dict[str, Any] = dict()
    nested_update(settings, _get_overrides_for_mod_dict(modid))
    return OverrideSettings(**settings)


@lru_cache(maxsize=100)
def _get_overrides_for_species_dict(species: str, modid: str) -> Dict:
    modid = modid or ''
    config_file = _load_overrides()
    settings: Dict[str, Any] = dict()
    nested_update(settings, _get_overrides_for_mod_dict(modid))
    nested_update(settings, config_file.species.get(species, OverrideSettings()).dict(exclude_unset=True))
    return settings


@lru_cache(maxsize=1024)
def get_overrides_for_species(species: str, modid: str) -> OverrideSettings:
    settings = _get_overrides_for_species_dict(species, modid)
    return OverrideSettings(**settings)


@lru_cache(maxsize=16)
def _get_overrides_for_map_dict(map_asset: str, modid: str) -> Dict:
    modid = modid or ''
    config_file = _load_overrides()
    settings: Dict[str, Any] = dict()
    nested_update(settings, _get_overrides_for_mod_dict(modid))
    nested_update(settings, config_file.maps.get(map_asset, OverrideSettings()).dict(exclude_unset=True))
    return settings


@lru_cache(maxsize=128)
def get_overrides_for_map(map: str, modid: str) -> OverrideSettings:
    settings = _get_overrides_for_map_dict(map, modid)
    return OverrideSettings(**settings)


def any_regexes_match(source: Union[Dict[str, str], List[str]], target: str, flags: int = re.I):
    regexes: Iterable[str] = source.values() if isinstance(source, Map) else source
    for search in regexes:
        if search and re.match(search, target, flags):
            return True

    return False


def nested_update(d, v):
    for key in v:
        if key in d and isinstance(d[key], Map) and isinstance(v[key], Map):
            nested_update(d[key], v[key])
        else:
            d[key] = deepcopy(v[key])
    return d
