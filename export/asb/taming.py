from typing import Any, Dict, List, Optional

from ark.overrides import OverrideSettings, TamingMethod
from ark.types import PrimalDinoCharacter, PrimalDinoStatusComponent
from ue.utils import clean_double as cd
from ue.utils import clean_float as cf

__all__ = [
    'gather_taming_data',
]


def gather_taming_data(char_props: PrimalDinoCharacter, dcsc_props: PrimalDinoStatusComponent,
                       overrides: OverrideSettings) -> Dict[str, Any]:
    data: Dict[str, Any] = dict()

    # Currently unable to gather the foods list
    eats: Optional[List[str]] = None
    special_food_values: Optional[List[Dict[str, Dict[str, List[int]]]]] = None

    if overrides.taming_method:
        can_tame = overrides.taming_method != TamingMethod.none
        data['nonViolent'] = overrides.taming_method == TamingMethod.awake
        data['violent'] = overrides.taming_method == TamingMethod.knockout
    else:
        can_tame = bool(char_props.bCanBeTamed[0])
        can_knockout = char_props.bCanBeTorpid[0]
        data['nonViolent'] = char_props.bSupportWakingTame[0] and can_tame
        data['violent'] = not char_props.bPreventSleepingTame[0] and can_tame and can_knockout

    if can_tame or True:
        data['tamingIneffectiveness'] = cf(char_props.TameIneffectivenessByAffinity[0].rounded_value)
        data['affinityNeeded0'] = cf(char_props.RequiredTameAffinity[0].rounded_value)
        data['affinityIncreasePL'] = cf(char_props.RequiredTameAffinityPerBaseLevel[0].rounded_value)

        torpor_depletion = dcsc_props.KnockedOutTorpidityRecoveryRateMultiplier[0].rounded_value \
            * dcsc_props.RecoveryRateStatusValue[2].rounded_value

        if data['violent']:
            data['torporDepletionPS0'] = cd(-torpor_depletion)
        if data['nonViolent']:
            data['wakeAffinityMult'] = cf(char_props.WakingTameFoodAffinityMultiplier[0].rounded_value)
            data['wakeFoodDeplMult'] = cf(dcsc_props.WakingTameFoodConsumptionRateMultiplier[0].rounded_value)

        data['foodConsumptionBase'] = cf(-dcsc_props.BaseFoodConsumptionRate[0].rounded_value)
        data['foodConsumptionMult'] = cf(dcsc_props.ProneWaterFoodConsumptionMultiplier[0].rounded_value)
        data['babyFoodConsumptionMult'] = cf(dcsc_props.BabyDinoConsumingFoodRateMultiplier[0].rounded_value *
                                             dcsc_props.ExtraBabyDinoConsumingFoodRateMultiplier[0].rounded_value)

        if eats is not None:
            data['eats'] = eats
        if special_food_values is not None:
            data['specialFoodValues'] = special_food_values

    return data
