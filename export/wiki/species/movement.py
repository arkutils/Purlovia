from typing import *

from pydantic import BaseModel

from ark.types import DinoCharacterStatusComponent, PrimalDinoCharacter, ShooterCharacterMovement
from automate.hierarchy_exporter import ExportModel
from ue.properties import FloatProperty


class SpeedData(ExportModel):
    base: float
    crouch: Optional[float]
    sprint: Optional[float]


class MovementModes(ExportModel):
    walk: Optional[SpeedData]
    fly: Optional[SpeedData]
    swim: Optional[SpeedData]


class StaminaRates(ExportModel):
    walk: Optional[FloatProperty]
    sprint: Optional[FloatProperty]
    swimOrFly: Optional[FloatProperty]


class MovementIntermediate(BaseModel):
    movementW: Optional[MovementModes]
    movementD: Optional[MovementModes]
    staminaRates: Optional[StaminaRates]


def can_walk(species: PrimalDinoCharacter, nav_props: Dict[str, Any]) -> bool:
    return nav_props.get('bCanWalk', True)


def has_free_movement_in_water(species: PrimalDinoCharacter) -> bool:
    '''Returns True if dino flies when submerged, granting full movement freedom.'''
    return species.SubmergedWaterMovementMode[0].get_enum_value_name() == 'MOVE_Flying'


def can_swim(species: PrimalDinoCharacter, nav_props: Dict[str, Any]) -> bool:
    '''Returns True if dino can submerge and swims by default when that happens.'''
    if nav_props.get('bCanSwim', False):
        return True

    if bool(species.bPreventEnteringWater[0]) or species.WaterSubmergedDepthThreshold[0] > 1.0:
        return False

    submerged_mode = species.SubmergedWaterMovementMode[0].get_enum_value_name()
    if submerged_mode in ('MOVE_Swimming', 'MOVE_Flying'):
        return True

    return False


def gather_movement_data(species: PrimalDinoCharacter, dcsc: DinoCharacterStatusComponent) -> MovementIntermediate:
    result = MovementIntermediate()

    untamedMult = species.UntamedRunningSpeedModifier[0] * species.ExtraUnTamedSpeedMultiplier[0]
    result.movementW = _gather_speeds(species, untamedMult)

    tamedMult = species.TamedRunningSpeedModifier[0] * species.ExtraTamedSpeedMultiplier[0]
    result.movementD = _gather_speeds(species, tamedMult)

    result.staminaRates = _gather_stamina(dcsc, result.movementW)

    return result


def _gather_speeds(species: PrimalDinoCharacter, multValue: float) -> MovementModes:
    result = MovementModes()

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

    canRun = species.bCanRun[0]
    canWalk = nav_props.get('bCanWalk', True)
    canCrouch = nav_props.get('bCanCrouch', False) and canWalk
    canSwim = can_swim(species, nav_props)
    canFly = nav_props.get('bCanFly', False) or species.bIsFlyerDino[0]

    if canWalk:
        result.walk = SpeedData(base=mult(cm.MaxWalkSpeed[0]))
        if canCrouch:
            result.walk.crouch = mult(cm.MaxWalkSpeedCrouched[0])
        if canRun and species.RunningSpeedModifier[0] != 1.0:
            result.walk.sprint = mult(cm.MaxWalkSpeed[0] * species.RunningSpeedModifier[0])

    if canFly:
        result.fly = SpeedData(base=mult(cm.MaxFlySpeed[0]))
        if canRun and species.FlyingRunSpeedModifier[0] != 1.0:
            result.fly.sprint = mult(cm.MaxFlySpeed[0] * species.FlyingRunSpeedModifier[0])

    if canSwim:
        max_speed = cm.MaxSwimSpeed[0] if not has_free_movement_in_water(species) else cm.MaxFlySpeed[0]
        result.swim = SpeedData(base=mult(max_speed))
        if canRun and species.bAllowRunningWhileSwimming[0] and species.RidingSwimmingRunSpeedModifier[0] != 1.0:
            result.swim.sprint = mult(max_speed * species.RidingSwimmingRunSpeedModifier[0])

    return result


def _gather_stamina(dcsc: DinoCharacterStatusComponent, movementW: MovementModes) -> StaminaRates:
    result = StaminaRates()

    if movementW.walk:
        if dcsc.bWalkingConsumesStamina[0]:
            result.walk = dcsc.WalkingStaminaConsumptionRate[0]
        if movementW.walk.sprint and dcsc.bRunningConsumesStamina[0]:
            result.sprint = dcsc.RunningStaminaConsumptionRate[0]
    if movementW.fly or movementW.swim:
        #if dcsc.bWalkingConsumesStamina[0]:
        result.swimOrFly = dcsc.SwimmingOrFlyingConsumptionRate[0]
        #if (movementW.swim.sprint or movementW.swim.walk) and dcsc.bRunningConsumesStamina[0]:
        #    result.sprint = dcsc.SwimmingOrFlyingConsumptionRate[0]

    return result
