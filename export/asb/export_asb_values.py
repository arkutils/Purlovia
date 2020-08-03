from typing import Any, Dict, List, Optional, Set, Tuple

import ark.gathering
import ue.gathering
from ark.overrides import OverrideSettings, get_overrides_for_species
from ark.types import PrimalDinoCharacter, PrimalDinoStatusComponent, PrimalGameData
from ark.variants import adjust_name_from_variants, get_variants_from_assetname, get_variants_from_species
from export.asb.bones import gather_damage_mults
from export.asb.breeding import gather_breeding_data
from export.asb.colors import gather_color_data, gather_pgd_colors
from export.asb.immobilize import gather_immobilization_data
from export.asb.stats import gather_stat_data
from export.asb.taming import gather_taming_data
from ue.asset import UAsset
from ue.loader import AssetNotFound, ModNotFound
from ue.utils import clean_float as cf
from utils.log import get_logger

__all__ = [
    'values_from_pgd',
    'values_for_species',
]

DCSC_DEFAULTS: PrimalDinoStatusComponent = PrimalDinoStatusComponent()

logger = get_logger(__name__)

#                    Ark
# Health              0
# Stamina             1
# Torpidity           2
# Oxygen              3
# Food                4
# Water               5
# Temperature         6
# Weight              7
# Melee Damage        8   (add 100%)
# Movement Speed      9   (add 100%)
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

ASB_STAT_INDEXES: Tuple[int, ...] = (0, 1, 3, 4, 7, 8, 9, 2)
ARK_STAT_INDEXES = tuple(range(12))


def values_from_pgd(asset: UAsset, require_override: bool = False) -> Dict[str, Any]:
    assert asset and asset.loader and asset.default_export
    loader = asset.loader
    pgd_props: PrimalGameData = ue.gathering.gather_properties(asset.default_export)

    result: Dict[str, Any] = dict()

    colors, dyes = gather_pgd_colors(asset, pgd_props, loader, require_override=require_override)
    if colors:
        result['colorDefinitions'] = colors
    if dyes:
        result['dyeDefinitions'] = dyes

    return result


def should_skip_from_variants(variants: Set[str], overrides: OverrideSettings) -> bool:
    skip_variants = set(name for name, use in overrides.variants_to_skip_export.items() if use)
    skip_variants |= set(name for name, use in overrides.variants_to_skip_export_asb.items() if use)
    return bool(variants & skip_variants)


