'''
with ue_parsing_context(metadata=True, link=True, properties=True):
    # GUI stuff

with ue_parsing_context(metadata=False, link=True, properties=False):
    # hierarchy gathering

    with ue_parsing_context(properties=True):
        # exporting
        # inherits metadata=False, link=True
'''

from dataclasses import dataclass
from typing import Optional, cast

from utils.log import get_logger
from utils.xlocal import xlocal

__all__ = [
    'ParsingContext',
    'ue_parsing_context',
    'get_ctx',
]

logger = get_logger(__name__)

INCLUDE_METADATA = True


def disable_metadata():
    global INCLUDE_METADATA  # pylint: disable=global-statement
    INCLUDE_METADATA = False


@dataclass
class ParsingContext:
    # metadata: bool
    link: bool
    properties: bool
    extended_properties: bool
    bulk_data: bool
    context_level: int


DEFAULT_CONTEXT = ParsingContext(
    # metadata=True,
    link=True,
    properties=True,
    extended_properties=False,
    bulk_data=False,
    context_level=1,
)

__current_ctx = xlocal(**vars(DEFAULT_CONTEXT))


def get_ctx() -> ParsingContext:
    return cast(ParsingContext, __current_ctx)


def ue_parsing_context(
        *,
        #    metadata: Optional[bool] = None,
        link: Optional[bool] = None,
        properties: Optional[bool] = None,
        extended_properties: Optional[bool] = None,
        bulk_data: Optional[bool] = None):
    '''
    Change the current UE parsing context.
    This is a context manager for use in a `with` statement.

    Usage:
        with ue_parsing_context(metadata=False, properties=False):
            asset = loader[assetname]
    '''
    fields = dict(context_level=__current_ctx.context_level + 1)

    # if metadata is not None: fields['metadata'] = metadata
    if link is not None:
        fields['link'] = link
    if properties is not None:
        fields['properties'] = properties
    if extended_properties is not None:
        fields['extended_properties'] = extended_properties
    if bulk_data is not None:
        fields['bulk_data'] = bulk_data

    ctx = __current_ctx(**fields)
    return ctx
