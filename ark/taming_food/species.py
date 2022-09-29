'''Methods for gathering food overrides from species.'''

from functools import singledispatch
from typing import cast

from cachetools import LRUCache, cached

from ark.stats import Stat
from ark.types import PrimalDinoCharacter, PrimalDinoSettings
from ue.asset import UAsset
from ue.gathering import gather_properties
from ue.loader import AssetLoader
from ue.properties import ArrayProperty, StructProperty

from .datatypes import SpeciesFoods, SpeciesItemOverride

__all__ = [
    'collect_species_data',
]


@singledispatch
def collect_species_data(input, loader: AssetLoader = None) -> SpeciesFoods:
    raise NotImplementedError("collect_species_data() is not implemented for these input types")


@collect_species_data.register
def collect_species_data_by_cls_name(cls_name: str, loader: AssetLoader) -> SpeciesFoods:
    '''
    Get food overrides for a species.
    '''
    asset = loader[cls_name]
    species: PrimalDinoCharacter = gather_properties(asset)
    return collect_species_data_by_proxy(species)


@collect_species_data.register
def collect_species_data_by_asset(asset: UAsset) -> SpeciesFoods:
    species: PrimalDinoCharacter = gather_properties(asset)
    return collect_species_data_by_proxy(species)


@collect_species_data.register
def collect_species_data_by_proxy(species: PrimalDinoCharacter) -> SpeciesFoods:
    child_settings: PrimalDinoSettings | None = species.get('BabyDinoSettings', 0, None)
    adult_settings: PrimalDinoSettings | None = species.get('AdultDinoSettings', 0, None)
    default_settings: PrimalDinoSettings | None = species.get('DinoSettingsClass', 0, None)

    adult_foods = _gather_combined_foods_from(adult_settings, default_settings)
    child_foods = _gather_combined_foods_from(child_settings, default_settings)

    result = SpeciesFoods(bp=species.get_source().fullname)
    result.adult_eats = adult_foods

    # Only include child foods if they are
    if child_foods is not adult_foods:
        result.child_eats = child_foods

    return result


def _settings_cache_key(age_settings: PrimalDinoSettings | None, default_settings: PrimalDinoSettings | None):
    return (age_settings.get_source().fullname if age_settings else None,
            default_settings.get_source().fullname if default_settings else None)


# cache is keyed by (age_settings bp, default_settings bp)
@cached(cache=LRUCache(maxsize=100), key=_settings_cache_key)
def _gather_combined_foods_from(age_settings: PrimalDinoSettings | None,
                                default_settings: PrimalDinoSettings | None) -> list[SpeciesItemOverride]:
    '''
    Gather correctly combined combination of food and extra food overrides from a combination of settings classes.
    This function is cached by the BP names of the two settings classes.
    '''
    foods = _gather_foods_from(age_settings, default_settings, 'FoodEffectivenessMultipliers')
    extras = _gather_foods_from(age_settings, default_settings, 'ExtraFoodEffectivenessMultipliers')

    return _combine_food_and_extra(foods, extras)


def _gather_foods_from(age_settings: PrimalDinoSettings | None, default_settings: PrimalDinoSettings | None,
                       field: str) -> list[SpeciesItemOverride]:

    values: ArrayProperty | None = None
    if age_settings is not None:
        values = age_settings.get(field, 0, None)
    if values is None and default_settings is not None:
        values = default_settings.get(field, 0, None)

    if not values:
        return []

    return _process_foods(values)


def _process_foods(array: ArrayProperty | None) -> list[SpeciesItemOverride]:
    '''
    Get processed food overrides from a field like FoodEffectivenessMultipliers or ExtraFoodEffectivenessMultipliers.
    '''
    if not array:
        return []

    results: list[SpeciesItemOverride] = []
    for item in array.values:
        result = _collect_stat_effect(cast(StructProperty, item))
        if result:
            results.append(result)

    return results


def _combine_food_and_extra(foods: list[SpeciesItemOverride], extras: list[SpeciesItemOverride]) -> list[SpeciesItemOverride]:
    # Collect everything in correct override order
    result: list[SpeciesItemOverride] = []
    if foods:
        result.extend(food for food in foods if food)
    if extras:
        result.extend(extra for extra in extras if extra)

    # Remove duplicates, in reverse # TODO: Verify priority of duplicates
    bps: set[str] = set()
    for i in range(len(result) - 1, -1, -1):
        bp = result[i].bp
        if bp in bps:
            del result[i]

        bps.add(bp)

    return result


def _collect_stat_effect(food: StructProperty) -> SpeciesItemOverride | None:
    v = food.as_dict()
    bp = v['FoodItemParent'].value.value and v['FoodItemParent'].value.value.fullname
    if not bp:
        return None
    o = SpeciesItemOverride(bp=bp)
    o.untamed_priority = float(v['UntamedFoodConsumptionPriority'])

    o.affinity_override = float(v['AffinityOverride'])

    aem = float(v['AffinityEffectivenessMultiplier'])
    o.affinity_mult = aem if aem != 0 else 1

    o.mults[Stat.Health] = float(v['HealthEffectivenessMultiplier'])
    o.mults[Stat.Stamina] = float(v['StaminaEffectivenessMultiplier'])
    o.mults[Stat.Torpidity] = float(v['TorpidityEffectivenessMultiplier'])
    o.mults[Stat.Food] = float(v['FoodEffectivenessMultiplier'])

    return o
