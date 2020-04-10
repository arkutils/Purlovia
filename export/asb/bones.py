from typing import Dict, Optional

from ark.properties import PriorityPropDict
from ark.types import PrimalDinoStatusComponent, PrimalDinoCharacter

__all__ = [
    'gather_damage_mults',
]


def gather_damage_mults(char_props: PrimalDinoCharacter, dcsc_props: PrimalDinoStatusComponent,
                        props: PriorityPropDict) -> Optional[Dict[str, float]]:
    if not props['BoneDamageAdjusters'][0]:
        return None

    adjusters = props['BoneDamageAdjusters'][0][-1].values

    result = dict()
    for bone_info in adjusters:
        name = str(bone_info.get_property('BoneName'))
        mult = bone_info.get_property('DamageMultiplier')
        result[name] = mult

    return result
