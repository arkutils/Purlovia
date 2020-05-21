'''Parse and cache taming food data for use in extraction phases.'''

from dataclasses import dataclass, field
from functools import lru_cache
from operator import itemgetter
from typing import Any, Dict, List, Optional, Set, Tuple

from ue.gathering import gather_properties
from ue.hierarchy import find_parent_classes, find_sub_classes
from ue.loader import AssetLoader
from ue.properties import StructProperty
from ue.tree import is_fullname_an_asset
from utils.tree import IndexedTree

from .types import PrimalDinoCharacter, PrimalDinoSettings, PrimalItem

__all__ = [
    'TamingFoodHandler',
]


class TamingFoodHandler:
    def __init__(self, loader: AssetLoader):
        self.loader = loader


@dataclass(init=False)
class ItemStatEffect:
    base: float
    speed: Optional[float] = None


@dataclass(init=False)
class ItemOverride:
    bp: str
    priority: float
    food_mult: float
    torpor_mult: float
    affinity_mult: float
    affinity_override: float


@dataclass
class Item:
    bp: str
    name: Optional[str] = field(default=None, init=False)
    food: Optional[ItemStatEffect] = field(default=None, init=False)
    torpor: Optional[ItemStatEffect] = field(default=None, init=False)
    affinity: Optional[ItemStatEffect] = field(default=None, init=False)


items: IndexedTree[Item] = IndexedTree(
    Item(bp=PrimalItem.get_ue_type()),
    lambda item: item.bp,
)


def _gather_items(loader: AssetLoader):
    items.clear()

    for cls_name in find_sub_classes(PrimalItem.get_ue_type()):
        if cls_name.startswith('/Game/Mods/'): continue  # REMOVE ME!!!

        item = Item(bp=cls_name)
        parent = _get_parent(cls_name)
        items.add(parent, item)

        if not is_fullname_an_asset(cls_name): continue

        asset = loader[cls_name]
        proxy: PrimalItem = gather_properties(asset)
        item.name = str(proxy.DescriptiveNameBase[0])
        _collect_item_effects(item, proxy)


def _collect_species_data(cls_name: str, loader: AssetLoader) -> List[ItemOverride]:
    settings_cls = _get_species_settings_cls(cls_name, loader)
    if not settings_cls:
        return []
    foods = _collect_settings_foods(settings_cls, loader)
    return foods


def _get_species_settings_cls(cls_name: str, loader: AssetLoader) -> Optional[str]:
    asset = loader[cls_name]
    proxy: PrimalDinoCharacter = gather_properties(asset)
    settings = proxy.get('DinoSettingsClass', 0, fallback=None)
    if settings is None:
        return None
    return settings.value.value.fullname


@lru_cache(maxsize=100)
def _collect_settings_foods(cls_name: str, loader: AssetLoader) -> List[ItemOverride]:
    asset = loader[cls_name]
    proxy: PrimalDinoSettings = gather_properties(asset)

    # Join base and extra entries
    normal_list = proxy.get('FoodEffectivenessMultipliers', 0, None)
    extra_list = proxy.get('ExtraFoodEffectivenessMultipliers', 0, None)
    foods: List[ItemOverride] = []
    if normal_list:
        foods.extend(_collect_settings_effect(food) for food in normal_list.values)
    if extra_list:
        foods.extend(_collect_settings_effect(food) for food in extra_list.values)

    # Remove duplicates, in reverse # TODO: Verify priority of duplicates
    bps: Set[str] = set()
    foods.reverse()
    for i, food in enumerate(foods):
        if food.bp in bps:
            del foods[i]

        bps.add(food.bp)

    foods.reverse()

    return foods


def _collect_settings_effect(food: StructProperty) -> ItemOverride:
    v = food.as_dict()
    o = ItemOverride()
    o.bp = v['FoodItemParent'].value.value.fullname
    o.priority = float(v['UntamedFoodConsumptionPriority'])
    o.food_mult = float(v['FoodEffectivenessMultiplier'])
    o.torpor_mult = float(v['TorpidityEffectivenessMultiplier'])
    o.affinity_mult = float(v['AffinityEffectivenessMultiplier'])
    o.affinity_override = float(v['AffinityOverride'])
    return o


def _get_parent(cls_name: str) -> str:
    parent = next(find_parent_classes(cls_name, include_self=False))
    return parent


def _collect_item_effects(item: Item, proxy: PrimalItem):
    inputs = proxy.get('UseItemAddCharacterStatusValues', 0, fallback=None)
    if not inputs: return

    for add in inputs.values:
        effect = _collect_status_effects(add)
        stat = add.get_property('StatusValueType', 0).get_enum_value_name()
        if stat == 'Food':
            item.food = effect
        elif stat == 'Torpidity':
            item.torpor = effect


def _collect_status_effects(effect: StructProperty) -> ItemStatEffect:
    v = effect.as_dict()
    o = ItemStatEffect()
    o.base = int(v['BaseAmountToAdd'])
    if v['bAddOverTime'] and v['AddOverTimeSpeed'] != 0:
        o.speed = float(v['AddOverTimeSpeed'])
    else:
        o.speed = None
    return o


def print_species_effects(cls_name: str, loader: AssetLoader):
    foods = _collect_species_data(cls_name, loader)
    data: List[Dict[str, Any]] = [vars(food) for food in foods]
    for food in data:
        bp = food['bp']
        bp = bp[bp.rfind('.') + 1:]
        bp = bp.replace('PrimalItemConsumable_', '')
        if bp.endswith('_C'): bp = bp[:-2]
        food['bp'] = bp

    headers = ('classname', 'pri', 'food*', 'torp*', 'aff*', 'aff=')

    def affinity_calc(food: Dict[str, Any]):
        return food['affinity_override']  # * food['affinity_mult']

    values = [food.values() for food in sorted(data, reverse=True, key=affinity_calc)]

    from tabulate import tabulate
    table = tabulate([headers, *values], headers='firstrow')
    print(table)
