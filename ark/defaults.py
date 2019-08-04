from ue.proxy import *

FEMALE_MINTIMEBETWEENMATING_DEFAULT = 64800.0
FEMALE_MAXTIMEBETWEENMATING_DEFAULT = 172800.0

BABYGESTATIONSPEED_DEFAULT = 0.000035

BASE_VALUES = (100, 100, 100, 100, 100, 100, 0, 0, 0, 0, 0, 0)
IW_VALUES = (0, 0, 0.06, 0, 0, 0, 0, 0, 0, 0, 0, 0)
IMPRINT_VALUES = (0.2, 0, 0.2, 0, 0.2, 0.2, 0, 0.2, 0.2, 0.2, 0, 0)
EXTRA_MULTS_VALUES = (1.35, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
DONTUSESTAT_VALUES = (0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1)
CANLEVELUP_VALUES = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

# Stats that are represented as percentages instead
IS_PERCENT_STAT = (0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1)


class DCSC(UEProxyStructure, uetype='/Script/ShooterGame.PrimalDinoStatusComponent'):
    MaxStatusValues = uefloats(100.0, 100.0, 0.0, 100.0, 0, '00000000')
    CanLevelUp = uebools(True, False, True, False)


class DinoChar(UEProxyStructure, uetype='/Script/ShooterGame.PrimalDinoCharacter'):
    # DescriptiveName = uestrings('') # need uestrings!
    Something = uefloats(0.0, 0.0)
