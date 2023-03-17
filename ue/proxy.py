from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional, Tuple, Type, TypeVar, Union

from utils.generics import get_generic_args

from .base import UEBase
from .hierarchy import find_parent_classes
from .loader import AssetLoader
from .properties import BoolProperty, ByteProperty, DummyAsset, FloatProperty, IntProperty, ObjectProperty, StringProperty

__all__ = [
    'UEProxyStructure',
    'EmptyProxy',
    'uemap',
    'uefloats',
    'uebytes',
    'uebools',
    'ueints',
    'uestrings',
    'get_proxy_for_type',
    'get_proxy_for_exact_type',
    'ProxyComponent',
    'LazyReference',
]

_UETYPE = '__uetype'
_UEFIELDS = '__uefields'
_UEOVERRIDDEN = '__ueoverridden'
_UEOBJECT = '__ueobject'

NO_FALLBACK = object()


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
            if hasattr(default, '__copy__'):
                value = default.__copy__()
            else:
                value = {**default}

            setattr(self, name, value)

        # Initialise the empty set of overridden fields
        setattr(self, _UEOVERRIDDEN, set())
        setattr(self, _UEOBJECT, None)

    def __getitem__(self, name):
        return getattr(self, name)

    def __contains__(self, name):
        return hasattr(self, name)

    def get_all(self):
        return {k: v for k, v in vars(self).items() if not k.startswith('_')}

    def get(self, field_name: str, field_index: int = 0, fallback=NO_FALLBACK) -> Any:
        field_value = getattr(self, field_name, None)
        result = field_value
        if field_value is not None:
            indexed_value = field_value.get(field_index, None)
            result = indexed_value

        if result is None:
            if fallback is NO_FALLBACK:
                raise IndexError(f"{field_name}[{field_index}] not found on {self.__class__.__name__} proxy")
            else:
                return fallback

        return result

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

    def set_source(self, source: Any):
        setattr(self, _UEOBJECT, source)

    def get_source(self) -> Any:
        return getattr(self, _UEOBJECT, None)

    def has_override(self, name: str, index: int = 0):
        '''Returns True if a value has been set (excluding the defaults).'''
        return (name, index) in getattr(self, _UEOVERRIDDEN)


_proxies: Dict[str, Type[UEProxyStructure]] = dict()


def _register_proxy(uetype: str, cls: Type[UEProxyStructure]):
    global _proxies  # pylint: disable=global-statement
    _proxies[uetype] = cls


MISSING = object()

Tval = TypeVar('Tval')
Tele = TypeVar('Tele', bound=UEBase)
Tproxy = TypeVar('Tproxy', bound=UEProxyStructure)


def get_proxy_for_type(cls_name: str, loader: AssetLoader, default=MISSING) -> Tproxy:
    '''
    Step up through the inheritance tree to find the first available proxy type.
    '''
    klass = loader.load_class(cls_name)
    for parent_cls_name in find_parent_classes(klass, include_self=True):
        proxy = get_proxy_for_exact_type(parent_cls_name)
        if proxy:
            return proxy

    if default is MISSING:
        raise TypeError(f"No proxy type available for {cls_name}")

    return default


def get_proxy_for_exact_type(uetype: str):
    global _proxies  # pylint: disable=global-statement
    cls = _proxies.get(uetype, None)
    if cls is None:
        return None
    proxy = cls()
    return proxy


class EmptyProxy(UEProxyStructure, uetype=''):
    __is_empty_proxy = True


class ProxyComponentWrapper(Mapping[int, Tproxy]):
    '''The wrapper that maintains a proxy component's target proxy.'''

    def __init__(self, sub_proxy: Tproxy):
        super().__init__()
        self._proxy = sub_proxy

    def __iter__(self):
        yield 0

    def __len__(self):
        return 1

    def __getitem__(self, index) -> Tproxy:
        '''Retrieve the associated proxy.'''
        if index != 0:
            raise ValueError("Components can only have index 0")

        return self._proxy

    def __setitem__(self, index, value: ObjectProperty):
        '''Update the wrapped proxy with values from the given ObjectProperty.'''
        if index != 0:
            raise ValueError("Components can only have index 0")

        if not isinstance(value, ObjectProperty):
            raise TypeError("Expected ObjectProperty")

        export = value.value.value
        props = export.properties.as_dict()
        self._proxy.update(props)


