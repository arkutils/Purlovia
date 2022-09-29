import sys
from enum import IntEnum
from typing import Callable, Iterable, Protocol

__all__ = [
    "display",
    "display_table",
]


class SupportsDunderStr(Protocol):

    def __str__(self) -> str:
        ...


display_table: Callable[[Iterable[Iterable[str | float | int | SupportsDunderStr]], Iterable[str]], None]


class RuntimeEnvironment(IntEnum):
    Notebook = 1,
    IPython = 2,
    Plain = 3,


env = RuntimeEnvironment.Plain
if 'ipykernel' in sys.modules:
    env = RuntimeEnvironment.Notebook
elif 'IPython' in sys.modules:
    env = RuntimeEnvironment.IPython

if env == RuntimeEnvironment.Notebook:
    from IPython.display import display

    from .notebook import display_table, init_tables  # type: ignore
    init_tables()

else:
    from .plain import display_table, init_tables  # type: ignore
    init_tables()
    display = print
