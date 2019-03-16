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

BASE_VALUES = (100, 100, 100, 100, 100, 100, 0, 0, 0, 0, 0, 0)


def values_for_species(asset: UAsset, props):
    name = stat_value(props, 'DescriptiveName', 0, None)
    bp = asset.assetname + '.' + asset.assetname.split('/')[-1]  # nasty

    species = dict(name=name, blueprintPath=bp)
    species['statsRaw'] = list()
    for asb_index, ark_index in enumerate((0, 1, 3, 4, 7, 8, 9, 2)):
        add_one = 1 if ark_index == 8 or ark_index == 9 else 0
        # hp_mult = 1
        hp_mult = 1.35 if ark_index == 0 else 1

        stat_data = [
            stat_value(props, 'MaxStatusValues', ark_index, BASE_VALUES) + add_one,
            stat_value(props, 'AmountMaxGainedPerLevelUpValue', ark_index, 0.0),
            stat_value(props, 'AmountMaxGainedPerLevelUpValueTamed', ark_index, 0.0) * hp_mult,
            stat_value(props, 'TamingMaxStatAdditions', ark_index, 0.0),
            stat_value(props, 'TamingMaxStatMultipliers', ark_index, 0.0),
        ]
        species['statsRaw'].append(stat_data)

    species['NoImprintingForSpeed'] = not stat_value(props, 'CanLevelUpValue', 9, True)
    species['TamedBaseHealthMultiplier'] = stat_value(props, 'TamedBaseHealthMultiplier', 0, 1.0)

    return species
