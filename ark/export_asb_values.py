from ue.asset import UAsset
from ark.properties import stat_value
import ark.mod

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

    # statsRaw data
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

    # breeding data
    breeding_data = dict()
    breeding_data['gestationTime'] = 0
    breeding_data['incubationTime'] = 0

    gestation_breeding = stat_value(props, 'bUseBabyGestation', 0, False)
    has_eggs = False
    if props['FertilizedEggItemsToSpawn'][0] and props['FertilizedEggItemsToSpawn'][0][-1].values:
        eggs = list(filter(lambda v: v and str(v) != 'None', props['FertilizedEggItemsToSpawn'][0][-1].values))
        has_eggs = not not eggs

    if gestation_breeding:
        gestation_speed = stat_value(props, 'BabyGestationSpeed', 0, 0.000035)
        extra_gestation_speed_m = stat_value(props, 'ExtraBabyGestationSpeedMultiplier', 0, 1.0)

        # 'gestationTime' = 1 / (Baby Gestation Speed × Extra Baby Gestation Speed Multiplie)
        breeding_data['gestationTime'] = 1 / gestation_speed / extra_gestation_speed_m

    elif has_eggs:
        fert_egg_asset = asset.loader.load_related(eggs[0])
        fert_egg_props = ark.mod.gather_properties(fert_egg_asset)
        egg_decay = stat_value(fert_egg_props, 'EggLoseDurabilityPerSecond', 0, 1)
        extra_egg_decay_m = stat_value(fert_egg_props, 'ExtraEggLoseDurabilityPerSecondMultiplier', 0, 1)

        # 'incubationTime' = 100 / (Egg Lose Durability Per Second × Extra Egg Lose Durability Per Second Multiplier)
        breeding_data['incubationTime'] = 100 / egg_decay / extra_egg_decay_m
        breeding_data['eggTempMin'] = stat_value(fert_egg_props, 'EggMinTemperature', 0)
        breeding_data['eggTempMax'] = stat_value(fert_egg_props, 'EggMaxTemperature', 0)

    # 'maturationTime' = 1 / (Baby Age Speed × Extra Baby Age Speed Multiplier)
    baby_age_speed = stat_value(props, 'BabyAgeSpeed', 0, 1)
    extra_baby_age_speed_m = stat_value(props, 'ExtraBabyAgeSpeedMultiplier', 0, 1)

    breeding_data['maturationTime'] = 1 / baby_age_speed / extra_baby_age_speed_m
    breeding_data[f'matingCooldownMin'] = stat_value(props, 'NewFemaleMinTimeBetweenMating', 0, 64800.0)
    breeding_data[f'matingCooldownMax'] = stat_value(props, 'NewFemaleMaxTimeBetweenMating', 0, 172800.0)

    # Should not apply for future support of mods like S+ that allow all creatures to mate
    if stat_value(props, 'bCanHaveBaby', 0, False):
        species['breeding'] = breeding_data

    # misc data
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
