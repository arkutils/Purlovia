from typing import *
import logging

from ue.asset import UAsset
from ark.properties import stat_value

from ark.export.bones import gather_damage_mults
from ark.export.breeding import gather_breeding_data
from ark.export.colors import gather_color_data
from ark.export.immobilize import gather_immobilization_data
from ark.export.stats import gather_stat_data
from ark.export.taming import gather_taming_data

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

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

# 50% TE Bonus Levels (MaxTamingEffectivenessBaseLevelMultiplier Default: 0.5)

# TBHM  TamedBaseHealthMultiplier

NAME_CHANGES = {
    'Dire Bear': 'Direbear',
    'Ichthyosaurus': 'Ichthy',
    'Paraceratherium': 'Paracer',
}
IMPRINT_VALUES = (0.2, 0, 0.2, 0, 0.2, 0.2, 0, 0.2, 0.2, 0.2, 0, 0)

ASB_STAT_INDEXES = (0, 1, 3, 4, 7, 8, 9, 2)
ARK_STAT_INDEXES = list(range(12))

remove_default_values = True  # TODO: probably set to False for production runs


# returns the species' mass or the default value of 100
# needs to be incorporated into the gather props function as species
#    that inherit from other species will use it's parent's mass instead
#    and ends up receiving the "default" 100 value for mass
def get_species_mass(asset):
    for export in asset.exports:
        if export.namespace.value:
            if str(export.namespace.value) == str(asset.default_export):
                for prop in export.properties:
                    if str(prop.header.name.value) == 'Mass':
                        return prop.value.value
    return 100.0


def values_for_species(asset: UAsset,
                       props,
                       allFields=False,
                       fullStats=False,
                       includeColor=True,
                       includeBreeding=True,
                       includeImmobilize=True,
                       includeDamageMults=True,
                       includeTaming=True):
    assert asset.loader

    name = stat_value(props, 'DescriptiveName', 0, None) or stat_value(props, 'DinoNameTag', 0, None)
    if not name:
        logger.warning(f"Species {asset.assetname} has no DescriptiveName or DinoNameTag")
        name = '<unnamed species>'

    assert asset.assetname is not None and asset.default_export and asset.default_class and asset.default_class.fullname
    bp: str = asset.default_class.fullname
    if bp.endswith('_C'):
        bp = bp[:-2]

    # Replace names to match ASB's hardcoding of specific species
    name = NAME_CHANGES.get(name, name)

    # Tag is used to identify immobilization targets and compatible saddles
    # tag = stat_value(props, 'CustomTag', 0, None) or f'<unknown tag for {asset.default_class.name}'

    # Drag weight is used for immobilization calculation and arena entry
    # dragWeight = stat_value(props, 'DragWeight', 0, None)

    species = dict(name=name, blueprintPath=bp)  #, tag=tag, dragWeight=dragWeight

    # Stat data
    statsField = 'fullStatsRaw' if fullStats else 'statsRaw'
    statIndexes = ARK_STAT_INDEXES if fullStats else ASB_STAT_INDEXES
    species[statsField] = gather_stat_data(props, statIndexes)

    if includeImmobilize:
        # ImmobilizedBy format data
        immobilization_data = gather_immobilization_data(props, asset.loader)
        species['immobilizedBy'] = immobilization_data

    if includeBreeding:
        # Breeding data
        if stat_value(props, 'bCanHaveBaby', 0, False):  # TODO: Consider always including this data
            breeding_data = gather_breeding_data(props, asset.loader)
            if breeding_data:
                species['breeding'] = breeding_data

    if includeColor:
        # Color data
        if stat_value(props, 'bUseColorization', False):
            colors = gather_color_data(props, asset.loader)
            if colors:
                species['colors'] = colors

    if includeTaming:
        # Taming data
        if stat_value(props, 'bCanBeTamed', True) or True:  # ASB currently requires all species to have taming data
            taming = gather_taming_data(props)
            if taming:
                species['taming'] = taming

    if includeDamageMults:
        # Bone damage multipliers
        dmg_mults = gather_damage_mults(props)
        if dmg_mults:
            species['boneDamageAdjusters'] = dmg_mults

    # Misc data
    noSpeedImprint = (stat_value(props, 'DinoMaxStatAddMultiplierImprinting', 9, IMPRINT_VALUES) == 0)
    usesOxyWild = stat_value(props, 'bCanSuffocate', 0, True)
    usesOxyTamed = stat_value(props, 'bCanSuffocateIfTamed', 0, usesOxyWild)
    forceOxy = stat_value(props, 'bForceGainOxygen', 0, False)
    doesntUseOxygen = not (usesOxyTamed or forceOxy)
    ETBHM = stat_value(props, 'ExtraTamedBaseHealthMultiplier', 0, 1)
    TBHM = stat_value(props, 'TamedBaseHealthMultiplier', 0, 1) * ETBHM

    if allFields or TBHM != 1: species['TamedBaseHealthMultiplier'] = TBHM
    if allFields or noSpeedImprint: species['NoImprintingForSpeed'] = noSpeedImprint
    if allFields or doesntUseOxygen: species['doesNotUseOxygen'] = doesntUseOxygen

    return species
