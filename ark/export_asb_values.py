import math
from typing import *
import warnings
import logging
from dataclasses import dataclass, field

from ue.asset import UAsset
from ue.loader import AssetLoader
from ue.properties import LinearColor
from ark.properties import stat_value, PriorityPropDict
import ark.mod

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

ASB_STAT_INDEXES = (0, 1, 3, 4, 7, 8, 9, 2)
ARK_STAT_INDEXES = list(range(12))

BASE_VALUES = (100, 100, 100, 100, 100, 100, 0, 0, 0, 0, 0, 0)
IW_VALUES = (0, 0, 0.06, 0, 0, 0, 0, 0, 0, 0, 0, 0)
IMPRINT_VALUES = (0.2, 0, 0.2, 0, 0.2, 0.2, 0, 0.2, 0.2, 0.2, 0, 0)
EXTRA_MULTS_VALUES = (1.35, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
DONTUSESTAT_VALUES = (0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1)
CANLEVELUP_VALUES = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

FEMALE_MINTIMEBETWEENMATING_DEFAULT = 64800.0
FEMALE_MAXTIMEBETWEENMATING_DEFAULT = 172800.0

BABYGESTATIONSPEED_DEFAULT = 0.000035

DEFAULT_COLOR_REGIONS = [0, 0, 0, 0, 0, 0]

# Stats that are represented as percentages instead
IS_PERCENT_STAT = (0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1)

remove_default_values = True  # TODO: probably set to False for production runs

cached_color_defs: List[Tuple[str, Tuple[float, float, float, float]]] = []


# TODO: Move to somewhere more global, probably alongside gather_properties
def create_dict(prop):
    return dict((str(v.name), v.value) for v in prop.values)


def convert_linear_color(lcolor: LinearColor):
    # Uses rounded as it matches the export file values
    return (lcolor.r.rounded, lcolor.g.rounded, lcolor.b.rounded, lcolor.a.rounded)


def read_colour_definitions(asset):
    props = ark.mod.gather_properties(asset)

    color_defs = []
    for color_def in props['ColorDefinitions'][0][-1].values:
        color_dict = create_dict(color_def)
        color_defs.append((str(color_dict['ColorName']), convert_linear_color(color_dict['ColorValue'].values[0])))

    return color_defs


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


def gather_breeding_data(props, loader: AssetLoader) -> Dict[str, Any]:
    data: Dict[str, Any] = dict(gestationTime=0, incubationTime=0)

    gestation_breeding = stat_value(props, 'bUseBabyGestation', 0, False)
    has_eggs = False

    if props['FertilizedEggItemsToSpawn'][0] and props['FertilizedEggItemsToSpawn'][0][-1].values:
        # eggs = list(filter(lambda v: v and str(v) != 'None', props['FertilizedEggItemsToSpawn'][0][-1].values))
        eggs = [egg for egg in props['FertilizedEggItemsToSpawn'][0][-1].values if str(egg) != 'None']
        has_eggs = bool(eggs)

    if gestation_breeding:
        gestation_speed = stat_value(props, 'BabyGestationSpeed', 0, BABYGESTATIONSPEED_DEFAULT)
        extra_gestation_speed_m = stat_value(props, 'ExtraBabyGestationSpeedMultiplier', 0, 1.0)

        # TODO: Verify if these should really default to 1 - seems odd
        gestation_speed = gestation_speed or 1
        extra_gestation_speed_m = extra_gestation_speed_m or 1
        # 'gestationTime' = 1 / (Baby Gestation Speed × Extra Baby Gestation Speed Multiplie)
        data['gestationTime'] = (1 / gestation_speed /
                                 extra_gestation_speed_m) if gestation_speed and extra_gestation_speed_m else None

    elif has_eggs:
        fert_egg_asset = loader.load_related(eggs[0])
        fert_egg_props = ark.mod.gather_properties(fert_egg_asset)
        egg_decay = stat_value(fert_egg_props, 'EggLoseDurabilityPerSecond', 0, 1)
        extra_egg_decay_m = stat_value(fert_egg_props, 'ExtraEggLoseDurabilityPerSecondMultiplier', 0, 1)

        # 'incubationTime' = 100 / (Egg Lose Durability Per Second × Extra Egg Lose Durability Per Second Multiplier)
        data['incubationTime'] = (100 / egg_decay / extra_egg_decay_m) if egg_decay and extra_egg_decay_m else None
        data['eggTempMin'] = stat_value(fert_egg_props, 'EggMinTemperature', 0)
        data['eggTempMax'] = stat_value(fert_egg_props, 'EggMaxTemperature', 0)

    # 'maturationTime' = 1 / (Baby Age Speed × Extra Baby Age Speed Multiplier)
    baby_age_speed = stat_value(props, 'BabyAgeSpeed', 0, 1)
    extra_baby_age_speed_m = stat_value(props, 'ExtraBabyAgeSpeedMultiplier', 0, 1)

    data['maturationTime'] = (1 / baby_age_speed / extra_baby_age_speed_m) if baby_age_speed and extra_baby_age_speed_m else None
    data['matingCooldownMin'] = stat_value(props, 'NewFemaleMinTimeBetweenMating', 0, FEMALE_MINTIMEBETWEENMATING_DEFAULT)
    data['matingCooldownMax'] = stat_value(props, 'NewFemaleMaxTimeBetweenMating', 0, FEMALE_MAXTIMEBETWEENMATING_DEFAULT)

    return data


def ensure_color_data(loader: AssetLoader):
    global cached_color_defs
    if cached_color_defs: return
    cached_color_defs = read_colour_definitions(loader['/Game/PrimalEarth/CoreBlueprints/COREMEDIA_PrimalGameData_BP'])


def gather_color_data(props, loader: AssetLoader):
    # TODO: Handle mod color definitions

    male_colorset_asset = loader.load_related(props['RandomColorSetsMale'][0][-1])
    male_colorset_props = ark.mod.gather_properties(male_colorset_asset)

    # Female Colorset
    # female_colorset_asset = loader.load_related(props['RandomColorSetsFemale'][0][-1])
    # female_colorset_props = ark.mod.gather_properties(female_colorset_asset)

    colors = list()
    for i, region in enumerate(DEFAULT_COLOR_REGIONS):
        prevent_region = stat_value(props, 'PreventColorizationRegions', i, region)
        color: Dict[str, Any] = dict()
        color_ids: List[int] = list()

        if prevent_region:
            color['name'] = None
        elif i not in male_colorset_props['ColorSetDefinitions']:
            color['name'] = None
        else:
            color_set_defs = create_dict(male_colorset_props['ColorSetDefinitions'][i][-1])

            try:
                color['name'] = str(color_set_defs['RegionName'])
            except:
                color['name'] = 'Unknown Region Name'

            if 'ColorEntryNames' in color_set_defs:
                # If one color doesn't exist, this entire region is nulled
                # Needs to be better implemented to support invalid color names
                try:
                    for color_name in color_set_defs['ColorEntryNames'].values:
                        color_id = [c_def[0] for c_def in cached_color_defs].index(str(color_name)) + 1
                        if color_id not in color_ids:
                            color_ids.append(color_id)
                except:
                    warnings.warn(f'{color_name} was not found in the Color definitions')

        if not color_ids:
            color['name'] = None

        color['colorIds'] = color_ids
        colors.append(color)

    return colors


def gather_taming_data(props) -> Dict[str, Any]:
    data: Dict[str, Any] = dict()

    # Currently unable to gather the foods list
    eats: Optional[List[str]] = None
    favorite_kibble: Optional[str] = None
    special_food_values: Optional[List[Dict[str, Dict[str, List[int]]]]] = None

    can_tame = stat_value(props, 'bCanBeTamed', 0, True)
    can_knockout = stat_value(props, 'bCanBeTorpid', 0, True)
    data['nonViolent'] = stat_value(props, 'bSupportWakingTame', 0, False) and can_tame
    data['violent'] = not stat_value(props, 'bPreventSleepingTame', 0, False) and can_tame and can_knockout

    if can_tame or True:
        data['tamingIneffectiveness'] = stat_value(props, 'TameIneffectivenessByAffinity', 0, 20.0)
        data['affinityNeeded0'] = stat_value(props, 'RequiredTameAffinity', 0, 100)
        data['affinityIncreasePL'] = stat_value(props, 'RequiredTameAffinityPerBaseLevel', 0, 5.0)

        torpor_depletion = stat_value(props, 'KnockedOutTorpidityRecoveryRateMultiplier', 0, 3.0) * stat_value(
            props, 'RecoveryRateStatusValue', 2, 0.00)

        if data['violent']:
            data['torporDepletionPS0'] = -torpor_depletion
        if data['nonViolent']:
            data['wakeAffinityMult'] = stat_value(props, 'WakingTameFoodAffinityMultiplier', 0, 1.6)
            data['wakeFoodDeplMult'] = stat_value(props, 'WakingTameFoodConsumptionRateMultiplier', 0, 2.0)

        data['foodConsumptionBase'] = -stat_value(props, 'BaseFoodConsumptionRate', 0, -0.025000)  # pylint: disable=invalid-unary-operand-type
        data['foodConsumptionMult'] = stat_value(props, 'ProneWaterFoodConsumptionMultiplier', 0, 1.00)

        if eats is not None:
            data['eats'] = eats
        if favorite_kibble is not None:
            data['favoriteKibble'] = favorite_kibble
        # data['specialFoodValues'] = special_food_values # TODO: Temporarily commented out

    return data


@dataclass
class ImmobilizingItem:
    name: str
    minWeight: Optional[float] = 0
    maxWeight: Optional[float] = math.inf
    minMass: Optional[float] = 0
    maxMass: Optional[float] = math.inf
    ignoreTags: List[str] = field(default_factory=list)
    ignoreBosses: bool = False


immobilization_itemdata: List[ImmobilizingItem] = [
    ImmobilizingItem(name="Bola", maxWeight=150),
    ImmobilizingItem(name="Chain Bola", minWeight=148, maxWeight=900, ignoreBosses=True),
    ImmobilizingItem(name="Bear Trap", maxMass=201, ignoreTags=['Mek', 'MegaMek'], ignoreBosses=True),
    ImmobilizingItem(name="Large Bear Trap", minMass=150, ignoreBosses=True),
    ImmobilizingItem(name="Plant Species Y", maxMass=300, ignoreBosses=True),
]


def ensure_immobilization_itemdata(loader: AssetLoader) -> List[ImmobilizingItem]:
    global immobilization_itemdata  #pylint: disable=global-statement
    if immobilization_itemdata:
        return immobilization_itemdata

    # TODO: Implement search for buffs and structures that can immobilize
    # bImmobilizeTarget for buffs (including bolas, etc)
    raise NotImplementedError


def gather_immobilization_data(props: PriorityPropDict, loader: AssetLoader, mass) -> List[str]:
    items = ensure_immobilization_itemdata(loader)
    immobilizedBy: List[Any] = []
    if stat_value(props, 'bPreventImmobilization', 0, False):
        return immobilizedBy
    if stat_value(props, 'bIsWaterDino', 0, False):
        return immobilizedBy
    weight = stat_value(props, 'DragWeight', 0, 35)
    is_boss = stat_value(props, 'bIsBossDino', 0, False)
    tag = stat_value(props, 'CustomTag', 0, None)
    for item in items:
        if item.minWeight > weight or item.maxWeight <= weight:
            continue
        if item.minMass > mass or item.maxMass <= mass:
            continue
        if is_boss:
            continue
        if tag in item.ignoreTags:  # pylint: disable=unsupported-membership-test
            continue
        immobilizedBy.append(item.name)

    return immobilizedBy


def values_for_species(asset: UAsset,
                       props,
                       allFields=False,
                       fullStats=False,
                       includeColor=False,
                       includeBreeding=True,
                       includeImmobilize=True,
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
    tag = stat_value(props, 'CustomTag', 0, None) or f'<unknown tag for {asset.default_class.name}'

    # Drag weight is used for immobilization calculation and arena entry
    dragWeight = stat_value(props, 'DragWeight', 0, None)

    species = dict(name=name, blueprintPath=bp)  #, tag=tag, dragWeight=dragWeight

    # Stat data
    statsField = 'fullStatsRaw' if fullStats else 'statsRaw'
    statIndexes = ARK_STAT_INDEXES if fullStats else ASB_STAT_INDEXES
    species[statsField] = gather_stat_data(props, statIndexes)

    if includeImmobilize:
        # ImmobilizedBy format data
        mass = get_species_mass(asset)
        immobilization_data = gather_immobilization_data(props, asset.loader, mass)
        if immobilization_data:
            species['immobilizedBy'] = immobilization_data

    if includeBreeding:
        # Breeding data
        if stat_value(props, 'bCanHaveBaby', 0, False):  # TODO: Consider always including this data
            breeding_data = gather_breeding_data(props, asset.loader)  # type: ignore
            if breeding_data:
                species['breeding'] = breeding_data

    if includeColor:
        # Color data
        ensure_color_data(asset.loader)
        if stat_value(props, 'bUseColorization', False):
            colors = gather_color_data(props, asset.loader)
            if colors:
                species['colors'] = colors

    if includeTaming:
        # Taming data
        # ASB currently requires all species to have taming data
        if stat_value(props, 'bCanBeTamed', True) or True:
            taming = gather_taming_data(props)
            if taming:
                species['taming'] = taming

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