class ProxyComponent(Mapping[int, Tproxy]):
    _cmp_type: Optional[Type] = None

    def _init_proxy_field(self):
        '''Grab the generic type of this class and store it locally for use later.'''
        if self._cmp_type is not None:
            return

        # Sadly this can't be done in __init__ as the typing variables are not yet set
        args = get_generic_args(self)
        if not args or len(args) != 1 or not issubclass(args[0], UEProxyStructure):
            raise TypeError("This class must be used generically with a single UEProxyStructure type argument")

        self._cmp_type = args[0]

    def __copy__(self) -> ProxyComponentWrapper[Tproxy]:
        self._init_proxy_field()
        assert self._cmp_type
        proxy = self._cmp_type()
        copy = ProxyComponentWrapper[Tproxy](proxy)
        return copy

    def __getitem__(self, index):
        raise RuntimeError("?")

    def __setitem__(self, index, value):
        raise RuntimeError("?")

    def __iter__(self):
        yield 0

    def __len__(self):
        return 1


class LazyReferenceWrapper(Mapping[int, Tproxy]):
    '''The wrapper that evaluates a lazy reference when required.'''

    def __init__(self, sub_proxy: Tproxy):
        super().__init__()
        self._proxy = sub_proxy
        self._target: Optional[ObjectProperty] = None
        self._cache: Optional[Tproxy] = None

    def __iter__(self):
        yield 0

    def __len__(self):
        return 1

    def __getitem__(self, index) -> Tproxy:
        '''Retrieve the associated proxy.'''
        if index != 0:
            raise ValueError("References can only have index 0")

        if not self._target:
            raise ValueError("Lazy reference has no value")

        if not self._cache:
            assert self._target.asset and self._target.asset.loader
            loader: AssetLoader = self._target.asset.loader
            export = loader.load_class(self._target.value.value.fullname)

            # Lazy import to avoid cyclic dependency
            from .gathering import gather_properties  # pylint: disable=import-outside-toplevel
            self._cache = gather_properties(export)

        return self._cache

    def __setitem__(self, index, value: ObjectProperty):
        '''Update the target from the given ObjectProperty.'''
        if index != 0:
            raise ValueError("Components can only have index 0")

        if not isinstance(value, ObjectProperty):
            raise TypeError("Expected ObjectProperty")

        self._target = value


class LazyReference(Mapping[int, Tproxy]):
    _cmp_type: Optional[Type] = None

    def _init_proxy_field(self):
        '''Grab the generic type of this class and store it locally for use later.'''
        if self._cmp_type is not None:
            return

        # Sadly this can't be done in __init__ as the typing variables are not yet set
        args = get_generic_args(self)
        if not args or len(args) != 1 or not issubclass(args[0], UEProxyStructure):
            raise TypeError("This class must be used generically with a single UEProxyStructure type argument")

        self._cmp_type = args[0]

    def __copy__(self) -> LazyReferenceWrapper[Tproxy]:
        self._init_proxy_field()
        assert self._cmp_type
        proxy = self._cmp_type()
        copy = LazyReferenceWrapper[Tproxy](proxy)
        return copy

    def __getitem__(self, index):
        raise RuntimeError("?")

    def __setitem__(self, index, value):
        raise RuntimeError("?")

    def __iter__(self):
        yield 0

    def __len__(self):
        return 1


def uemap(uetype: Type[Tele], args: Iterable[Union[Tval, Tele]], **kwargs) -> Mapping[int, Tele]:
    output: Dict[int, Tele] = dict()

    asset: Optional[UEBase] = DummyAsset()

    for i, v in enumerate(args):
        if v is None:
            continue

        if isinstance(v, UEBase):
            output[i] = v  # type: ignore
        else:
            ele = uetype.create(v, **kwargs, asset=asset)  # type: ignore
            output[i] = ele

            # if not asset:
            #     asset = ele.asset
            #     kwargs['asset'] = asset

    return output


def uefloats(*args: Union[float, str, Tuple[float, str]]) -> Mapping[int, FloatProperty]:
    return uemap(FloatProperty, args)


def uebytes(*args: Union[int, Tuple[str, str]]) -> Mapping[int, ByteProperty]:
    return uemap(ByteProperty, args)


def uebools(*args: bool) -> Mapping[int, BoolProperty]:
    return uemap(BoolProperty, args)


def ueints(*args: int) -> Mapping[int, IntProperty]:
    return uemap(IntProperty, args)


def uestrings(*args: str) -> Mapping[int, StringProperty]:
    return uemap(StringProperty, args)
