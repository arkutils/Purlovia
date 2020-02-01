from typing import *

from ark.types import PrimalDinoCharacter


def gather_movement_data(species: PrimalDinoCharacter, multValue: float) -> Dict[str, Any]:
    result: Dict[str, Any] = dict()

    def mult(v):
        v = v * multValue
        v = round(v, 1)
        if v == int(v):
            v = int(v)
        return v

    # TODO: Include ScaleExtraRunningSpeedModifier and ScaleExtraRunningMultiplier(Min|Max|Speed)

    canRun = species.bCanRun[0]

    if species.bCanWalk[0]:
        result['walk'] = dict(base=mult(species.MaxWalkSpeed[0]))
        if species.bCanCrouch[0]:
            result['walk']['crouch'] = mult(species.MaxWalkSpeedCrouched[0])
        if canRun:
            result['walk']['sprint'] = mult(species.MaxWalkSpeed[0] * species.RunningSpeedModifier[0])

    if species.bIsFlyerDino[0]:
        result['fly'] = dict(base=mult(species.MaxFlySpeed[0]))
        if canRun:
            result['fly']['sprint'] = mult(species.MaxFlySpeed[0] * species.FlyingRunSpeedModifier[0])

    if species.bCanSwim[0]:
        result['swim'] = dict(base=mult(species.MaxSwimSpeed[0]))
        if canRun and species.bAllowRunningWhileSwimming[0]:
            result['swim']['sprint'] = mult(species.MaxSwimSpeed[0] * species.RidingSwimmingRunSpeedModifier[0])

    return result
