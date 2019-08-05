from itertools import repeat

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

STAT_COUNT = 12


class PrimalDinoStatusComponent(UEProxyStructure, uetype='/Script/ShooterGame.PrimalDinoStatusComponent'):
    # DevKit Verified
    AmountMaxGainedPerLevelUpValue = uefloats(*repeat(0, STAT_COUNT))
    AmountMaxGainedPerLevelUpValueTamed = uefloats(*repeat(0, STAT_COUNT))
    BaseFoodConsumptionRate = uefloats(-0.025000)  # TODO: needs raw data
    bCanSuffocate = uebools(True)
    bCanSuffocateIfTamed = uebools(False)
    bForceGainOxygen = uebools(False)
    CanLevelUpValue = uefloats(*repeat(0, STAT_COUNT))
    DinoMaxStatAddMultiplierImprinting = uefloats(0.2, 0, 0.2, 0, 0.2, 0.2, 0, 0.2, 0.2, 0.2, 0, 0)
    DontUseValue = uefloats(*repeat(0, STAT_COUNT))
    ExtraTamedHealthMultiplier = uefloats(1.35)  # TODO: needs raw data
    KnockedOutTorpidityRecoveryRateMultiplier = uefloats(3.0)
    MaxStatusValues = uefloats(100, 100, 100, 100, 100, 100, 0, 0, 0, 0, 0, 0)
    ProneWaterFoodConsumptionMultiplier = uefloats(1.0)
    RecoveryRateStatusValue = uefloats(100.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    TamedBaseHealthMultiplier = uefloats(1.0)
    TamingMaxStatAdditions = uefloats(*repeat(0, STAT_COUNT))
    TamingMaxStatMultipliers = uefloats(*repeat(0, STAT_COUNT))
    TheMaxTorporIncreasePerBaseLevel = uefloats(0.06)  # TODO: needs raw data
    WakingTameFoodConsumptionRateMultiplier = uefloats(2.0)

    # DevKit Unverified


DCSC = PrimalDinoStatusComponent


class PrimalDinoCharacter(UEProxyStructure, uetype='/Script/ShooterGame.PrimalDinoCharacter'):
    # DevKit Verified
    BabyAgeSpeed = uefloats(0.033)  # TODO: needs raw data
    BabyGestationSpeed = uefloats(0.000035)  # TODO: needs raw data
    bCanBeTamed = uebools(True)
    bCanBeTorpid = uebools(True)
    bCanHaveBaby = uebools(False)
    bIgnoreAllImmobilizationTraps = uebools(False)
    bIsBossDino = uebools(False)
    bIsCorrupted = uebools(False)
    bIsWaterDino = uebools(False)
    bPreventImmobilization = uebools(False)
    bPreventSleepingTame = uebools(False)
    bSupportWakingTame = uebools(False)
    bUseBabyGestation = uebools(False)
    bUseColorization = uebools(False)
    CustomTag = uestrings('')  # NameProperty (Default: None)
    DescriptiveName = uestrings('')  # StringProperty (Default: 'PrimalCharacter')
    DinoNameTag = uestrings('')  # NameProperty (Default: None)
    DragWeight = uefloats(35.0)
    ExtraBabyAgeSpeedMultiplier = uefloats(1.0)
    ExtraBabyGestationSpeedMultiplier = uefloats(1.0)
    ExtraTamedBaseHealthMultiplier = uefloats(1.0)
    NewFemaleMaxTimeBetweenMating = uefloats(172800.0)
    NewFemaleMinTimeBetweenMating = uefloats(64800.0)
    PreventColorizationRegions = uebytes(0, 0, 0, 0, 0, 0)
    RequiredTameAffinity = uefloats(100)
    RequiredTameAffinityPerBaseLevel = uefloats(5.0)
    TameIneffectivenessByAffinity = uefloats(20)
    WakingTameFoodAffinityMultiplier = uefloats(1.6)  # TODO: needs raw data
    WakingTameFoodIncreaseMultiplier = uefloats(1.0)

    # TODO: Other types, not yet supported
    # RandomColorSetsMale (ObjectProperty) = 'None'
    # RandomColorSetsFemale (ObjectProperty) = 'None'
    # FertilizedEggItemsToSpawn (ArrayProperty) = []
    # BoneDamageAdjusters (ArrayProperty) = []

    # DevKit Unverified


class ShooterCharacterMovement(UEProxyStructure, uetype='/Script/ShooterGame.ShooterCharacterMovement'):
    # DevKit Verified
    Mass = uefloats(100.0)

    # DevKit Unverified


class PrimalGameData(UEProxyStructure, uetype='/Script/ShooterGame.PrimalGameData'):
    # DevKit Verified
    ModDescription = uestrings('')
    ModName = uestrings('')
    #   ColorDefinitions (ArrayProperty) = []
    #   MasterDyeList (ArrayProperty) = []

    # DevKit Unverified


class PrimalItem(UEProxyStructure, uetype='/Script/ShooterGame.PrimalItem'):
    # DevKit Verified
    bSupportDragOntoOtherItem = uebools(False)
    DescriptiveNameBase = uestrings('')
    EggLoseDurabilityPerSecond = uefloats(1.0)
    EggMaxTemperature = uefloats(30.0)
    EggMinTemperature = uefloats(15.0)
    ExtraEggLoseDurabilityPerSecondMultiplier = uefloats(1.0)
    ItemDescription = uestrings('')
    # BaseCraftingResourceRequirements (ArrayProperty) = []
    # UseItemAddCharacterStatusValues (ArrayProperty) = []

    # DevKit Unverified


class PrimalItem_Dye(PrimalItem, uetype='/Script/ShooterGame.PrimalItem_Dye'):
    bSupportDragOntoOtherItem = uebools(True)
    # DevKit Verified
    # DyeColor (LinearColor) = (0.0, 0.0, 0.0, 0.0)
    # DyeUISceneTemplate (ObjectProperty) = None

    # DevKit Unverified


class PrimalDinoSettings(UEProxyStructure, uetype='/Script/ShooterGame.PrimalDinoSettings'):
    # DevKit Verified
    TamingAffinityNoFoodDecreasePercentageSpeed = uefloats(0.0075)  # TODO: needs raw data
    WakingTameDisplayItemName = uebools(False)
    # BaseDamageTypeAdjusters (ArrayProperty) = []
    # DinoFoodTypeImage (ObjectProperty only Textures) = None
    # DinoFoodTypeName (StringProperty (?)) = ''
    # ExtraDamageTypeAdjusters (ArrayProperty) = []
    # ExtraFoodEffectivenessMultipliers (ArrayProperty) = []
    # FoodEffectivenessMultipliers (ArrayProperty) = []

    # DevKit Unverified
