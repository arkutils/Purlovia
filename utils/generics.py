from typing import List, Optional, Tuple, Type


def get_generic_args(obj) -> Optional[List[Type]]:
    orig_class = getattr(obj, '__orig_class__', None)
    args: Optional[Tuple[Type]] = None
    if orig_class:
        args = getattr(orig_class, '__args__', None)
    return args  # type: ignore
