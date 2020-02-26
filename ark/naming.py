import re
from typing import List, Optional, Tuple

from .types import PrimalDinoCharacter

__all__ = [
    'get_variants_from_assetname',
]


def get_variants_from_assetname(char: PrimalDinoCharacter) -> Tuple[str, ...]:
    bp: str = char.get_source().fullname.split('.')[0]
    cls: str = bp.split('/')[-1]
    variants: List[str] = []

    # Mission variants
    match = re.search(r'/MissionVariants/(\w+?)/(\w+?)/', bp)
    if match:
        variants.append(match[1])
        variants.append(match[2])
    else:
        match = re.search(r'/MissionVariants/(\w+?)/', bp)
        if match:
            variants.append(match[1])

    # Biome variants
    # TODO: Use overrides instead of these hardcoded values
    if '/BiomeVariants/Lava_Golem/Volcano_Golem' in bp:
        variants.append('Volcano')
    elif '/BiomeVariants/Lunar_Salmon/Rare_Lunar_Salmon' in bp:
        variants.append('Lunar')
    else:
        match = re.search(r'/BiomeVariants/(\w+?)_', bp)
        if match:
            variants.append(match[1])
        else:
            match = re.search(r'/BiomeVariants/(?P<name>[^/_.]+)\w*/(?P=name)', bp)
            if match:
                variants.append(match['name'])

    # TODO: Use overrides instead of these hardcoded values
    if '/Mods/' not in bp:
        for biome_suffix in ('Bog', 'Lunar', 'Ocean', 'Snow', 'VR', 'Volcano', 'Volcanic'):
            if cls.endswith('_' + biome_suffix):
                variants.append(biome_suffix)

    # Boss and difficulty
    if char.bIsBossDino[0]:
        entry = 'Boss'
        if 'Minion' in cls:
            entry = 'Boss Minion'
        variants.append(entry)

        match = re.search(r'(Easy|Med(?:ium)?|Hard)', cls)
        if match:
            diff = match[0]
            if diff == 'Med': diff = 'Medium'
            variants.append(diff)

    if char.bIsCorrupted[0]:
        variants.append('Corrupted')

    # Remove duplicates without altering order, correcting some oddities
    result: List[str] = []
    for name in variants:
        if name == 'Volcanic': name = 'Volcano'
        if name == 'Arctic': name = 'Snow'
        if name not in result:
            result.append(name)

    return tuple(result)
