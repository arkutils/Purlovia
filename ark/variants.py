import re
from typing import Set

from .overrides import OverrideSettings
from .types import PrimalDinoCharacter

__all__ = [
    'get_variants_from_species',
    'get_variants_from_assetname',
    'should_skip_from_variants',
    'adjust_name_from_variants',
]


def _gather_mission_variants(assetname: str, variants: Set[str]):
    '''Decode Genesis-like mission variants, which contain mission type and optional biome type.'''

    # Both mission type and biome type
    match = re.search(r'/MissionVariants/(\w+?)/(\w+?)/', assetname)
    if match:
        variants.add(match[1])
        variants.add(match[2])
        variants.add('Mission')
        return

    # Just mission type
    match = re.search(r'/MissionVariants/(\w+?)/', assetname)
    if match:
        variants.add(match[1])
        variants.add('Mission')

    # Genesis2 style
    match = re.search(r'/Missions(?:/ModularMission)?/(\w+?)/', assetname)
    if match:
        variants.add(match[1])
        variants.add('Mission')


def _gather_biome_variants(assetname: str, variants: Set[str]):
    '''Decode Genesis-like biome variants.'''

    # Gen 1 normal form
    match = re.search(r'/Genesis/.*/BiomeVariants/(\w+?)_', assetname)
    if match:
        variants.add(match[1])
        return

    # Gen 1 messy form
    match = re.search(r'/Genesis/.*?/BiomeVariants/(?P<name>[^/_.]+)\w*/(?P=name)', assetname)
    if match:
        variants.add(match['name'])

    # Gen 2 form
    match = re.search(r'/Genesis2/.*?/BiomeVariants/.+_(?P<name>[^/_.]+)$', assetname)
    if match:
        variants.add(match['name'])


def adjust_name_from_variants(name: str, variants: set, overrides: OverrideSettings) -> str:
    for part, target in overrides.variants_to_remove_name_parts.items():
        if part in variants:
            idx = name.find(target)
            if idx >= 0:
                name = name[:idx] + name[idx + len(target):]

    return name


def get_variants_from_species(char: PrimalDinoCharacter, assetname: str, overrides: OverrideSettings) -> Set[str]:
    variants = get_variants_from_assetname(assetname, overrides)

    # Handle flags
    for flag, target in overrides.variants_from_flags.items():
        if char.get(flag, 0, fallback=False):
            for label in target if isinstance(target, list) else [target]:
                variants.add(label)

    # Search for variants in the descriptive name using supplied regexes
    descriptive_name = str(char.DescriptiveName[0] or '')
    for part, target in overrides.name_variants.items():
        if re.match(part, descriptive_name, re.DOTALL):
            for label in target if isinstance(target, list) else [target]:
                variants.add(label)

    # Re-apply removals so they also apply to species names, etc
    for name, use in overrides.remove_variants.items():
        if use and name in variants:
            variants.remove(name)

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

    # Search for variants surrounded by underscores within the full assetname
    path_ = assetname[:assetname.rfind('/')].replace('/', '_')
    for name, use in overrides.pathname_variant_parts.items():
        if use and ('_' + name in path_ or name + '_' in path_):
            variants.add(name)

    # Search for variants as full path components within the full assetname
    for name, use in overrides.pathname_variant_components.items():
        if use and ('/' + name + '/' in assetname):
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
            for name in new_name if isinstance(new_name, list) else [new_name]:
                variants.add(name)

    return variants


def should_skip_from_variants(variants: Set[str], overrides: OverrideSettings) -> bool:
    skip_variants = set(name for name, use in overrides.variants_to_skip_export.items() if use)
    return bool(variants & skip_variants)
