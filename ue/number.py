import math
import operator
from numbers import Number, Real

__all__ = [
    'make_binary_operators',
    'make_binary_operator',
    'make_operator',
]


def make_binary_operators(op):
    def fwd(a, b):
        assert a.is_serialised
        if isinstance(b, Number):
            return op(a.value, b)
        return NotImplemented

    fwd.__name__ = '__' + op.__name__ + '__'
    fwd.__doc__ = op.__doc__

    def rev(b, a):
        assert b.is_serialised
        if isinstance(a, Number):
            return op(a, b.value)
        return NotImplemented

    rev.__name__ = '__r' + op.__name__ + '__'
    rev.__doc__ = op.__doc__

    return fwd, rev


def make_binary_operator(op):
    def fn(a, b):
        assert a.is_serialised
        if isinstance(b, Number):
            return op(a.value, b)
        return NotImplemented

    fn.__name__ = '__' + op.__name__ + '__'
    fn.__doc__ = op.__doc__

    return fn


def make_operator(op):
    def fn(v, *args, **kwargs):
        assert v.is_serialised
        return op(v.value, *args, **kwargs)

    fn.__name__ = '__' + op.__name__ + '__'
    fn.__doc__ = op.__doc__

    return fn
