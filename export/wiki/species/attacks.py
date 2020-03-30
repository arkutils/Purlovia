from typing import *

from ark.types import PrimalDinoCharacter
from ue.properties import StructProperty


def gather_attack_data(char: PrimalDinoCharacter):
    result: Dict[str, Any] = dict()

    result['defaultDmg'] = char.MeleeDamageAmount[0]
    result['defaultSwingRadius'] = char.MeleeSwingRadius[0]

    if 'AttackInfos' in char:
        attacks = [_convert_attack(cast(StructProperty, attack)) for attack in char.AttackInfos[0].values]
        if attacks:
            result['attacks'] = attacks

    return dict(attack=result)


def _convert_attack(attack: StructProperty):
    d: Dict[str, Any] = attack.as_dict()

    v = dict(
        name=d['AttackName'][0] or None,
        interval=d['AttackInterval'][0],
        dmg=d['MeleeDamageAmount'][0],
        radius=d['MeleeSwingRadius'][0],
        stamina=d['StaminaCost'][0],
    )

    proj = d['ProjectileClass'][0]
    if proj:
        v['isProjectile'] = True

    return v
