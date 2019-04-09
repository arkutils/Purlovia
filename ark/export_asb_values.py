from ue.asset import UAsset
from ark.properties import stat_value

#                    Ark   ASB
# Health              0     0
# Stamina             1     1
# Torpidity           2     7
# Oxygen              3     2
# Food                4     3
# Water               5
# Temperature         6
# Weight              7     4
# Melee Damage        8     5  (add 100%)
# Movement Speed      9     6  (add 100%)
# Fortitude           10
# Crafting Skill      11

# ASB wants arrays per-stat of [B, Iw, Id, Ta, Tm]

# B     MaxStatusValues
# Iw    AmountMaxGainedPerLevelUpValue
# Id    AmountMaxGainedPerLevelUpValueTamed
# Ta    TamingMaxStatAdditions
# Tm    TamingMaxStatMultipliers

# TBHM  TamedBaseHealthMultiplier

NAME_CHANGES = {
    'Dire Bear': 'Direbear',
    'Ichthyosaurus': 'Ichthy',
    'Paraceratherium': 'Paracer',
}

BASE_VALUES = (100, 100, 100, 100, 100, 100, 0, 0, 0, 0, 0, 0)
IW_VALUES = (0, 0, 0.06, 0, 0, 0, 0, 0, 0, 0, 0, 0)
IMPRINT_VALUES = (0.2, 0, 0.2, 0, 0.2, 0.2, 0, 0.2, 0.2, 0.2, 0, 0)
EXTRA_MULTS_VALUES = (1.35, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)

remove_default_values = True  # TODO: probably set to False for production runs


def values_for_species(asset: UAsset, props, all=False):
    # Create a temporary set of Iw defaults, overriding torpor with TheMaxTorporIncreasePerBaseLevel or 0.06
    iw_values = list(IW_VALUES)
    iw_values[2] = stat_value(props, 'TheMaxTorporIncreasePerBaseLevel', 0, 0.06)

    name = stat_value(props, 'DescriptiveName', 0, None)
    bp = asset.assetname + '.' + asset.assetname.split('/')[-1]  # nasty

    # Replace names to match ASB's hardcoding of specific species
    name = NAME_CHANGES.get(name, name)

    species = dict(name=name, blueprintPath=bp)
    species['statsRaw'] = list()
    for asb_index, ark_index in enumerate((0, 1, 3, 4, 7, 8, 9, 2)):
        add_one = 1 if ark_index == 8 or ark_index == 9 else 0
        zero_mult = stat_value(props, 'CanLevelUpValue', ark_index, 1)
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

        species['statsRaw'].append(stat_data)

    noSpeedImprint = (stat_value(props, 'DinoMaxStatAddMultiplierImprinting', 9, IMPRINT_VALUES) == 0)
    usesOxyWild = stat_value(props, 'bCanSuffocate', 0, True)
    usesOxyTamed = stat_value(props, 'bCanSuffocateIfTamed', 0, usesOxyWild)
    forceOxy = stat_value(props, 'bForceGainOxygen', 0, False)
    doesntUseOxygen = not (usesOxyTamed or forceOxy)
    ETBHM = stat_value(props, 'ExtraTamedBaseHealthMultiplier', 0, 1)
    TBHM = stat_value(props, 'TamedBaseHealthMultiplier', 0, 1) * ETBHM

    if all or TBHM != 1: species['TamedBaseHealthMultiplier'] = TBHM
    if all or noSpeedImprint: species['NoImprintingForSpeed'] = noSpeedImprint
    if all or doesntUseOxygen: species['doesNotUseOxygen'] = doesntUseOxygen

    return species
