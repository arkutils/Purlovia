from typing import List, Optional

from ark.defaults import *
from ark.properties import stat_value
from ark.types import PrimalDinoCharacter, PrimalDinoStatusComponent
from ue.utils import clean_double as cd
from ue.utils import clean_float as cf

__all__ = [
    'gather_stat_data',
]


def gather_stat_data(char_props: PrimalDinoCharacter, dcsc_props: PrimalDinoStatusComponent, props, statIndexes):
    statsArray = list()

    # Create a temporary set of Iw defaults, overriding torpor with TheMaxTorporIncreasePerBaseLevel or 0.06
    iw_values = list(IW_VALUES)
    iw_values[2] = stat_value(props, 'TheMaxTorporIncreasePerBaseLevel', 0, 0.06)

    for _, ark_index in enumerate(statIndexes):
        can_level = (ark_index == 2) or stat_value(props, 'CanLevelUpValue', ark_index, CANLEVELUP_VALUES)
        add_one = 1 if IS_PERCENT_STAT[ark_index] else 0
        zero_mult = 1 if can_level else 0
        ETHM = stat_value(props, 'ExtraTamedHealthMultiplier', ark_index, EXTRA_MULTS_VALUES)

        stat_data: Optional[List[float]] = [
            cd(stat_value(props, 'MaxStatusValues', ark_index, BASE_VALUES) + add_one),
            cd(stat_value(props, 'AmountMaxGainedPerLevelUpValue', ark_index, iw_values) * zero_mult),
            cd(stat_value(props, 'AmountMaxGainedPerLevelUpValueTamed', ark_index, 0.0) * ETHM * zero_mult),
            cf(stat_value(props, 'TamingMaxStatAdditions', ark_index, 0.0)),
            cf(stat_value(props, 'TamingMaxStatMultipliers', ark_index, 0.0)),
        ]

        # Creates a null value in the JSON for stats that are unused
        dont_use = stat_value(props, 'DontUseValue', ark_index, DONTUSESTAT_VALUES)
        if dont_use and not can_level:
            stat_data = None

        statsArray.append(stat_data)

    return statsArray
