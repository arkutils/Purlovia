from typing import NoReturn

__all__ = [
    'throw',
]


def throw(ex: Exception) -> NoReturn:
    raise ex
