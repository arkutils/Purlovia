from typing import *

from .base import UEBase
from .properties import (
    BoolProperty, ByteProperty, DummyAsset, FloatProperty, IntProperty,
    StringProperty)

__all__ = [
    'UEProxyStructure',
    'EmptyProxy',
    'uemap',
    'uefloats',
    'uebytes',
    'uebools',
    'ueints',
    'uestrings',
    'proxy_for_type',
]

_UETYPE = '__uetype'
_UEFIELDS = '__uefields'
_UEOVERRIDDEN = '__ueoverridden'


class UEProxyStructure:
    '''Baseclass for UE proxy structures.

    These classes provide typed property names and default values to match values found
    in-game binaries, outside of the normal asset system.'''

    __proxy_classes: Dict[str, Type['UEProxyStructure']] = dict()

    @classmethod
    def get_ue_type(cls):
        return getattr(cls, _UETYPE)

    @classmethod
    def get_defaults(cls):
        return getattr(cls, _UEFIELDS)

    def __init_subclass__(cls, uetype: str):
        if not uetype and not getattr(cls, '_EmptyProxy__is_empty_proxy', None):
            raise ValueError("uetype must be specified for this proxy class")

        if len(cls.__bases__) > 1:
            raise TypeError('UEProxyStructure subclasses cannot inherit from more than one class')

        # Register this cls as available for proxy creation
        setattr(cls, _UETYPE, uetype)
        _register_proxy(uetype, cls)

        # Record the defaults into _UEFIELDS
        fields = dict()
        base = cls
        while True:
            base = base.__base__
            if base is object or base is UEProxyStructure:
                break

            for name, default in getattr(base, _UEFIELDS).items():
                if name.startswith('_'):
                    continue
                fields[name] = default

        for name, default in cls.__dict__.items():
            if name.startswith('_'):
                continue
            fields[name] = default

        for name in fields:
            if hasattr(cls, name):
                delattr(cls, name)

        setattr(cls, _UEFIELDS, fields)

    def __init__(self):
        # Initialise the proxy with a *copy* of the defaults from _UEFIELDS
        fields = getattr(self, _UEFIELDS)
        for name, default in fields.items():
            value = {**default}
            setattr(self, name, value)

        # Initialise the empty set of overridden fields
        setattr(self, _UEOVERRIDDEN, set())

    def __getitem__(self, name):
        return getattr(self, name)

    def update(self, values: Mapping[str, Mapping[int, UEBase]]):
        overrides = getattr(self, _UEOVERRIDDEN)
        target_dict = vars(self)
        for name, field_values in values.items():
            if name not in target_dict:
                target_dict[name] = dict()
            target_field = target_dict[name]
            for i, value in field_values.items():
                target_field[i] = value
                overrides.add((name, i))

    def has_override(self, name: str, index: int = 0):
        '''Returns True if a value has bee set (excluding the defaults).'''
        return (name, index) in getattr(self, _UEOVERRIDDEN)


_proxies: Dict[str, Type[UEProxyStructure]] = dict()


def _register_proxy(uetype: str, cls: Type[UEProxyStructure]):
    global _proxies  # pylint: disable=global-statement
    _proxies[uetype] = cls


def proxy_for_type(uetype: str):
    global _proxies  # pylint: disable=global-statement
    cls = _proxies.get(uetype, None)
    if cls is None:
        return None
    proxy = cls()
    return proxy


class EmptyProxy(UEProxyStructure, uetype=None):
    __is_empty_proxy = True


Tval = TypeVar('Tval')
Tele = TypeVar('Tele', bound=UEBase)


def uemap(uetype: Type[Tele], args: Iterable[Union[Tval, Tele]], **kwargs) -> Mapping[int, Tele]:
    output: Dict[int, Tele] = dict()

    asset: Optional[UEBase] = DummyAsset()

    for i, v in enumerate(args):
        if v is None:
            continue

        if isinstance(v, UEBase):
            output[i] = v  # type: ignore
        else:
            ele = uetype.create(v, **kwargs)  # type: ignore
            ele.asset = asset
            output[i] = ele

            if not asset:
                asset = ele.asset
                kwargs['asset'] = asset

    return output


def uefloats(*args: Union[float, str, Tuple[float, str]]) -> Mapping[int, FloatProperty]:
    return uemap(FloatProperty, args)


def uebytes(*args: int) -> Mapping[int, ByteProperty]:
    return uemap(ByteProperty, args, size=1)


def uebools(*args: bool) -> Mapping[int, BoolProperty]:
    return uemap(BoolProperty, args)


def ueints(*args: int) -> Mapping[int, IntProperty]:
    return uemap(IntProperty, args)


def uestrings(*args: str) -> Mapping[int, StringProperty]:
    return uemap(StringProperty, args)
