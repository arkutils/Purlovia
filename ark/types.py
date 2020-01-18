from itertools import repeat
from typing import Mapping

from ue.properties import ArrayProperty, LinearColor, ObjectProperty
from ue.proxy import *

STAT_COUNT = 12
COLOR_REGION_COUNT = 6


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
    PreventColorizationRegions = uebytes(*repeat(0, COLOR_REGION_COUNT))
    RequiredTameAffinity = uefloats(100)
    RequiredTameAffinityPerBaseLevel = uefloats(5.0)
    TameIneffectivenessByAffinity = uefloats(20)
    WakingTameFoodAffinityMultiplier = uefloats(1.6)  # TODO: needs raw data
    WakingTameFoodIncreaseMultiplier = uefloats(1.0)

    RandomColorSetsMale: Mapping[int, ObjectProperty]  # = 'None'
    RandomColorSetsFemale: Mapping[int, ObjectProperty]  # = 'None'
    FertilizedEggItemsToSpawn: Mapping[int, ArrayProperty]  # = []
    BoneDamageAdjusters: Mapping[int, ArrayProperty]  # = []

    # DevKit Unverified


class ShooterCharacterMovement(UEProxyStructure, uetype='/Script/ShooterGame.ShooterCharacterMovement'):
    # DevKit Verified
    Mass = uefloats(100.0)

    # DevKit Unverified


class PrimalGameData(UEProxyStructure, uetype='/Script/ShooterGame.PrimalGameData'):
    # DevKit Verified
    ModDescription = uestrings('')
    ModName = uestrings('')

    ColorDefinitions: Mapping[int, ArrayProperty]  # = []
    MasterDyeList: Mapping[int, ArrayProperty]  # = []

    # DevKit Unverified


class PrimalItem(UEProxyStructure, uetype='/Script/ShooterGame.PrimalItem'):
    # DevKit Verified
    bSupportDragOntoOtherItem = uebools(False)
    bUseItemDurability = uebools(True)
    bPreventCheatGive = uebools(False)
    bAllowRepair = uebools(True)
    bDurabilityRequirementIgnoredInWater = uebools(False)
    BaseCraftingXP = uefloats(2.0)
    BaseRepairingXP = uefloats(2.0)
    BaseItemWeight = uefloats(0.5)
    CraftingMinLevelRequirement = ueints(0)
    BlueprintTimeToCraft = uefloats(5.0)
    DroppedItemLifeSpanOverride = uefloats(0.0)
    MaxItemQuantity = ueints(1)
    MinBlueprintTimeToCraft = uefloats(0.1)
    MinItemDurability = uefloats(0.0)
    DescriptiveNameBase = uestrings('')
    EggLoseDurabilityPerSecond = uefloats(1.0)
    EggMaxTemperature = uefloats(30.0)
    EggMinTemperature = uefloats(15.0)
    ExtraEggLoseDurabilityPerSecondMultiplier = uefloats(1.0)
    ItemDescription = uestrings('')
    SpoilingTime = uefloats(0.0)
    TimeForFullRepair = uefloats(5.0)
    CraftingGiveItemCount = ueints(1)
    RepairResourceRequirementMultiplier = uefloats(0.5)

    BaseCraftingResourceRequirements: Mapping[int, ArrayProperty]  # = []
    OverrideRepairingRequirements: Mapping[int, ArrayProperty] # = []
    UseItemAddCharacterStatusValues: Mapping[int, ArrayProperty]  # = []
    SpoilingItem: Mapping[int, ObjectProperty]

    # DevKit Unverified

    DefaultFolderPaths: Mapping[int, ArrayProperty]
    ItemIcon: Mapping[int, ObjectProperty]
    StructureToBuild: Mapping[int, ObjectProperty]
    WeaponToBuild: Mapping[int, ObjectProperty]


class PrimalItem_Dye(PrimalItem, uetype='/Script/ShooterGame.PrimalItem_Dye'):
    bSupportDragOntoOtherItem = uebools(True)
    # DevKit Verified
    DyeColor: Mapping[int, LinearColor]  # = (0.0, 0.0, 0.0, 0.0)
    DyeUISceneTemplate: Mapping[int, ObjectProperty]  # = None

    # DevKit Unverified


class PrimalDinoSettings(UEProxyStructure, uetype='/Script/ShooterGame.PrimalDinoSettings'):
    # DevKit Verified
    DinoFoodTypeName = uestrings('')
    TamingAffinityNoFoodDecreasePercentageSpeed = uefloats(0.0075)  # TODO: needs raw data
    WakingTameDisplayItemName = uebools(False)

    BaseDamageTypeAdjusters: Mapping[int, ArrayProperty]  # = []
    ExtraDamageTypeAdjusters: Mapping[int, ArrayProperty]  # = []
    ExtraFoodEffectivenessMultipliers: Mapping[int, ArrayProperty]  # = []
    FoodEffectivenessMultipliers: Mapping[int, ArrayProperty]  # = []
    DinoFoodTypeImage: Mapping[int, ObjectProperty]  # = None

    # DevKit Unverified
