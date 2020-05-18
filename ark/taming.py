'''Parse and cache taming food data for use in extraction phases.'''

from dataclasses import dataclass, field
from typing import Optional, Tuple

from ue.gathering import gather_properties
from ue.hierarchy import find_parent_classes, find_sub_classes
from ue.loader import AssetLoader
from ue.properties import StructProperty
from ue.tree import is_fullname_an_asset
from utils.tree import IndexedTree

from .types import PrimalItem

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

    for clsname in find_sub_classes(PrimalItem.get_ue_type()):
        if clsname.startswith('/Game/Mods/'): continue  # REMOVE ME!!!

        item = Item(bp=clsname)
        parent = _get_parent(clsname)
        items.add(parent, item)

        if not is_fullname_an_asset(clsname): continue

        asset = loader[clsname]
        assert asset.default_export
        proxy: PrimalItem = gather_properties(asset.default_export)
        item.name = str(proxy.DescriptiveNameBase[0])
        _collect_item_effects(item, proxy)


def _get_parent(clsname: str) -> str:
    parent = next(find_parent_classes(clsname, include_self=False))
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
