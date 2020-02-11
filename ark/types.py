from itertools import repeat
from typing import Mapping

from ue.properties import ArrayProperty, ByteProperty, LinearColor, ObjectProperty
from ue.proxy import *

STAT_COUNT = 12
COLOR_REGION_COUNT = 6


class Blueprint(UEProxyStructure, uetype='/Script/Engine.Blueprint'):
    # DevKit Unverified

    ParentClass: Mapping[int, ObjectProperty]
    SimpleConstructionScript: Mapping[int, ObjectProperty]
    BlueprintSystemVersion = ueints(0)
    GeneratedClass: Mapping[int, ObjectProperty]
    bLegacyNeedToPurgeSkelRefs = uebools()
    bLegacyGeneratedClassIsAuthoritative = uebools()
    # BlueprintGuid: Mapping[int, StructProperty]


class ShooterCharacterMovement(UEProxyStructure, uetype='/Script/ShooterGame.ShooterCharacterMovement'):
    # DevKit Verified
    Mass = uefloats(100.0)
    MaxCustomMovementSpeed = uefloats(600.0)
    MaxFlySpeed = uefloats(600.0)
    MaxSwimSpeed = uefloats(300.0)
    MaxWalkSpeed = uefloats(600.0)
    MaxWalkSpeedCrouched = uefloats(300.0)
    MaxWalkSpeedProne = uefloats(100.0)

    # DevKit Unverified

    # MaxStepHeight = [0] = '75.0',
    # JumpZVelocity[0] = '800.0',
    # WalkableFloorAngle[0] = '38.0',
    # WalkableFloorZ[0] = '0.788011 (inexact)',
    # MaxImpulseVelocityMagnitude[0] = '1.0',
    # MaxImpulseVelocityZ[0] = '1.0',
    # RotationRate[0] = StructProperty(Rotator(a='0.0', b='200.0', c='0.0')),
    # RotationAcceleration[0] = '78.0',
    # RotationBraking[0] = '78.0',
    # AngleToStartRotationBraking[0] = '70.0',
    # bUseRotationAcceleration[0] = True,
    # NavAgentProps[0] = StructProperty('bCanJump = (BoolProperty) True'),
    # UpdatedComponent[0] = ObjectProperty('CollisionCylinder (CapsuleComponent (Class) from /Script/Engine) [None]')


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

    # Components
    CharacterMovement = ProxyComponent[ShooterCharacterMovement]()

    # Flags
    bAllowCarryFlyerDinos = uebools(False)
    bAllowFlyerLandedRider = uebools(False)
    bAllowRunningWhileSwimming = uebools(False)
    bCanBeTamed = uebools(True)
    bCanBeTorpid = uebools(True)
    bCanCrouch = uebools(False)
    bCanHaveBaby = uebools(False)
    bCanRun = uebools(False)
    bFlyerAllowRidingInCaves = uebools(False)
    bIgnoreAllImmobilizationTraps = uebools(False)
    bIsBossDino = uebools(False)
    bIsCorrupted = uebools(False)
    bIsFlyerDino = uebools(False)
    bIsWaterDino = uebools(False)
    bPreventEnteringWater = uebools(False)
    bPreventImmobilization = uebools(False)
    bPreventSleepingTame = uebools(False)
    bSupportWakingTame = uebools(False)
    bUseBabyGestation = uebools(False)
    bUseColorization = uebools(False)

    # General
    CustomTag = uestrings('')  # NameProperty (Default: None)
    DescriptiveName = uestrings('')  # StringProperty (Default: 'PrimalCharacter')
    DinoNameTag = uestrings('')  # NameProperty (Default: None)
    DragWeight = uefloats(35.0)
    PreventColorizationRegions = uebytes(*repeat(0, COLOR_REGION_COUNT))

    # Breeding/reproduction
    BabyAgeSpeed = uefloats(0.033)  # TODO: needs raw data
    BabyGestationSpeed = uefloats(0.000035)  # TODO: needs raw data
    ExtraBabyAgeSpeedMultiplier = uefloats(1.0)
    ExtraBabyGestationSpeedMultiplier = uefloats(1.0)
    ExtraTamedBaseHealthMultiplier = uefloats(1.0)
    FertilizedEggItemsToSpawn: Mapping[int, ArrayProperty]  # = []
    NewFemaleMaxTimeBetweenMating = uefloats(172800.0)
    NewFemaleMinTimeBetweenMating = uefloats(64800.0)
    RequiredTameAffinity = uefloats(100)
    RequiredTameAffinityPerBaseLevel = uefloats(5.0)
    TameIneffectivenessByAffinity = uefloats(20)
    TargetingTeamNameOverride = uestrings('')
    WakingTameFoodAffinityMultiplier = uefloats(1.6)  # TODO: needs raw data
    WakingTameFoodIncreaseMultiplier = uefloats(1.0)

    # Coloring
    BoneDamageAdjusters: Mapping[int, ArrayProperty]  # = []
    RandomColorSetsFemale: Mapping[int, ObjectProperty]  # = 'None'
    RandomColorSetsMale: Mapping[int, ObjectProperty]  # = 'None'

    # Attacking
    AttackInfos: Mapping[int, ArrayProperty]
    MeleeDamageAmount = ueints(0)
    MeleeSwingRadius = uefloats(0.0)

    # Movement
    MaxFallSpeed = uefloats(1200.0)
    FallDamageMultiplier = uefloats(165.0)

    FlyingRunSpeedModifier = uefloats(1.0)
    RidingSwimmingRunSpeedModifier = uefloats(1.0)
    RunningSpeedModifier = uefloats(1.5)
    TamedRunningSpeedModifier = uefloats(1.0)
    UntamedRunningSpeedModifier = uefloats(1.0)
    ExtraUnTamedSpeedMultiplier = uefloats(1.0)
    ExtraTamedSpeedMultiplier = uefloats(1.0)

    ScaleExtraRunningMultiplierMax = uefloats(0.0)
    ScaleExtraRunningMultiplierMin = uefloats(0.0)
    ScaleExtraRunningMultiplierSpeed = uefloats(0.0)
    ScaleExtraRunningSpeedModifier = uebools(False)

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
    bIsEgg = uebools(False)
    bSupportDragOntoOtherItem = uebools(False)
    bUseItemDurability = uebools(True)
    bOverrideRepairingRequirements = uebools(False)
    bIsCookingIngredient = uebools(False)
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
    MaxDurabilitiyOverride = uefloats(0.0)
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
    CraftingSkillQualityMultiplierMin = uefloats(0.0)
    CraftingSkillQualityMultiplierMax = uefloats(0.05)
    NewItemDurabilityOverride = uefloats(-1.0)
    MyItemType = uebytes(('EPrimalItemType', 'MiscConsumable'))
    MyConsumableType = uebytes(('EPrimalConsumableType', 'Food'))
    MyEquipmentType = uebytes(('EPrimalEquipmentType', 'Hat'))
    Ingredient_WeightIncreasePerQuantity = uefloats(0.01)
    Ingredient_FoodIncreasePerQuantity = uefloats(0.1)
    Ingredient_HealthIncreasePerQuantity = uefloats(0.1)
    Ingredient_StaminaIncreasePerQuantity = uefloats(0.1)

    BaseCraftingResourceRequirements: Mapping[int, ArrayProperty]  # = []
    ItemIconMaterialParent: Mapping[int, ObjectProperty]  # = 'None'
    OverrideRepairingRequirements: Mapping[int, ArrayProperty]  # = []
    UseItemAddCharacterStatusValues: Mapping[int, ArrayProperty]  # = []
    SpoilingItem: Mapping[int, ObjectProperty]  # = 'None'
    StructureToBuild: Mapping[int, ObjectProperty]  # = 'None'
    WeaponTemplate: Mapping[int, ObjectProperty]  # = 'None'
    EggDinoClassToSpawn: Mapping[int, ObjectProperty]  # = 'None'

    # DevKit Unverified

    DefaultFolderPaths: Mapping[int, ArrayProperty]
    ItemIcon: Mapping[int, ObjectProperty]


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
