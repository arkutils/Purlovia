import math
from dataclasses import dataclass, field
from typing import Any, List, Optional

from ark.types import PrimalDinoCharacter
from ue.loader import AssetLoader

__all__ = [
    'gather_immobilization_data',
]


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
    global immobilization_itemdata  # pylint: disable=global-statement
    if immobilization_itemdata:
        return immobilization_itemdata

    # TODO: Implement search for buffs and structures that can immobilize
    # bImmobilizeTarget for buffs (including bolas, etc)
    raise NotImplementedError


def gather_immobilization_data(char_props: PrimalDinoCharacter, loader: AssetLoader) -> List[str]:
    # Tag is used to identify immobilization targets and compatible saddles
    # tag = char_props.CustomTag[0] or f'<unknown tag for {asset.default_class.name}'

    # Drag weight is used for immobilization calculation and arena entry
    # dragWeight = char_props.DragWeight[0]

    items = ensure_immobilization_itemdata(loader)
    immobilizedBy: List[Any] = []
    if char_props.bPreventImmobilization[0]:
        return immobilizedBy
    if char_props.bIsWaterDino[0]:
        return immobilizedBy
    weight = char_props.DragWeight[0]
    mass = char_props.CharacterMovement[0].Mass[0].rounded_value  # type: ignore
    is_boss = char_props.bIsBossDino[0]
    tag = char_props.CustomTag[0]
    ignore_traps = char_props.bIgnoreAllImmobilizationTraps[0]
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
