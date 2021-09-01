from typing import Any, Dict, Optional, Union

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
    sprint: Optional[FloatProperty]
    swimOrFly: Optional[FloatProperty]


class MovementIntermediate(ExportModel):
    movementW: Optional[MovementModes]
    movementD: Optional[MovementModes]
    movementR: Optional[MovementModes]
    staminaRates: Optional[StaminaRates]


def can_walk(_species: PrimalDinoCharacter, nav_props: Dict[str, Any]) -> bool:
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

    result.movementW = _gather_speeds(species, species.ExtraUnTamedSpeedMultiplier[0], False)
    result.movementD = _gather_speeds(species, species.ExtraTamedSpeedMultiplier[0], True)
    result.staminaRates = _gather_stamina(dcsc, result.movementW)

    rider_main_differs = species.RiderMaxSpeedModifier[0] != 1
    rider_extra_differs = species.RiderExtraMaxSpeedModifier[0] != 1
    rider_sprint_differs = species.RiderMaxRunSpeedModifier[0] != 1
    if species.bAllowRiding[0] and (rider_main_differs or rider_extra_differs or rider_sprint_differs):
        result.movementR = MovementModes(
            walk=_calculate_ridden_speeds(species, result.movementD.walk),
            swim=_calculate_ridden_speeds(species, result.movementD.swim),
            fly=_calculate_ridden_speeds(species, result.movementD.fly),
        )

    return result


def _calculate_base_speed(species: PrimalDinoCharacter, base: FloatProperty, tamed: bool) -> float:
    if not tamed:
        return base * species.UntamedWalkingSpeedModifier[0]
    else:
        return base * species.TamedWalkingSpeedModifier[0]


def _calculate_sprint_speed(species: PrimalDinoCharacter, base: Union[float, FloatProperty], mult: Union[float, FloatProperty],
                            tamed: bool) -> float:
    speed = base * mult * species.RunningSpeedModifier[0]
    if not tamed:
        speed = speed * species.UntamedRunningSpeedModifier[0]
    else:
        speed = speed * species.TamedRunningSpeedModifier[0]

    if bool(species.ScaleExtraRunningSpeedModifier[0]) and species.ScaleExtraRunningMultiplierMax[0] <= 1.0:
        # ScaleExtraRunningMultiplierMax determines max speed while running.
        speed = speed * species.ScaleExtraRunningMultiplierMax[0]
    # Other ScaleExtra properties didn't seem to have an effect.

    return speed


def _clean_value(v: float) -> Union[float, int]:
    v = round(v, 1)
    if v == int(v):
        v = int(v)
    return v


def _calculate_ridden_speeds(species: PrimalDinoCharacter, dom: Optional[SpeedData]) -> Optional[SpeedData]:
    if not dom:
        return None

    def _get_component(base: float) -> float:
        return _clean_value(base * species.RiderMaxSpeedModifier[0] * species.RiderExtraMaxSpeedModifier[0])

    return SpeedData(
        base=_get_component(dom.base),
        crouch=_get_component(dom.crouch) if dom.crouch else None,
        sprint=_get_component(dom.sprint * species.RiderMaxRunSpeedModifier[0]) if dom.sprint else None,
    )


def _gather_speeds(species: PrimalDinoCharacter, staticMult: FloatProperty, tamed) -> MovementModes:
    result = MovementModes()

    def mult(v):
        return _clean_value(v * staticMult)

    cm: ShooterCharacterMovement = species.CharacterMovement[0]
    nav_props_struct = cm.get('NavAgentProps', fallback=None)
    nav_props = nav_props_struct.as_dict() if nav_props_struct else {}

    canRun = species.bCanRun[0]
    canWalk = nav_props.get('bCanWalk', True)
    canCrouch = nav_props.get('bCanCrouch', False) and canWalk
    canSwim = can_swim(species, nav_props)
    canFly = nav_props.get('bCanFly', False) or species.bIsFlyerDino[0]

    if canWalk:
        # Calculate base walking speed
        walk = _calculate_base_speed(species, cm.MaxWalkSpeed[0], tamed)
        result.walk = SpeedData(base=mult(walk))

        # Calculate crouching speed
        if canCrouch:
            result.walk.crouch = mult(cm.MaxWalkSpeedCrouched[0])

        # Calculate running speed
        if canRun:
            sprint = mult(_calculate_sprint_speed(species, cm.MaxWalkSpeed[0], 1.0, tamed))
            if sprint != result.walk.base:
                result.walk.sprint = sprint

    if canFly:
        # Calculate base flying speed
        fly = _calculate_base_speed(species, cm.MaxFlySpeed[0], tamed)
        result.fly = SpeedData(base=mult(fly))

        # Calculate running speed
        if canRun:
            sprint = mult(_calculate_sprint_speed(species, cm.MaxFlySpeed[0], species.FlyingRunSpeedModifier[0], tamed))
            if sprint != result.fly.base:
                result.fly.sprint = sprint

    if canSwim:
        # Calculate base swimming speed
        has_free_movement = has_free_movement_in_water(species)
        swim = cm.MaxSwimSpeed[0] if not has_free_movement else cm.MaxFlySpeed[0]
        swim_walk = _calculate_base_speed(species, swim, tamed)
        result.swim = SpeedData(base=mult(swim_walk))

        # Calculate running speed
        if canRun and bool(species.bAllowRunningWhileSwimming[0]):
            sprint = mult(_calculate_sprint_speed(species, swim, species.SwimmingRunSpeedModifier[0], tamed))
            if sprint != result.swim.base:
                result.swim.sprint = sprint

    return result


def _gather_stamina(dcsc: DinoCharacterStatusComponent, movementW: MovementModes) -> StaminaRates:
    result = StaminaRates()

    if movementW.walk and movementW.walk.sprint:
        result.sprint = dcsc.RunningStaminaConsumptionRate[0]
    if movementW.fly or movementW.swim:
        result.swimOrFly = dcsc.SwimmingOrFlyingStaminaConsumptionRate[0]

    return result
