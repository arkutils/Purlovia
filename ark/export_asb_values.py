from logging import NullHandler, getLogger
from typing import *

from ark.export.bones import gather_damage_mults
from ark.export.breeding import gather_breeding_data
from ark.export.colors import gather_color_data, gather_pgd_colors
from ark.export.immobilize import gather_immobilization_data
from ark.export.stats import gather_stat_data
from ark.export.taming import gather_taming_data
from ark.properties import PriorityPropDict, gather_properties, stat_value
from ue.asset import UAsset
from ue.loader import AssetLoader

from .overrides import get_overrides_for_species

__all__ = [
    'values_from_pgd',
    'values_for_species',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())

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

ASB_STAT_INDEXES: Tuple[int, ...] = (0, 1, 3, 4, 7, 8, 9, 2)
ARK_STAT_INDEXES = tuple(range(12))


def values_from_pgd(asset: UAsset, require_override: bool = False) -> Dict[str, Any]:
    assert asset and asset.loader
    loader = asset.loader
    props = gather_properties(asset)

    result: Dict[str, Any] = dict()

    colors, dyes = gather_pgd_colors(props, loader, require_override=require_override)
    if colors:
        result['colorDefinitions'] = colors
    if dyes:
        result['dyeDefinitions'] = dyes

    return result


def values_for_species(asset: UAsset,
                       props: PriorityPropDict,
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

    assert asset.assetname and asset.default_export and asset.default_class and asset.default_class.fullname

    modid: str = asset.loader.get_mod_id(asset.assetname)
    overrides = get_overrides_for_species(asset.assetname, modid)

    bp: str = asset.default_class.fullname
    if bp.endswith('_C'):
        bp = bp[:-2]

    # Replace names to match ASB's hardcoding of specific species
    name = overrides.descriptive_name or name

    # Tag is used to identify immobilization targets and compatible saddles
    # tag = stat_value(props, 'CustomTag', 0, None) or f'<unknown tag for {asset.default_class.name}'

    # Drag weight is used for immobilization calculation and arena entry
    # dragWeight = stat_value(props, 'DragWeight', 0, None)

    species = dict(name=name, blueprintPath=bp)  #, tag=tag, dragWeight=dragWeight

    # Stat data
    statsField = 'fullStatsRaw' if fullStats else 'statsRaw'
    statIndexes = ARK_STAT_INDEXES if fullStats else ASB_STAT_INDEXES
    species[statsField] = gather_stat_data(props, statIndexes)

    # Set imprint multipliers
    stat_imprint_mults: List[float] = list()
    for ark_index in statIndexes:
        imprint_mult = stat_value(props, 'DinoMaxStatAddMultiplierImprinting', ark_index, IMPRINT_VALUES)
        stat_imprint_mults.append(imprint_mult)
    if stat_imprint_mults != list(IMPRINT_VALUES):
        species['statImprintMult'] = stat_imprint_mults

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
            colors = gather_color_data(asset, props, overrides)
            if colors is not None:
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

    DONTUSESTAT_VALUES = (0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1)
    displayed_stats: int = 0

    for i in statIndexes:
        use_stat = not stat_value(props, 'DontUseValue', i, DONTUSESTAT_VALUES)
        if use_stat and not (i == 9 and doesntUseOxygen):
            displayed_stats |= (1 << i)

    if allFields or TBHM != 1: species['TamedBaseHealthMultiplier'] = TBHM
    if allFields or noSpeedImprint: species['NoImprintingForSpeed'] = noSpeedImprint
    if allFields or doesntUseOxygen: species['doesNotUseOxygen'] = doesntUseOxygen
    if allFields or displayed_stats: species['displayedStats'] = displayed_stats

    return species
