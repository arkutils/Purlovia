from typing import *

from ark.properties import stat_value
from ue.utils import clean_double as cd
from ue.utils import clean_float as cf

__all__ = [
    'gather_taming_data',
]


def gather_taming_data(props) -> Dict[str, Any]:
    data: Dict[str, Any] = dict()

    # Currently unable to gather the foods list
    eats: Optional[List[str]] = None
    favorite_kibble: Optional[str] = None
    special_food_values: Optional[List[Dict[str, Dict[str, List[int]]]]] = None

    can_tame = stat_value(props, 'bCanBeTamed', 0, True)
    can_knockout = stat_value(props, 'bCanBeTorpid', 0, True)
    data['nonViolent'] = stat_value(props, 'bSupportWakingTame', 0, False) and can_tame
    data['violent'] = not stat_value(props, 'bPreventSleepingTame', 0, False) and can_tame and can_knockout

    if can_tame or True:
        data['tamingIneffectiveness'] = cf(stat_value(props, 'TameIneffectivenessByAffinity', 0, 20.0))
        data['affinityNeeded0'] = cf(stat_value(props, 'RequiredTameAffinity', 0, 100))
        data['affinityIncreasePL'] = cf(stat_value(props, 'RequiredTameAffinityPerBaseLevel', 0, 5.0))

        torpor_depletion = stat_value(props, 'KnockedOutTorpidityRecoveryRateMultiplier', 0, 3.0) \
            * stat_value(props, 'RecoveryRateStatusValue', 2, 0.00)

        if data['violent']:
            data['torporDepletionPS0'] = cd(-torpor_depletion)
        if data['nonViolent']:
            data['wakeAffinityMult'] = cf(stat_value(props, 'WakingTameFoodAffinityMultiplier', 0, 1.6))
            data['wakeFoodDeplMult'] = cf(stat_value(props, 'WakingTameFoodConsumptionRateMultiplier', 0, 2.0))

        data['foodConsumptionBase'] = cf(-stat_value(props, 'BaseFoodConsumptionRate', 0, -0.025000))  # pylint: disable=invalid-unary-operand-type
        data['foodConsumptionMult'] = cf(stat_value(props, 'ProneWaterFoodConsumptionMultiplier', 0, 1.00))

        if eats is not None:
            data['eats'] = eats
        if favorite_kibble is not None:
            data['favoriteKibble'] = favorite_kibble
        if special_food_values is not None:
            data['specialFoodValues'] = special_food_values

    return data
