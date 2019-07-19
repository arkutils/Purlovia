from typing import *

from ark.properties import PriorityPropDict


def gather_damage_mults(props: PriorityPropDict) -> Optional[Dict[str, float]]:
    if not props['BoneDamageAdjusters'][0]:
        return None

    adjusters = props['BoneDamageAdjusters'][0][-1].values

    result = dict()
    for bone_info in adjusters:
        name = str(bone_info.get_property('BoneName'))
        mult = bone_info.get_property('DamageMultiplier').value
        result[name] = mult

    return result
