# Experimenting with

#%% Setup
import copy
import types
from dataclasses import dataclass
from typing import *

from ue.base import UEBase
from ue.properties import (BoolProperty, ByteProperty, FloatProperty, IntProperty)

# props = gather_properties(export, include_defaults=True)
# props.clean.MaxStatusValues[0]
# props.clean['MaxStatusValues'][0]

# props = gather_properties_raw(export, include_defaults=True)
# props.raw.MaxStatusValues[0]
# props.raw['MaxStatusValues'][0]

#%% Default values
DEFAULTS = {
    '/Script/ShooterGame.PrimalDinoCharacter': {
        'bUseBabyGestation': False,
        'BabyGestationSpeed': FloatProperty.create(0.000035, bytes.fromhex('F7CC1238')),
    },
    '/Script/ShooterGame.PrimalDinoStatusComponent': {
        'MaxStatusValues': (100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0),
        'ExtraTamedHealthMultiplier': (1.35, ),
        'DinoMaxStatAddMultiplierImprinting': (0.2, 0, 0.2, 0, 0.2, 0.2, 0, 0.2, 0.2, 0.2, 0, 0),
        'TheMaxTorporIncreasePerBaseLevel': (0.06, ),
    },
}

#%% Types
Tval = TypeVar('Tval')
Tele = TypeVar('Tele', bound=UEBase)


def uemap(uetype: Type[Tele], args: Iterable[Union[Tval, Tele]]) -> Mapping[int, Tele]:
    output: Dict[int, Tele] = dict()

    for i, v in enumerate(args):
        if v is None:
            continue

        if isinstance(v, UEBase):
            output[i] = v  # type: ignore
        else:
            ele = uetype.create(v)  # type: ignore
            output[i] = ele

    return output


def uefloats(*args: Union[float, str]) -> Mapping[int, FloatProperty]:
    values = [FloatProperty.create(data=bytes.fromhex(v)) if isinstance(v, str) else v for v in args]
    return uemap(FloatProperty, values)


def ueints(*args: Union[float, str]) -> Mapping[int, IntProperty]:
    values = [IntProperty.create(v) for v in args]
    return uemap(IntProperty, values)


def uebytes(*args: Union[float, str]) -> Mapping[int, ByteProperty]:
    values = [ByteProperty.create(v) for v in args]
    return uemap(ByteProperty, values)


def uebools(*args: Union[float, str]) -> Mapping[int, BoolProperty]:
    values = [BoolProperty.create(v) for v in args]
    return uemap(BoolProperty, values)


#%% Structure
class UEProxyStructure:
    __uetype: str
    __uefields: Tuple[str, Tuple[UEBase, ...]]

    def get_ue_type(self):
        return self.__uetype

    # def __init_subclass__(cls, uetype: str):
    #     if not uetype:
    #         raise ValueError("uetype must be specified for this proxy class")

    #     cls.__uetype = uetype

    def update(self, values: Mapping[str, Mapping[int, UEBase]]):
        target_dict = vars(self)
        for name, field_values in values.items():
            if name not in target_dict:
                target_dict[name] = dict()
            target_field = target_dict[name]
            for i, value in field_values.items():
                target_field[i] = value


#%% Proxy attr
_UETYPE = '__uetype'
_UEFIELDS = '__uefields'

MISSING = object()


def _proxify_class(cls: Type, ue_type: str):
    if cls.__bases__ != (UEProxyStructure, ):
        raise ValueError("UE proxy classes must inherit from UEProxyStructure")

    if '__init__' in cls.__dict__:
        raise ValueError("UE proxy class cannot define __init__")

    if cls.__dict__.get('__annotations__', {}):
        raise ValueError("UE proxy classes should not have type annotations")

    setattr(cls, _UETYPE, ue_type)

    fields = dict()

    for name, default in cls.__dict__.items():
        if name.startswith('_'):
            continue
        fields[name] = default

    for name in fields:
        delattr(cls, name)

    setattr(cls, _UEFIELDS, fields)

    def init(self):
        # self.__bases__ = self.__bases__
        fields = getattr(self, _UEFIELDS)
        for name, default in fields.items():
            value = {**default}
            setattr(self, name, value)

    setattr(cls, '__init__', init)

    print(cls.__bases__)

    return cls


def ueproxy(ue_type: str):
    if not isinstance(ue_type, str):
        raise TypeError("Incorrect usage of @ueproxy('<uetype>'")

    def wrap(cls):
        return _proxify_class(cls, ue_type)

    return wrap


#%% Proxy class
@ueproxy('/Script/ShooterGame.PrimalDinoStatusComponent')
class DCSC(UEProxyStructure):
    MaxStatusValues = uefloats(100.0, 100.0, 0.0, 100.0, 0, 'E0000000')
    CanLevelUp = uebools(True, False, True, False)


#%% Tests
dcsc1 = DCSC()
dcsc2 = DCSC()

#%% Show 1
dcsc1.MaxStatusValues

#%% Show 2
dcsc2.MaxStatusValues

#%% Show
dcsc1.MaxStatusValues[0] = 'one'
dcsc2.MaxStatusValues[0] = 'two'
#%% Update
dcsc1.update({'MaxStatusValues': {0: FloatProperty.create(200)}})

#%%
