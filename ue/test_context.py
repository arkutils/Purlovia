import pytest

from .context import ParseDepth, ParseMeta, get_ctx, parsing_context


@pytest.fixture(name='ctx')
def fixture_ctx():
    return get_ctx()


def test_defaults(ctx):
    assert ctx.depth == ParseDepth.DEFAULT
    assert ctx.meta == ParseMeta.DEFAULT


def test_reset(ctx):
    assert ParseDepth.HEADER != ParseDepth.DEFAULT
    assert ParseMeta.FULL != ParseMeta.DEFAULT

    with parsing_context(depth=ParseDepth.HEADER):
        pass

    assert ctx.depth == ParseDepth.DEFAULT
    assert ctx.meta == ParseMeta.DEFAULT

    with parsing_context(meta=ParseMeta.FULL):
        pass

    assert ctx.depth == ParseDepth.DEFAULT
    assert ctx.meta == ParseMeta.DEFAULT


def test_simple_override(ctx):
    with parsing_context(depth=ParseDepth.HEADER):
        assert ctx.depth == ParseDepth.HEADER
        assert ctx.meta == ParseMeta.DEFAULT

    with parsing_context(meta=ParseMeta.FULL):
        assert ctx.depth == ParseDepth.DEFAULT
        assert ctx.meta == ParseMeta.FULL


def test_multi_level(ctx):
    assert ParseDepth.MEMORY != ParseDepth.DEFAULT
    assert ParseDepth.HEADER != ParseDepth.DEFAULT
    assert ParseMeta.FULL != ParseMeta.DEFAULT

    with parsing_context(depth=ParseDepth.HEADER):
        assert ctx.depth == ParseDepth.HEADER
        assert ctx.meta == ParseMeta.DEFAULT

        with parsing_context(depth=ParseDepth.MEMORY):
            assert ctx.depth == ParseDepth.MEMORY
            assert ctx.meta == ParseMeta.DEFAULT

            with parsing_context(meta=ParseMeta.FULL):
                assert ctx.depth == ParseDepth.MEMORY
                assert ctx.meta == ParseMeta.FULL

            assert ctx.depth == ParseDepth.MEMORY
            assert ctx.meta == ParseMeta.DEFAULT

        assert ctx.depth == ParseDepth.HEADER
        assert ctx.meta == ParseMeta.DEFAULT

    assert ctx.depth == ParseDepth.DEFAULT
    assert ctx.meta == ParseMeta.DEFAULT
