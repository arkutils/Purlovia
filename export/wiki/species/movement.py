from typing import *

from ark.types import PrimalDinoCharacter, ShooterCharacterMovement


def gather_movement_data(species: PrimalDinoCharacter) -> Dict[str, Any]:
    result: Dict[str, Any] = dict()

    untamedMult = species.UntamedRunningSpeedModifier[0] * species.ExtraUnTamedSpeedMultiplier[0]
    result['movementW'] = _gather_speeds(species, untamedMult)

    tamedMult = species.TamedRunningSpeedModifier[0] * species.ExtraTamedSpeedMultiplier[0]
    result['movementD'] = _gather_speeds(species, tamedMult)

    return result


def _gather_speeds(species: PrimalDinoCharacter, multValue: float) -> Dict[str, Any]:
    result: Dict[str, Any] = dict()

    def mult(v):
        v = v * multValue
        v = round(v, 1)
        if v == int(v):
            v = int(v)
        return v

    # TODO: Include ScaleExtraRunningSpeedModifier and ScaleExtraRunningMultiplier(Min|Max|Speed)

    cm: ShooterCharacterMovement = species.CharacterMovement[0]
    nav_props_struct = cm.get('NavAgentProps', fallback=None)
    nav_props = nav_props_struct.as_dict() if nav_props_struct else {}

    isWaterDino = bool(species.bIsWaterDino[0])
    canWalk = nav_props.get('bCanWalk', True) and not isWaterDino
    canCrouch = nav_props.get('bCanCrouch', False) and canWalk
    canRun = canWalk and species.bCanRun[0]
    canSwim = (nav_props.get('bCanSwim', True) or isWaterDino) and not species.bPreventEnteringWater[0]
    canFly = nav_props.get('bCanFly', False) or species.bIsFlyerDino[0]

    if canWalk:
        result['walk'] = dict(base=mult(cm.MaxWalkSpeed[0]))
        if canCrouch:
            result['walk']['crouch'] = mult(cm.MaxWalkSpeedCrouched[0])
        if canRun and species.RunningSpeedModifier[0] != 1.0:
            result['walk']['sprint'] = mult(cm.MaxWalkSpeed[0] * species.RunningSpeedModifier[0])

    if canFly:
        result['fly'] = dict(base=mult(cm.MaxFlySpeed[0]))
        if canRun and species.FlyingRunSpeedModifier[0] != 1.0:
            result['fly']['sprint'] = mult(cm.MaxFlySpeed[0] * species.FlyingRunSpeedModifier[0])

    if canSwim:
        result['swim'] = dict(base=mult(cm.MaxSwimSpeed[0]))
        if canRun and species.bAllowRunningWhileSwimming[0] and species.RidingSwimmingRunSpeedModifier[0] != 1.0:
            result['swim']['sprint'] = mult(cm.MaxSwimSpeed[0] * species.RidingSwimmingRunSpeedModifier[0])

    return result
