from functools import singledispatch
from typing import List, Optional, Set

from cachetools import LRUCache, cached

from ark.types import PrimalDinoCharacter, PrimalDinoSettings
from ue.asset import UAsset
from ue.gathering import gather_properties
from ue.loader import AssetLoader
from ue.properties import StructProperty

from .datatypes import ItemOverride

__all__ = [
    'collect_species_data',
]


@singledispatch
def collect_species_data(cls_name: str, loader: AssetLoader) -> List[ItemOverride]:
    '''
    Get food overrides for a species.
    '''
    asset = loader[cls_name]
    species: PrimalDinoCharacter = gather_properties(asset)
    try:
        settings = species.DinoSettingsClass[0]
    except ValueError:
        return []
    foods = _collect_settings_foods(settings)
    return foods


@collect_species_data.register
def collect_species_data_by_asset(asset: UAsset) -> List[ItemOverride]:
    species: PrimalDinoCharacter = gather_properties(asset)
    try:
        settings = species.DinoSettingsClass[0]
    except ValueError:
        return []
    foods = _collect_settings_foods(settings)
    return foods


@collect_species_data.register
def collect_species_data_by_proxy(species: PrimalDinoCharacter) -> List[ItemOverride]:
    try:
        settings = species.DinoSettingsClass[0]
    except ValueError:
        return []
    foods = _collect_settings_foods(settings)
    return foods


# cache is keyed by proxy's fullname
@cached(cache=LRUCache(maxsize=100), key=lambda proxy: proxy.get_source().fullname)
def _collect_settings_foods(proxy: PrimalDinoSettings) -> List[ItemOverride]:
    '''
    Get food overrides from a DinoSettings asset.
    Cached, as these are re-used by multiple species.
    '''
    # asset = loader[cls_name]
    # proxy: PrimalDinoSettings = gather_properties(asset)

    # Join base and extra entries
    normal_list = proxy.get('FoodEffectivenessMultipliers', 0, None)
    extra_list = proxy.get('ExtraFoodEffectivenessMultipliers', 0, None)
    foods: List[ItemOverride] = []
    if normal_list:
        foods.extend(eff for eff in (_collect_settings_effect(food) for food in normal_list.values) if eff is not None)
    if extra_list:
        foods.extend(eff for eff in (_collect_settings_effect(food) for food in extra_list.values) if eff is not None)

    # Remove duplicates, in reverse # TODO: Verify priority of duplicates
    bps: Set[str] = set()
    foods.reverse()
    for i, food in enumerate(foods):
        if food.bp in bps:
            del foods[i]

        bps.add(food.bp)

    foods.reverse()

    return foods


def _collect_settings_effect(food: StructProperty) -> Optional[ItemOverride]:
    v = food.as_dict()
    bp = v['FoodItemParent'].value.value and v['FoodItemParent'].value.value.fullname
    if not bp:
        return None
    o = ItemOverride(bp=bp)
    o.untamed_priority = float(v['UntamedFoodConsumptionPriority'])

    value = float(v['AffinityOverride'])
    if value != 0:
        o.overrides['affinity'] = value

    value = float(v['AffinityEffectivenessMultiplier'])
    o.mults['affinity'] = value if value != 0 else 1

    o.mults['health'] = float(v['HealthEffectivenessMultiplier'])
    o.mults['torpor'] = float(v['TorpidityEffectivenessMultiplier'])
    o.mults['food'] = float(v['FoodEffectivenessMultiplier'])
    o.mults['stamina'] = float(v['StaminaEffectivenessMultiplier'])

    return o
