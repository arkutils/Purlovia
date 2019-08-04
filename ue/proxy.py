from typing import *

from .base import UEBase
from .properties import (BoolProperty, ByteProperty, FloatProperty, IntProperty, StringProperty)

__all__ = [
    'UEProxyStructure',
    'uefloats',
    'uebytes',
    'uebools',
    'ueints',
    'uestrings',
    'proxy_for_type',
]

_UETYPE = '__uetype'
_UEFIELDS = '__uefields'


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
        if not uetype:
            raise ValueError("uetype must be specified for this proxy class")

        setattr(cls, _UETYPE, uetype)
        _register_proxy(uetype, cls)

        fields = dict()

        for name, default in cls.__dict__.items():
            if name.startswith('_'):
                continue
            fields[name] = default

        for name in fields:
            delattr(cls, name)

        setattr(cls, _UEFIELDS, fields)

    def __init__(self):
        fields = getattr(self, _UEFIELDS)
        for name, default in fields.items():
            value = {**default}
            setattr(self, name, value)

    def update(self, values: Mapping[str, Mapping[int, UEBase]]):
        target_dict = vars(self)
        for name, field_values in values.items():
            if name not in target_dict:
                target_dict[name] = dict()
            target_field = target_dict[name]
            for i, value in field_values.items():
                target_field[i] = value


_proxies: Dict[str, Type[UEProxyStructure]] = dict()


def _register_proxy(uetype: str, cls: Type[UEProxyStructure]):
    global _proxies  # pylint: disable=global-statement
    _proxies[uetype] = cls


def proxy_for_type(uetype: str):
    cls = _proxies.get(uetype, None)
    if cls is None:
        return None
    proxy = cls()
    return proxy


Tval = TypeVar('Tval')
Tele = TypeVar('Tele', bound=UEBase)


def uemap(uetype: Type[Tele], args: Iterable[Union[Tval, Tele]], **kwargs) -> Mapping[int, Tele]:
    output: Dict[int, Tele] = dict()

    asset: Optional[UEBase] = None

    for i, v in enumerate(args):
        if v is None:
            continue

        if isinstance(v, UEBase):
            output[i] = v  # type: ignore
        else:
            ele = uetype.create(v, **kwargs)  # type: ignore
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
