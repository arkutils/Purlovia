from typing import List, Optional, Tuple

from ark.types import PrimalDinoStatusComponent
from ue.utils import clean_double as cd
from ue.utils import clean_float as cf

__all__ = [
    'gather_stat_data',
]

IS_PERCENT_STAT = (0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1)


def gather_stat_data(dcsc_props: PrimalDinoStatusComponent, meta_props: PrimalDinoStatusComponent,
                     statIndexes: Tuple[int, ...]) -> List[Optional[List[float]]]:
    statsArray = list()

    iw_values: List[float] = [0] * len(statIndexes)
    for _, ark_index in enumerate(statIndexes):
        can_level = (ark_index == 2) or meta_props.CanLevelUpValue[ark_index]
        dont_use = meta_props.DontUseValue[ark_index]

        # Creates a null value in the JSON for stats that are unused
        if dont_use and not can_level:
            stat_data: Optional[List[float]] = None

        else:
            add_one = 1 if IS_PERCENT_STAT[ark_index] else 0
            zero_mult = 1 if can_level else 0
            ETHM = dcsc_props.ExtraTamedHealthMultiplier[0].rounded_value if ark_index == 0 else 1

            # Overrides the IW value for Torpor. While this hasn't been seen before, a species may allow torpor
            #   to be leveled in the wild. Unsure how Ark would handle this.
            if ark_index == 2:
                iw_values[ark_index] = dcsc_props.TheMaxTorporIncreasePerBaseLevel[0].rounded_value
            else:
                iw_values[ark_index] = dcsc_props.AmountMaxGainedPerLevelUpValue[ark_index].rounded_value

            stat_data = [
                cd(dcsc_props.MaxStatusValues[ark_index].rounded_value + add_one),
                cd(iw_values[ark_index] * zero_mult),
                cd(dcsc_props.AmountMaxGainedPerLevelUpValueTamed[ark_index].rounded_value * ETHM * zero_mult),
                cf(dcsc_props.TamingMaxStatAdditions[ark_index].rounded_value),
                cf(dcsc_props.TamingMaxStatMultipliers[ark_index].rounded_value),
            ]

        statsArray.append(stat_data)

    return statsArray
