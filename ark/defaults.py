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
    AmountMaxGainedPerLevelUpValue = uefloats(0, 0, 0.06, 0, 0, 0, 0, 0, 0, 0, 0, 0)  # TODO: Should 0.06 be here? needs raw data
    AmountMaxGainedPerLevelUpValueTamed = uefloats(*(0, ) * 12)
    BaseFoodConsumptionRate = uefloats(-0.025000)  # TODO: needs raw data
    CanLevelUpValue = uebytes(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    DontUseValue = uebytes(0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 1, 1)
    ExtraTamedHealthMultiplier = uefloats((1.35, 'CDCCAC3F'), 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
    MaxStatusValues = uefloats(100, 100, 100, 100, 100, 100, 0, 0, 0, 0, 0, 0)
    ProneWaterFoodConsumptionMultiplier = uefloats(1.0)
    RecoveryRateStatusValue = uefloats(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)  # TODO: Need numbers - only one known is 0 for torpor
    TamingMaxStatAdditions = uefloats(*(0, ) * 12)
    TamingMaxStatMultipliers = uefloats(*(0, ) * 12)


class DinoChar(UEProxyStructure, uetype='/Script/ShooterGame.PrimalDinoCharacter'):
    BabyAgeSpeed = uefloats((0.033, '022B073D'))
    BabyGestationSpeed = uefloats((0.000035, 'F7CC1238'))
    bCanBeTamed = uebools(True)
    bCanBeTorpid = uebools(True)
    bIgnoreAllImmobilizationTraps = uebools(False)
    bIsBossDino = uebools(False)
    bIsCorrupted = uebools(False)
    bIsWaterDino = uebools(False)
    bPreventImmobilization = uebools(False)
    bPreventSleepingTame = uebools(False)
    bSupportWakingTame = uebools(False)
    bUseBabyGestation = uebools(False)
    CustomTag = uestrings('')
    DescriptiveName = uestrings('')
    DragWeight = uefloats(35.0)
    ExtraBabyAgeSpeedMultiplier = uefloats(1.0)
    ExtraBabyGestationSpeedMultiplier = uefloats(1.0)
    KnockedOutTorpidityRecoveryRateMultiplier = uefloats(3.0)
    Mass = uefloats(100.0)
    NewFemaleMaxTimeBetweenMating = uefloats(172800.0)
    NewFemaleMinTimeBetweenMating = uefloats(64800.0)
    PreventColorizationRegions = uebytes(0, 0, 0, 0, 0, 0)
    RequiredTameAffinity = uefloats(100)
    RequiredTameAffinityPerBaseLevel = uefloats(5.0)
    TameIneffectivenessByAffinity = uefloats(20)
    TheMaxTorporIncreasePerBaseLevel = uefloats(0.06)  # TODO: needs raw data
    WakingTameFoodAffinityMultiplier = uefloats(1.6)  # TODO: needs raw data
    WakingTameFoodConsumptionRateMultiplier = uefloats(2.0)

    # TODO: Other types, not yet supported
    # RandomColorSetsMale
    # RandomColorSetsFemale
    # FertilizedEggItemsToSpawn
    # BoneDamageAdjusters


# PGD
#   ColorDefinitions
#   MasterDyeList

# Egg
#   EggLoseDurabilityPerSecond
#   ExtraEggLoseDurabilityPerSecondMultiplier
#   EggMinTemperature
#   EggMaxTemperature
