from typing import Any, Dict, List, Optional, cast

from ark.types import PrimalDinoCharacter
from automate.hierarchy_exporter import ExportModel
from ue.properties import BoolProperty, FloatProperty, IntProperty, StringLikeProperty, StructProperty


class AttackInfo(ExportModel):
    name: StringLikeProperty
    interval: FloatProperty
    dmg: IntProperty
    radius: FloatProperty
    stamina: FloatProperty
    isProjectile: bool = False


class AttackData(ExportModel):
    defaultDmg: Optional[IntProperty]
    defaultSwingRadius: Optional[FloatProperty]
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
        name=d['AttackName'],
        interval=d['AttackInterval'],
        dmg=d['MeleeDamageAmount'],
        radius=d['MeleeSwingRadius'],
        stamina=d['StaminaCost'],
        isProjectile=bool(d['ProjectileClass']),  # True if ObjectProperty contains reference
    )

    return v
