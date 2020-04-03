import re
from typing import List, Optional, Set, Tuple

from .overrides import OverrideSettings
from .types import PrimalDinoCharacter

__all__ = [
    'get_variants_from_species',
    'get_variants_from_assetname',
    'should_skip_from_variants',
    'adjust_name_from_variants',
]


def _gather_mission_variants(bp: str, variants: Set[str]):
    '''Decode Genesis-like mission variants, which contain mission type and optional biome type.'''

    # Both mission type and biome type
    match = re.search(r'/MissionVariants/(\w+?)/(\w+?)/', bp)
    if match:
        variants.add(match[1])
        variants.add(match[2])
        return

    # Just mission type
    match = re.search(r'/MissionVariants/(\w+?)/', bp)
    if match:
        variants.add(match[1])


def _gather_biome_variants(bp: str, variants: Set[str]):
    '''Decode Genesis-like biome variants.'''

    # Normal form
    match = re.search(r'/BiomeVariants/(\w+?)_', bp)
    if match:
        variants.add(match[1])
        return

    # Messy form
    match = re.search(r'/BiomeVariants/(?P<name>[^/_.]+)\w*/(?P=name)', bp)
    if match:
        variants.add(match['name'])


def adjust_name_from_variants(name: str, variants: set, overrides: OverrideSettings) -> str:
    for part, target in overrides.variants_to_remove_name_parts.items():
        if part in variants:
            idx = name.find(target)
            if idx >= 0:
                name = name[:idx] + name[idx + len(target):]

    return name


def get_variants_from_species(char: PrimalDinoCharacter) -> Set[str]:
    variants: Set[str] = set()

    # Handle basic features
    if char.bIsBossDino[0]:
        variants.add('Boss')
    if char.bIsCorrupted[0]:
        variants.add('Corrupted')

    return variants


def get_variants_from_assetname(assetname: str, overrides: OverrideSettings) -> Set[str]:
    cls: str = assetname.split('/')[-1]
    variants: Set[str] = set()

    # Handle Genesis-like missions and biomes
    _gather_mission_variants(assetname, variants)
    _gather_biome_variants(assetname, variants)

    # Search for variants from overrides
    cls_ = '_' + cls + '_'
    for name, use in overrides.classname_variant_parts.items():
        if use and ('_' + name in cls_ or name + '_' in cls_):
            variants.add(name)

    # Search for variants within the full assetname
    path_ = assetname[:assetname.rfind('/')].replace('/', '_')
    for name, use in overrides.pathname_variant_parts.items():
        if use and ('_' + name in path_ or name + '_' in path_):
            variants.add(name)

    # Additions from overrides
    for name, use in overrides.add_variants.items():
        if use:
            variants.add(name)

    # Removals from overrides
    for name, use in overrides.remove_variants.items():
        if use and name in variants:
            variants.remove(name)

    # And renames from overrides, last
    for old_name, new_name in overrides.variant_renames.items():
        if old_name in variants:
            variants.remove(old_name)
            variants.add(new_name)

    return variants


def should_skip_from_variants(variants: Set[str], overrides: OverrideSettings) -> bool:
    skip_variants = set(name for name, use in overrides.variants_to_skip_export.items() if use)
    return bool(variants & skip_variants)
