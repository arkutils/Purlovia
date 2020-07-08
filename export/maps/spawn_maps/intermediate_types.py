from dataclasses import dataclass


@dataclass
class SpawnFrequency:
    __slots__ = ('path', 'frequency')
    path: str
    frequency: float


@dataclass
class SpawnRectangle:
    __slots__ = ('x', 'y', 'w', 'h', 'cave', 'untameable')
    x: float
    y: float
    w: float
    h: float
    cave: bool
    untameable: bool


@dataclass
class SpawnPoint:
    __slots__ = ('x', 'y', 'cave', 'untameable')
    x: float
    y: float
    cave: bool
    untameable: bool
