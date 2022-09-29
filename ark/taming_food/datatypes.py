'''Data types for the food system.'''

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from ark.stats import Stat

__all__ = (
    'SpeciesItemOverride',
    'SpeciesFoods',
    'ItemStatEffect',
    'Item',
    # 'ItemStatus',
)


@dataclass
class SpeciesItemOverride:
    '''Specifies overrides for the effect of an item. Species have many of these.'''
    bp: str
    untamed_priority: float = field(default=0, init=False)
    affinity_override: float = field(default=0, init=False)
    affinity_mult: float = field(default=1, init=False)
    mults: Dict[Stat, float] = field(default_factory=dict, init=False)


@dataclass
class SpeciesFoods:
    '''A container for the foods that a species can eat.'''
    bp: str
    adult_eats: list[SpeciesItemOverride] = field(default_factory=list, init=False)
    '''
    Foods eaten as an adult.
    '''
    child_eats: list[SpeciesItemOverride] | None = field(default=None, init=False)
    '''
    Foods eaten while growing up. None means the adult list should be used.
    '''


@dataclass(eq=True, unsafe_hash=True)
class ItemStatEffect:
    '''How much and how fast of an effect to apply.'''
    base: float = field(default=0)
    speed: float = field(default=0)

    def __str__(self):
        speed = f" @ {self.speed}" if self.speed else ''
        return f"{self.base:.3f}{speed}"

    def __lt__(self, other: ItemStatEffect):
        return self.base < other.base


@dataclass()
class Item:
    '''An item and its effects, on use and as a custom recipe ingredient.'''
    bp: str
    modid: str
    name: str = field(default='')
    affinity_mult: float = field(default=1.0, init=False)
    untamed_priority: float = field(default=0, init=False)
    use_item_stats: Dict[Stat, ItemStatEffect] = field(default_factory=dict, init=False)
    ingredient_stats: Dict[Stat, ItemStatEffect] = field(default_factory=dict, init=False)
    preventDinoUse: bool = field(default=False, init=False)
    preventDinoAutoUse: bool = field(default=False, init=False)


@dataclass()
class ItemUseResult:
    '''The effect of using an item.'''
    bp: str
    affinity: float = field(default=0.0, init=False)
    affinity_mult: float = field(default=1.0, init=False)
    untamed_priority: float = field(default=0, init=False)
    use_item_stats: Dict[Stat, ItemStatEffect] = field(default_factory=dict, init=False)

    def get_affinity_total(self) -> float:
        return self.affinity * self.affinity_mult
