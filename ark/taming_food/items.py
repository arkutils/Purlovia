'''Methods for gathering the effects of items in the game.'''

from operator import attrgetter
from typing import Iterable, Optional, cast

from ark.mod import get_core_mods
from ark.stats import Stat, stat_enum_to_stat
from ark.types import PrimalItem
from ue.gathering import gather_properties
from ue.hierarchy import find_sub_classes, get_parent_class
from ue.loader import AssetLoader
from ue.properties import ByteProperty, FloatProperty, StructProperty
from ue.tree import is_fullname_an_asset
from utils.tree import IndexedTree

from .datatypes import Item, ItemStatEffect

__all__ = [
    'gather_items',
    'food_items',
]

food_items: IndexedTree[Item] = IndexedTree(
    root=Item(bp=PrimalItem.get_ue_type(), modid=''),
    key_fn=attrgetter('bp'),
)


def gather_items(loader: AssetLoader, *, limit_modids: Optional[Iterable[str]] = None):
    '''
    Scan all items and collect their stat effects.
    Results are kept in the tree `ark.taming.items`.
    '''
    food_items.clear()

    # Cache core mod list
    core_mods = get_core_mods()

    for cls_name in find_sub_classes(PrimalItem.get_ue_type()):
        # Get modid and check if we want to gather it
        modid = loader.get_mod_id(cls_name) or ''
        if modid in core_mods:
            modid = ''
        if limit_modids is not None and modid not in limit_modids:
            continue

        # Create item
        item = Item(bp=cls_name, modid=modid)
        parent = get_parent_class(cls_name)
        try:
            food_items.add(parent, item)
        except KeyError:
            print(f'Failed to add item {item} to {parent}:')
            raise

        # Only look up stats if this is an asset
        if not is_fullname_an_asset(cls_name):
            continue

        # Collect stat effects, altering the object
        asset = loader[cls_name]
        proxy: PrimalItem = gather_properties(asset)
        item.name = str(proxy.DescriptiveNameBase[0])
        _collect_item_effects(item, proxy)


def _collect_item_effects(item: Item, proxy: PrimalItem):
    mult = proxy.GlobalTameAffinityMultiplier[0]
    item.affinity_mult = float(mult) or 1.0

    # Record food/water value when used in custom recipes
    if proxy.bIsCookingIngredient[0]:
        _set_dict_if_not_zero(item.ingredient_stats, Stat.Health, proxy.Ingredient_HealthIncreasePerQuantity[0])
        _set_dict_if_not_zero(item.ingredient_stats, Stat.Stamina, proxy.Ingredient_StaminaIncreasePerQuantity[0])
        _set_dict_if_not_zero(item.ingredient_stats, Stat.Food, proxy.Ingredient_FoodIncreasePerQuantity[0])
        _set_dict_if_not_zero(item.ingredient_stats, Stat.Water, proxy.Ingredient_WaterIncreasePerQuantity[0])
        _set_dict_if_not_zero(item.ingredient_stats, Stat.Weight, proxy.Ingredient_WeightIncreasePerQuantity[0])

    # Record some flags so we know how the item can be used
    item.preventDinoUse = bool(proxy.get('bPreventUseByDinos', fallback=False))
    item.preventDinoAutoUse = bool(proxy.get('bPreventDinoAutoConsume', fallback=False))

    # Gather on-use effects
    use_item_stats = proxy.get('UseItemAddCharacterStatusValues', fallback=None)
    if use_item_stats:
        entry: StructProperty
        for entry in use_item_stats.values:
            effect = _collect_status_effects(entry)
            stat = stat_enum_to_stat(cast(ByteProperty, entry.get_property('StatusValueType')))
            item.use_item_stats[stat] = effect


def _collect_status_effects(effect: StructProperty) -> ItemStatEffect:
    v = effect.as_dict()
    o = ItemStatEffect()
    o.base = float(v['BaseAmountToAdd'])
    o.speed = float(v['AddOverTimeSpeed']) if v['bAddOverTime'] else 0
    return o


def _set_dict_if_not_zero(target: dict, key: Stat, value: float | FloatProperty):
    if value != 0:
        target[key] = float(value)
