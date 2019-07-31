# Blah

#%% Setup
from dataclasses import dataclass
from typing import *

from ue.properties import FloatProperty

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


#% Structure
class UEData:
    pass


@dataclass(init=False)
class DinoCharacterStatusComponent(UEData):
    MaxStatusValues: Mapping[int, FloatProperty]


T = TypeVar('T', bound=UEData)


#%% Handler
def prep_defaults(cls: Type[T]) -> T:
    obj = cls()
    d = vars(obj)
    print(d)
    for k in cls.__annotations__.keys():
        d[k] = dict()
    return obj


# dcsc = DinoCharacterStatusComponent()
dcsc = prep_defaults(DinoCharacterStatusComponent)
# dcsc.MaxStatusValues = {0: FloatProperty.create(100.0)}

print(dcsc.MaxStatusValues)
dcsc.MaxStatusValues[0] = 100.0
print(dcsc.MaxStatusValues[0] + 1)

#%%
