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
# Tm    TamingMaxStatMultipliers
# Ta    TamingMaxStatAdditions

# TBHM  TamedBaseHealthMultiplier


def values_for_species(asset: UAsset, props):
    name = stat_value(props, 'DescriptiveName', 0, None)
    bp = asset.assetname + '.' + asset.assetname.split('/')[-1]  # nasty

    species = dict(name=name, blueprintPath=bp)
    species['statsRaw'] = list()
    for asb_index, ark_index in enumerate((0, 1, 3, 4, 7, 8, 9, 2)):
        stat_data = [
            stat_value(props, 'MaxStatusValues', ark_index, 1.0),
            stat_value(props, 'AmountMaxGainedPerLevelUpValue', ark_index, 0.0),
            stat_value(props, 'AmountMaxGainedPerLevelUpValueTamed', ark_index, 0.0),
            stat_value(props, 'TamingMaxStatMultipliers', ark_index, 0.0),
            stat_value(props, 'TamingMaxStatAdditions', ark_index, 0.0),
        ]
        species['statsRaw'].append(stat_data)

    species['NoImprintingForSpeed'] = not stat_value(props, 'CanLevelUpValue', 9, True)
    species['TamedBaseHealthMultiplier'] = stat_value(props, 'TamedBaseHealthMultiplier', 0, 1.0)

    return species
