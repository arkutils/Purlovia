'''Parse and cache taming food data for use in extraction phases.'''

from dataclasses import dataclass, field
from functools import lru_cache
from math import ceil
from operator import attrgetter, itemgetter
from typing import Any, Dict, Iterable, Iterator, List, Optional, Set

from config import get_global_config
from ue.gathering import gather_properties
from ue.hierarchy import find_parent_classes, find_sub_classes
from ue.loader import AssetLoader
from ue.properties import StructProperty
from ue.tree import is_fullname_an_asset
from utils.tree import IndexedTree

from .types import PrimalDinoCharacter, PrimalDinoSettings, PrimalItem

__all__ = (
    'gather_items',
    'collect_species_data',
    'evaluate_food_for_species',
    'Item',
)

# Potentially interesting species for testing taming foods:
# Equus, Megatherium, Tuso, Giant Queen Bee... and eventually Gacha


@dataclass(eq=True, unsafe_hash=True)
class ItemStatEffect:
    base: float = field(default=0)
    speed: float = field(default=0)

    def __str__(self):
        speed = f" @ {self.speed}" if self.speed else ''
        return f"{self.base:6.3f}{speed}"


@dataclass()
class ItemOverride:
    bp: str
    priority: float = field(default=0, init=False)
    food_mult: float = field(default=0, init=False)
    torpor_mult: float = field(default=0, init=False)
    affinity_mult: float = field(default=0, init=False)
    affinity_override: float = field(default=0, init=False)


@dataclass(eq=True, unsafe_hash=True)
class Item:
    bp: str
    modid: str
    name: str = field(default='')
    food: ItemStatEffect = field(default_factory=ItemStatEffect, init=False)
    torpor: ItemStatEffect = field(default_factory=ItemStatEffect, init=False)
    affinity: ItemStatEffect = field(default_factory=ItemStatEffect, init=False)


items: IndexedTree[Item] = IndexedTree(
    root=Item(bp=PrimalItem.get_ue_type(), modid=''),
    key_fn=attrgetter('bp'),
)


def gather_items(loader: AssetLoader, *, limit_modids: Optional[Iterable[str]] = None):
    '''
    Scan all items and collect their stat effects.
    Results are kept in the tree `ark.taming.items`.
    '''
    items.clear()
    config = get_global_config()

    for cls_name in find_sub_classes(PrimalItem.get_ue_type()):
        # Get modid and check if we want to gather it
        modid = loader.get_mod_id(cls_name) or ''
        if modid in config.official_mods.ids():
            modid = ''
        if limit_modids is not None and modid not in limit_modids:
            continue

        # Create item
        item = Item(bp=cls_name, modid=modid)
        parent = _get_parent(cls_name)
        items.add(parent, item)

        # Only look up stats if this is an asset
        if not is_fullname_an_asset(cls_name):
            continue

        # Collect stat effects, altering the object
        asset = loader[cls_name]
        proxy: PrimalItem = gather_properties(asset)
        item.name = str(proxy.DescriptiveNameBase[0])
        _collect_item_effects(item, proxy)


def collect_species_data(cls_name: str, loader: AssetLoader) -> List[ItemOverride]:
    '''
    Get food overrides for a species.
    '''
    settings_cls = _get_species_settings_cls(cls_name, loader)
    if not settings_cls:
        return []
    foods = _collect_settings_foods(settings_cls, loader)
    return foods


def _get_species_settings_cls(cls_name: str, loader: AssetLoader) -> Optional[str]:
    '''
    Get the DinoSettings class for a species.
    '''
    asset = loader[cls_name]
    proxy: PrimalDinoCharacter = gather_properties(asset)
    settings = proxy.get('DinoSettingsClass', 0, fallback=None)
    if settings is None:
        return None
    return settings.value.value.fullname


@lru_cache(maxsize=100)
def _collect_settings_foods(cls_name: str, loader: AssetLoader) -> List[ItemOverride]:
    '''
    Get food overrides from a DinoSettings asset.
    Cached, as these are re-used by multiple species.
    '''
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
    o = ItemOverride(bp=v['FoodItemParent'].value.value.fullname)
    o.priority = float(v['UntamedFoodConsumptionPriority'])
    o.food_mult = float(v['FoodEffectivenessMultiplier'])
    o.torpor_mult = float(v['TorpidityEffectivenessMultiplier'])
    o.affinity_mult = float(v['AffinityEffectivenessMultiplier'])
    o.affinity_override = float(v['AffinityOverride'])
    return o


def _get_parent(cls_name: str) -> str:
    '''
    Get the immediate parent of a given class.
    '''
    parent = next(find_parent_classes(cls_name, include_self=False))
    return parent


def _collect_item_effects(item: Item, proxy: PrimalItem):
    inputs = proxy.get('UseItemAddCharacterStatusValues', 0, fallback=None)
    if not inputs:
        return

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
    o.speed = float(v['AddOverTimeSpeed']) if v['bAddOverTime'] else 0
    return o


def _bp_to_clean_class(bp: str):
    bp = bp[bp.rfind('.') + 1:]
    bp = bp.replace('PrimalItemConsumable_', '')
    if bp.endswith('_C'):
        bp = bp[:-2]
    return bp


