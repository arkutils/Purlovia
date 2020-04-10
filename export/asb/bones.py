from typing import Dict, Optional

from ark.types import PrimalDinoCharacter

__all__ = [
    'gather_damage_mults',
]


def gather_damage_mults(char_props: PrimalDinoCharacter) -> Optional[Dict[str, float]]:
    damage_adjusters = char_props.get('BoneDamageAdjusters', 0, None)
    if not damage_adjusters:
        return None

    adjusters = damage_adjusters.values

    result = dict()
    for bone_info in adjusters:
        name = str(bone_info.get_property('BoneName'))
        mult = bone_info.get_property('DamageMultiplier')
        result[name] = mult

    return result
