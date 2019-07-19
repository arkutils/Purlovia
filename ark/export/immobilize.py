import math
from typing import *
from dataclasses import dataclass, field
from ue.loader import AssetLoader
from ark.properties import stat_value, PriorityPropDict


@dataclass
class ImmobilizingItem:
    name: str
    is_trap: bool = False
    minWeight: Optional[float] = 0
    maxWeight: Optional[float] = math.inf
    minMass: Optional[float] = 0
    maxMass: Optional[float] = math.inf
    ignoreTags: List[str] = field(default_factory=list)
    ignoreBosses: bool = False


immobilization_itemdata: List[ImmobilizingItem] = [
    ImmobilizingItem(name="Bola", maxWeight=150),
    ImmobilizingItem(name="Chain Bola", minWeight=148, maxWeight=900, ignoreBosses=True),
    ImmobilizingItem(name="Bear Trap", is_trap=True, maxMass=201, ignoreTags=['Mek', 'MegaMek'], ignoreBosses=True),
    ImmobilizingItem(name="Large Bear Trap", is_trap=True, minMass=150, ignoreBosses=True),
    ImmobilizingItem(name="Plant Species Y", is_trap=True, maxMass=300, ignoreBosses=True),
]


def ensure_immobilization_itemdata(loader: AssetLoader) -> List[ImmobilizingItem]:
    global immobilization_itemdata  #pylint: disable=global-statement
    if immobilization_itemdata:
        return immobilization_itemdata

    # TODO: Implement search for buffs and structures that can immobilize
    # bImmobilizeTarget for buffs (including bolas, etc)
    raise NotImplementedError


def gather_immobilization_data(props: PriorityPropDict, loader: AssetLoader) -> List[str]:
    items = ensure_immobilization_itemdata(loader)
    immobilizedBy: List[Any] = []
    if stat_value(props, 'bPreventImmobilization', 0, False):
        return immobilizedBy
    if stat_value(props, 'bIsWaterDino', 0, False):
        return immobilizedBy
    weight = stat_value(props, 'DragWeight', 0, 35)
    mass = stat_value(props, 'Mass', 0, 100.0)
    is_boss = stat_value(props, 'bIsBossDino', 0, False)
    tag = stat_value(props, 'CustomTag', 0, None)
    ignore_traps = stat_value(props, 'bIgnoreAllImmobilizationTraps', 0, False)
    for item in items:
        if item.is_trap and ignore_traps:
            continue
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
