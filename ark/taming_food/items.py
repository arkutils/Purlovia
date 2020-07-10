from operator import attrgetter
from typing import Iterable, Optional

from ark.mod import get_core_mods
from ark.types import PrimalItem
from ue.gathering import gather_properties
from ue.hierarchy import find_sub_classes, get_parent_class
from ue.loader import AssetLoader
from ue.properties import StructProperty
from ue.tree import is_fullname_an_asset
from utils.tree import IndexedTree

from .datatypes import Item, ItemStatEffect

__all__ = [
    'gather_items',
    'items',
]

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

    for cls_name in find_sub_classes(PrimalItem.get_ue_type()):
        # Get modid and check if we want to gather it
        modid = loader.get_mod_id(cls_name) or ''
        if modid in get_core_mods():
            modid = ''
        if limit_modids is not None and modid not in limit_modids:
            continue

        # Create item
        item = Item(bp=cls_name, modid=modid)
        parent = get_parent_class(cls_name)
        items.add(parent, item)

        # Only look up stats if this is an asset
        if not is_fullname_an_asset(cls_name):
            continue

        # Collect stat effects, altering the object
        asset = loader[cls_name]
        proxy: PrimalItem = gather_properties(asset)
        item.name = str(proxy.DescriptiveNameBase[0])
        _collect_item_effects(item, proxy)


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