def values_for_species(asset: UAsset, proxy: PrimalDinoCharacter) -> Optional[Dict[str, Any]]:
    assert asset.loader and asset.default_export and asset.default_class and asset.default_class.fullname

    char_props: PrimalDinoCharacter = ue.gathering.gather_properties(asset.default_export)
    dcsc_props: PrimalDinoStatusComponent = ark.gathering.gather_dcsc_properties(asset.default_export)

    # Having no name or tag is an indication that this is an intermediate class, not a spawnable species
    name = (str(char_props.DescriptiveName[0]) or str(char_props.DinoNameTag[0])).strip()
    if not name:
        logger.debug(f"Species {asset.assetname} has no DescriptiveName or DinoNameTag - skipping")
        return None

    # Also consider anything that doesn't override any base status value as non-spawnable
    if not any(dcsc_props.has_override('MaxStatusValues', n) for n in ARK_STAT_INDEXES):
        logger.debug(f"Species {asset.assetname} has no overridden stats - skipping")
        return None

    assert asset.assetname and asset.default_export and asset.default_class and asset.default_class.fullname

    modid: str = asset.loader.get_mod_id(asset.assetname) or ''
    overrides = get_overrides_for_species(asset.assetname, modid)

    if overrides.skip_export:
        return None

    bp: str = asset.default_class.fullname
    if bp.endswith('_C'):
        bp = bp[:-2]

    # Replace names to match ASB's hardcoding of specific species
    name = overrides.descriptive_name or name

    # Variant information
    variants = get_variants_from_assetname(asset.assetname, overrides) | get_variants_from_species(proxy, overrides)
    if variants:
        if should_skip_from_variants(variants, overrides):
            return None
        name = adjust_name_from_variants(name, variants, overrides)

    species: Dict[str, Any] = dict(name=name, blueprintPath=bp)
    if variants:
        species['variants'] = tuple(sorted(variants))

    # Stat data
    species['fullStatsRaw'] = gather_stat_data(dcsc_props, ARK_STAT_INDEXES)

    # Set imprint multipliers
    stat_imprint_mults: List[float] = list()
    unique_mults = False
    for stat_index in ARK_STAT_INDEXES:
        imprint_mult = dcsc_props.DinoMaxStatAddMultiplierImprinting[stat_index]
        stat_imprint_mults.append(imprint_mult.rounded_value)

        # TODO: Optimize: Too many property look ups
        if DCSC_DEFAULTS.DinoMaxStatAddMultiplierImprinting[stat_index] != imprint_mult:
            unique_mults = True

    if unique_mults:
        species['statImprintMult'] = stat_imprint_mults

    # ImmobilizedBy format data
    immobilization_data = None
    try:
        immobilization_data = gather_immobilization_data(char_props, asset.loader)
    except (AssetNotFound, ModNotFound) as ex:
        logger.warning(f'Failure while gathering immobilization data for {asset.assetname}:\n\t{ex}')
    if immobilization_data is not None:
        species['immobilizedBy'] = immobilization_data

    # Breeding data
    if char_props.bCanHaveBaby[0]:  # TODO: Consider always including this data
        breeding_data = None
        try:
            breeding_data = gather_breeding_data(char_props, asset.loader)
        except (AssetNotFound, ModNotFound) as ex:
            logger.warning(f'Failure while gathering breeding data for {asset.assetname}:\n\t{ex}')
        if breeding_data:
            species['breeding'] = breeding_data

    # Color data
    if char_props.bUseColorization[0]:
        colors = None
        try:
            colors = gather_color_data(char_props, overrides)
        except (AssetNotFound, ModNotFound) as ex:
            logger.warning(f'Failure while gathering color data for {asset.assetname}:\n\t{ex}')
        if colors is not None:
            species['colors'] = colors

    # Taming data
    if char_props.bCanBeTamed[0] or True:  # ASB currently requires all species to have taming data
        taming = None
        try:
            taming = gather_taming_data(char_props, dcsc_props)
        except (AssetNotFound, ModNotFound) as ex:
            logger.warning(f'Failure while gathering taming data for {asset.assetname}:\n\t{ex}')
        if taming:
            species['taming'] = taming

    # Bone damage multipliers
    dmg_mults = None
    try:
        dmg_mults = gather_damage_mults(char_props)
    except (AssetNotFound, ModNotFound) as ex:
        logger.warning(f'Failure while gathering bone damage data for {asset.assetname}:\n\t{ex}')
    if dmg_mults:
        species['boneDamageAdjusters'] = dmg_mults

    # Misc data
    noSpeedImprint: bool = (dcsc_props.DinoMaxStatAddMultiplierImprinting[9] == 0)
    usesOxyWild = dcsc_props.bCanSuffocate[0]
    usesOxyTamed = True if usesOxyWild else dcsc_props.bCanSuffocateIfTamed[0]
    forceOxy = dcsc_props.bForceGainOxygen[0]
    doesntUseOxygen = not (usesOxyTamed or forceOxy)

    ETBHM = char_props.ExtraTamedBaseHealthMultiplier[0]
    TBHM = dcsc_props.TamedBaseHealthMultiplier[0] * ETBHM

    displayed_stats: int = 0

    for i in ARK_STAT_INDEXES:
        use_stat = not dcsc_props.DontUseValue[i]
        if use_stat and not (i == 3 and doesntUseOxygen):
            displayed_stats |= (1 << i)

    species['TamedBaseHealthMultiplier'] = cf(TBHM)
    species['NoImprintingForSpeed'] = noSpeedImprint
    species['doesNotUseOxygen'] = doesntUseOxygen
    species['displayedStats'] = displayed_stats

    stat_name_overrides = get_stat_name_overrides(dcsc_props)
    if stat_name_overrides:
        species['statNames'] = stat_name_overrides

    return species


def get_stat_name_overrides(dcsc: PrimalDinoStatusComponent) -> Dict[int, str]:
    names = dcsc.get('StatusValueNameOverrides', 0, fallback=None)
    if names is None:
        return dict()

    pairs = [(n, str(raw).strip()) for n, raw in enumerate(names.values)]
    output = {n: name for n, name in pairs if name}

    return output
