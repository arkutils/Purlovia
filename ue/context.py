import threading
from collections import namedtuple
from contextlib import ContextDecorator
from enum import IntEnum, auto
from logging import NullHandler, getLogger
from typing import Optional, cast

from utils.xlocal import xlocal

__all__ = [
    'ParseDepth',
    'ParseMeta',
    'parsing_context',
    'get_ctx',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class ParseDepth(IntEnum):
    MEMORY = auto()
    HEADER = auto()
    PROPERTIES = auto()
    # BULKDATA = auto()

    DEFAULT = PROPERTIES
    FULL = PROPERTIES


class ParseMeta(IntEnum):
    NONE = auto()
    FULL = auto()

    DEFAULT = NONE


current_ctx = xlocal(depth=ParseDepth.DEFAULT, meta=ParseMeta.DEFAULT)


class Context:
    depth: ParseDepth
    meta: ParseMeta


def get_ctx() -> Context:
    return cast(Context, current_ctx)


def parsing_context(depth: Optional[ParseDepth] = None, meta: Optional[ParseMeta] = None):
    '''
    Change the current UE parsing context.
    This is a context manager for use in a `with` statement.

    Usage:
        with parsing_context(ParseDepth.PROPERTIES, ParseMeta.NONE):
            asset = loader[assetname]
    '''
    # Only override what is changed
    if depth is None and meta is None:
        return current_ctx()
    if depth is None:
        return current_ctx(meta=meta)

    return current_ctx(depth=depth)