def print_species_overrides(foods: List[ItemOverride], sort=True):
    data: List[Dict[str, Any]] = [vars(food) for food in foods]
    for food in data:
        food['bp'] = _bp_to_clean_class(food['bp'])

    headers = ('classname', 'pri', 'food*', 'torp*', 'aff*', 'aff=')
    if sort:
        data = sorted(data, reverse=True, key=itemgetter('affinity_override'))
    values = [food.values() for food in data]

    from tabulate import tabulate
    table = tabulate([headers, *values], headers='firstrow')
    print(table)


def print_eval_by_affinity(evals: List[Item]):
    data = [(item.food.base, item.affinity.base, _bp_to_clean_class(item.bp)) for item in evals if item.affinity.base]
    data.sort(reverse=True, key=itemgetter(0))  # sort by food first
    data.sort(reverse=True, key=itemgetter(1))  # and primarily by affinity
    headers = ('food', 'aff', 'class')

    from tabulate import tabulate
    table = tabulate([headers, *data], headers='firstrow')
    print(table)


def print_results_for_species(species: str, loader: AssetLoader):
    proxy: PrimalDinoCharacter = gather_properties(loader[species])
    affinity_required = float(proxy.RequiredTameAffinity[0] + proxy.RequiredTameAffinityPerBaseLevel[0] * 149) / 2

    def items_to_tame(item: Item):
        return ceil(affinity_required / item.affinity.base)

    evals = evaluate_food_for_species(species, loader)
    data = [(item.food.base, item.affinity.base, items_to_tame(item), _bp_to_clean_class(item.bp)) for item in evals
            if item.affinity.base]
    data.sort(reverse=True, key=itemgetter(0))  # sort by food first
    data.sort(reverse=True, key=itemgetter(1))  # and primarily by affinity
    headers = ('food', 'aff', 'need', 'class')

    from tabulate import tabulate
    table = tabulate([headers, *data], headers='firstrow')
    print(f"{species}:  (needs {affinity_required} affinity @ level 150)")
    print(table)


def print_item_effects(item: Item):
    print(f"{item.name}:")
    print(f"      Food: {item.food if item.food else '-'}")
    print(f"    Torpor: {item.torpor if item.torpor else '-'}")
    print(f"  Affinity: {item.affinity if item.affinity else '-'}")


def apply_species_overrides_to_item(item: Item, overrides: List[ItemOverride]) -> Item:
    '''
    Apply relevant overrides (from a species/settings) to an item.
    '''
    # Don't actually know anything about how this works... so we guess!

    # Try to match the item to all of the overrides in a most-specific-first manner.
    for cls_name in find_parent_classes(item.bp, include_self=True):
        for food in overrides:
            if food.bp == cls_name:
                return _apply_override_to_item(item, food)

    return item


def _apply_override_to_item(item: Item, override: ItemOverride):
    out = Item(bp=item.bp, name=item.name, modid=item.modid)

    def combine_stat(a: ItemStatEffect, b: float) -> ItemStatEffect:
        return ItemStatEffect(base=a.base * b, speed=a.speed)

    out.food = combine_stat(item.food, override.food_mult)
    out.torpor = combine_stat(item.torpor, override.torpor_mult)

    out.affinity = ItemStatEffect(base=override.affinity_override)
    # TODO: is there any use for affinity_mult?

    return out


def evaluate_food_for_species(cls_name: str, loader: AssetLoader, *,
                              limit_modids: Optional[Iterable[str]] = None) -> Iterator[Item]:
    '''
    Search for all taming foods relevant to the given species, and their effects.
    '''
    config = get_global_config()
    overrides = collect_species_data(cls_name, loader)
    for item in items.values():
        # Get modid of item and check if we want to include it
        if limit_modids is not None and item.modid not in limit_modids:
            continue

        # Apply overrides to the item
        effect = apply_species_overrides_to_item(item, overrides)

        # Ignore if it has no relevant effect
        if effect.food.base == 0 and effect.affinity.base == 0:
            continue

        yield effect


@dataclass
class ItemStatus:
    bp: str
    uses: int = field(default=0, init=False)
    sub_uses: int = field(default=0, init=False)
    food: float
    affinity: float


def clean_eval_items(evals: List[Item], *, limit_modids: Optional[Iterable[str]] = None):
    '''
    Clean up evaluated foods for a species.

    This removes items if they can be completely and correctly represented by a parent.
    '''

    # Make a tree parallel to the item tree, for collecting status (from only listed mods)
    def convert_node(item: Item) -> Optional[ItemStatus]:
        # Get modid of item and check if we want to include it
        if limit_modids is not None and item.modid not in limit_modids:
            return None
        return ItemStatus(bp=item.bp, food=item.food.base, affinity=item.affinity.base)

    status = items.translate(convert_node, attrgetter('bp'))

    # Mark all uses
    for food in evals:
        node = status.get(food.bp, fallback=None)
        if node:
            node.data.uses += 1

    # Walk the tree depth-first and mark sub-uses
    for node in status.root.walk_iterator():
        node.data.sub_uses = sum(sub_node.data.uses + sub_node.data.sub_uses for sub_node in node.nodes)

    # TODO: Why isn't ^^^ recursing up as expected?

    return status
