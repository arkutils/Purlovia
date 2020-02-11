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
        name=d['AttackName'] or None,
        interval=d['AttackInterval'],
        dmg=d['MeleeDamageAmount'],
        radius=d['MeleeSwingRadius'],
        stamina=d['StaminaCost'],
    )

    proj = d['ProjectileClass']
    if proj:
        v['isProjectile'] = True

    return v
