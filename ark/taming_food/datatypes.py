from dataclasses import dataclass, field
from typing import Dict

__all__ = (
    'ItemStatEffect',
    'ItemOverride',
    'Item',
    'ItemStatus',
)


@dataclass(eq=True, unsafe_hash=True)
class ItemStatEffect:
    base: float = field(default=0)
    speed: float = field(default=0)

    def __str__(self):
        speed = f" @ {self.speed}" if self.speed else ''
        return f"{self.base:6.3f}{speed}"


@dataclass
class ItemOverride:
    bp: str
    untamed_priority: float = field(default=0, init=False)
    overrides: Dict[str, float] = field(default_factory=dict, init=False)
    mults: Dict[str, float] = field(default_factory=dict, init=False)


@dataclass(eq=True, unsafe_hash=True)
class Item:
    bp: str
    modid: str
    name: str = field(default='')
    food: ItemStatEffect = field(default_factory=ItemStatEffect, init=False)
    torpor: ItemStatEffect = field(default_factory=ItemStatEffect, init=False)
    affinity: ItemStatEffect = field(default_factory=ItemStatEffect, init=False)


@dataclass
class ItemStatus:
    bp: str
    # uses: int = field(default=0, init=False)
    # sub_uses: int = field(default=0, init=False)
    food: float
    affinity: float
