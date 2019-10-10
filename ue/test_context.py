from typing import Iterable

import pytest

from .context import (DEFAULT_CONTEXT, ParsingContext, get_ctx, ue_parsing_context)


@pytest.fixture(name='ctx')
def fixture_ctx():
    return get_ctx()


def verify_defaults(ctx: ParsingContext, exclude: Iterable[str] = ()):
    excludes = dict.fromkeys(exclude)
    excludes['context_level'] = None
    for fieldname in vars(DEFAULT_CONTEXT):
        if fieldname in excludes:
            continue
        current_value = getattr(ctx, fieldname)
        assert current_value is not None
        assert current_value == getattr(DEFAULT_CONTEXT, fieldname), f"for field '{fieldname}'"


def test_defaults(ctx: ParsingContext):
    verify_defaults(ctx)
    assert ctx.context_level == 1


def test_reset(ctx: ParsingContext):
    with ue_parsing_context(link=not DEFAULT_CONTEXT.link):
        pass

    verify_defaults(ctx)

    with ue_parsing_context(properties=not DEFAULT_CONTEXT.properties):
        pass

    verify_defaults(ctx)


def test_simple_override(ctx: ParsingContext):
    with ue_parsing_context(link=not DEFAULT_CONTEXT.link):
        assert ctx.link == (not DEFAULT_CONTEXT.link)
        verify_defaults(ctx, exclude=['link'])

    with ue_parsing_context(properties=not DEFAULT_CONTEXT.properties):
        assert ctx.properties == (not DEFAULT_CONTEXT.properties)
        verify_defaults(ctx, exclude=['properties'])


def test_multi_level(ctx: ParsingContext):
    assert ctx.context_level == 1
    with ue_parsing_context():
        assert ctx.context_level == 2
        with ue_parsing_context():
            assert ctx.context_level == 3
            with ue_parsing_context():
                assert ctx.context_level == 4
            assert ctx.context_level == 3
        assert ctx.context_level == 2
    assert ctx.context_level == 1


def test_multicontext_level_overrides(ctx: ParsingContext):
    with ue_parsing_context(link=not DEFAULT_CONTEXT.link):
        assert ctx.link == (not DEFAULT_CONTEXT.link)
        verify_defaults(ctx, exclude=['link'])

        with ue_parsing_context(properties=not DEFAULT_CONTEXT.properties):
            assert ctx.link == (not DEFAULT_CONTEXT.link)
            assert ctx.properties == (not DEFAULT_CONTEXT.properties)
            verify_defaults(ctx, exclude=['link', 'properties'])

            with ue_parsing_context(link=DEFAULT_CONTEXT.link, properties=DEFAULT_CONTEXT.properties):
                verify_defaults(ctx)

            assert ctx.link == (not DEFAULT_CONTEXT.link)
            assert ctx.properties == (not DEFAULT_CONTEXT.properties)
            verify_defaults(ctx, exclude=['link', 'properties'])

        assert ctx.link == (not DEFAULT_CONTEXT.link)
        verify_defaults(ctx, exclude=['link'])
