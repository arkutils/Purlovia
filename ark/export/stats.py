from ark.properties import stat_value

BASE_VALUES = (100, 100, 100, 100, 100, 100, 0, 0, 0, 0, 0, 0)
IW_VALUES = (0, 0, 0.06, 0, 0, 0, 0, 0, 0, 0, 0, 0)
IMPRINT_VALUES = (0.2, 0, 0.2, 0, 0.2, 0.2, 0, 0.2, 0.2, 0.2, 0, 0)
EXTRA_MULTS_VALUES = (1.35, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
DONTUSESTAT_VALUES = (0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1)
CANLEVELUP_VALUES = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

# Stats that are represented as percentages instead
IS_PERCENT_STAT = (0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1)


def gather_stat_data(props, statIndexes):
    statsArray = list()

    # Create a temporary set of Iw defaults, overriding torpor with TheMaxTorporIncreasePerBaseLevel or 0.06
    iw_values = list(IW_VALUES)
    iw_values[2] = stat_value(props, 'TheMaxTorporIncreasePerBaseLevel', 0, 0.06)

    for _, ark_index in enumerate(statIndexes):
        can_level = (ark_index == 2) or stat_value(props, 'CanLevelUpValue', ark_index, CANLEVELUP_VALUES)
        add_one = 1 if IS_PERCENT_STAT[ark_index] else 0
        zero_mult = 1 if can_level else 0
        ETHM = stat_value(props, 'ExtraTamedHealthMultiplier', ark_index, EXTRA_MULTS_VALUES)

        stat_data = [
            stat_value(props, 'MaxStatusValues', ark_index, BASE_VALUES) + add_one,
            stat_value(props, 'AmountMaxGainedPerLevelUpValue', ark_index, iw_values) * zero_mult,
            stat_value(props, 'AmountMaxGainedPerLevelUpValueTamed', ark_index, 0.0) * ETHM * zero_mult,
            stat_value(props, 'TamingMaxStatAdditions', ark_index, 0.0),
            stat_value(props, 'TamingMaxStatMultipliers', ark_index, 0.0),
        ]

        # Round to 6dp like existing values creator
        stat_data = [round(value, 6) for value in stat_data]

        # Creates a null value in the JSON for stats that are unused
        dont_use = stat_value(props, 'DontUseValue', ark_index, DONTUSESTAT_VALUES)
        if dont_use and not can_level:
            stat_data = None

        statsArray.append(stat_data)

    return statsArray
