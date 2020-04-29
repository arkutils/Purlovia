from typing import List, Optional, cast

from ark.types import PrimalDinoCharacter
from automate.hierarchy_exporter import ExportModel
from ue.properties import StructProperty


class AttackInfo(ExportModel):
    name: str
    interval: float
    dmg: float
    radius: float
    stamina: float
    isProjectile: Optional[bool]


class AttackData(ExportModel):
    defaultDmg: Optional[int]
    defaultSwingRadius: Optional[float]
    attacks: Optional[List[AttackInfo]]


def gather_attack_data(char: PrimalDinoCharacter):
    result = AttackData()

    result.defaultDmg = char.MeleeDamageAmount[0]
    result.defaultSwingRadius = char.MeleeSwingRadius[0]

    if 'AttackInfos' in char:
        attacks = [_convert_attack(cast(StructProperty, attack)) for attack in char.AttackInfos[0].values]
        if attacks:
            result.attacks = attacks

    return result


def _convert_attack(attack: StructProperty) -> AttackInfo:
    d: Dict[str, Any] = attack.as_dict()

    v = AttackInfo(
        name=str(d['AttackName'] or None),
        interval=d['AttackInterval'],
        dmg=d['MeleeDamageAmount'],
        radius=d['MeleeSwingRadius'],
        stamina=d['StaminaCost'],
    )

    proj = d['ProjectileClass']
    if proj:
        v.isProjectile = True

    return v
