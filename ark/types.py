from itertools import repeat
from typing import Mapping

from ue.properties import ArrayProperty, LinearColor, ObjectProperty
from ue.proxy import LazyReference, ProxyComponent, UEProxyStructure, uebools, uebytes, uefloats, ueints, uestrings

STAT_COUNT = 12
COLOR_REGION_COUNT = 6

BLUEPRINT_CLS = '/Script/Engine.Blueprint'
PCSC_CLS = '/Script/ShooterGame.PrimalCharacterStatusComponent'
PDSC_CLS = '/Script/ShooterGame.PrimalDinoStatusComponent'
PDC_CLS = '/Script/ShooterGame.PrimalDinoCharacter'
PGD_CLS = '/Script/ShooterGame.PrimalGameData'
PRIMAL_CHR_CLS = '/Script/ShooterGame.PrimalCharacter'
PRIMAL_ITEM_CLS = '/Script/ShooterGame.PrimalItem'
PRIMAL_ITEM_DYE_CLS = '/Script/ShooterGame.PrimalItem_Dye'
PRIMAL_DINO_SETTINGS_CLS = '/Script/ShooterGame.PrimalDinoSettings'
SHOOTER_CHR_MOVEMENT_CLS = '/Script/ShooterGame.ShooterCharacterMovement'
PRIMAL_COLOR_SET_CLS = '/Script/ShooterGame.PrimalColorSet'

DCSC_CLS = '/Game/PrimalEarth/CoreBlueprints/DinoCharacterStatusComponent_BP.DinoCharacterStatusComponent_BP_C'
DINO_CHR_CLS = '/Game/PrimalEarth/CoreBlueprints/Dino_Character_BP.Dino_Character_BP_C'

COREMEDIA_PGD_PKG = '/Game/PrimalEarth/CoreBlueprints/COREMEDIA_PrimalGameData_BP'

FLOAT_0_2 = (0.20000000, 'cdcc4c3e')
FLOAT_1_0 = (1.00000000, '0000803f')
FLOAT_100_0 = (100.00000000, '0000c842')


class PrimalCharacterStatusComponent(UEProxyStructure, uetype=PCSC_CLS):
    BabyDinoConsumingFoodRateMultiplier = uefloats((25.50000000, '0000cc41'))
    BabyMaxHealthPercent = uefloats((0.10000000, 'cdcccc3d'))
    BaseCharacterLevel = ueints(1)
    BaseFoodConsumptionRate = uefloats((-0.02500000, 'cdccccbc'))
    CrouchedWaterFoodConsumptionMultiplier = uefloats(FLOAT_1_0)
    DinoMaxStatAddMultiplierImprinting = uefloats(
        FLOAT_0_2,  # [0]
        0,
        FLOAT_0_2,  # [2]
        0,
        FLOAT_0_2,  # [4]
        FLOAT_0_2,  # [5]
        0,
        FLOAT_0_2,  # [7]
        FLOAT_0_2,  # [8]
        FLOAT_0_2,  # [9]
        0,
        0,
    )
    DinoTamedAdultConsumingFoodRateMultiplier = uefloats(FLOAT_1_0)
    ExtraBabyDinoConsumingFoodRateMultiplier = uefloats((20.00000000, '0000a041'))
    ExtraFoodConsumptionMultiplier = uefloats(FLOAT_1_0)
    ExtraTamedHealthMultiplier = uefloats((1.35000002, 'cdccac3f'))
    FoodConsumptionMultiplier = uefloats(FLOAT_1_0)
    KnockedOutTorpidityRecoveryRateMultiplier = uefloats((3.00000000, '00004040'))
    MaxStatusValues = uefloats(
        FLOAT_100_0,  # [0]
        FLOAT_100_0,  # [1]
        FLOAT_100_0,  # [2]
        FLOAT_100_0,  # [3]
        FLOAT_100_0,  # [4]
        FLOAT_100_0,  # [5]
        0,
        0,
        0,
        0,
        0,
        0,
    )
    MaxTamingEffectivenessBaseLevelMultiplier = uefloats((0.50000000, '0000003f'))
    ProneWaterFoodConsumptionMultiplier = uefloats(FLOAT_1_0)
    RecoveryRateStatusValue = uefloats(
        FLOAT_100_0,  # [0]
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
    )
    TamedBaseHealthMultiplier = uefloats(FLOAT_1_0)
    TamingIneffectivenessMultiplier = uefloats(FLOAT_1_0)
    TheMaxTorporIncreasePerBaseLevel = uefloats((0.06000000, '8fc2753d'))
    WakingTameFoodConsumptionRateMultiplier = uefloats((2.00000000, '00000040'))
    WalkingStaminaConsumptionRate = uefloats((-0.30000001, '9a9999be'))
    RunningStaminaConsumptionRate = uefloats(-5)
    SwimmingOrFlyingStaminaConsumptionRate = uefloats(-0.3)


class Blueprint(UEProxyStructure, uetype=BLUEPRINT_CLS):
    # DevKit Unverified

    ParentClass: Mapping[int, ObjectProperty]
    SimpleConstructionScript: Mapping[int, ObjectProperty]
    BlueprintSystemVersion = ueints(0)
    GeneratedClass: Mapping[int, ObjectProperty]
    bLegacyNeedToPurgeSkelRefs = uebools()
    bLegacyGeneratedClassIsAuthoritative = uebools()
    # BlueprintGuid: Mapping[int, StructProperty]


class ShooterCharacterMovement(UEProxyStructure, uetype=SHOOTER_CHR_MOVEMENT_CLS):
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


class PrimalDinoStatusComponent(PrimalCharacterStatusComponent, uetype=PDSC_CLS):
    # DevKit Verified
    AmountMaxGainedPerLevelUpValue = uefloats(*repeat(0, STAT_COUNT))
    AmountMaxGainedPerLevelUpValueTamed = uefloats(*repeat(0, STAT_COUNT))
    bCanSuffocate = uebools(True)
    bCanSuffocateIfTamed = uebools(False)
    bForceGainOxygen = uebools(False)
    CanLevelUpValue = uefloats(*repeat(0, STAT_COUNT))
    DontUseValue = uefloats(*repeat(0, STAT_COUNT))
    TamingMaxStatAdditions = uefloats(*repeat(0, STAT_COUNT))
    TamingMaxStatMultipliers = uefloats(*repeat(0, STAT_COUNT))

    MaxExperiencePoints = uefloats(100000.0)
    LevelExperienceRampType = uebytes(('ELevelExperienceRampType', 'Player'))

    # DevKit Unverified
    StatusValueNameOverrides: Mapping[int, ArrayProperty]


class DinoCharacterStatusComponent(PrimalDinoStatusComponent, uetype=DCSC_CLS):
    pass


class PrimalColorSet(UEProxyStructure, uetype=PRIMAL_COLOR_SET_CLS):
    # DevKit Verified
    ColorSetDefinitions: Mapping[int, ArrayProperty]

    # DevKit Unverified


class PrimalDinoCharacter(UEProxyStructure, uetype=PDC_CLS):
    # DevKit Verified

    # Components
    CharacterMovement = ProxyComponent[ShooterCharacterMovement]()

    # Flags
    bAllowCarryFlyerDinos = uebools(False)
    bAllowFlyerLandedRider = uebools(False)
    bAllowRunningWhileSwimming = uebools(False)
    bAutoTameable = uebools(False)
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
    bIsRobot = uebools(False)
    bIsVehicle = uebools(False)
    bIsWaterDino = uebools(False)
    bPreventCloning = uebools(False)
    bPreventEnteringWater = uebools(False)
    bPreventImmobilization = uebools(False)
    bPreventMating = uebools(False)
    bPreventSleepingTame = uebools(False)
    bPreventUploading = uebools(False)
    bSupportWakingTame = uebools(False)
    bUniqueDino = uebools(False)
    bUseBabyGestation = uebools(False)
    bUseColorization = uebools(False)

    # General
    CustomTag = uestrings('')  # NameProperty (Default: None)
    DescriptiveName = uestrings('')  # StringProperty (Default: 'PrimalCharacter')
    DinoNameTag = uestrings('')  # NameProperty (Default: None)
    DragWeight = uefloats(35.0)
    PreventColorizationRegions = uebytes(*repeat(0, COLOR_REGION_COUNT))
    AutoFadeOutAfterTameTime = uefloats(0.0)

    # Breeding/reproduction
    BabyAgeSpeed = uefloats((0.03300000, '022b073d'))
    BabyGestationSpeed = uefloats((0.0000347222, 'b4a21138'))
    ExtraBabyAgeSpeedMultiplier = uefloats(FLOAT_1_0)
    ExtraBabyGestationSpeedMultiplier = uefloats(FLOAT_1_0)
    ExtraTamedBaseHealthMultiplier = uefloats(FLOAT_1_0)
    FertilizedEggItemsToSpawn: Mapping[int, ArrayProperty]  # = []
    FemaleMatingTime = uefloats(0.0)
    NewFemaleMaxTimeBetweenMating = uefloats((172800.00000000, '00c02848'))
    NewFemaleMinTimeBetweenMating = uefloats((64800.00000000, '00207d47'))
    RequiredTameAffinity = uefloats(FLOAT_100_0)
    RequiredTameAffinityPerBaseLevel = uefloats((5.00000000, '0000a040'))
    TameIneffectivenessByAffinity = uefloats((20.00000000, '0000a041'))
    TargetingTeamNameOverride = uestrings('')
    WakingTameFoodAffinityMultiplier = uefloats((1.60000002, 'cdcccc3f'))
    WakingTameFoodIncreaseMultiplier = uefloats(FLOAT_1_0)

    # Coloring
    BoneDamageAdjusters: Mapping[int, ArrayProperty]  # = []
    RandomColorSetsFemale = LazyReference[PrimalColorSet]()
    RandomColorSetsMale = LazyReference[PrimalColorSet]()

    # Attacking
    AttackInfos: Mapping[int, ArrayProperty]
    MeleeDamageAmount = ueints(0)
    MeleeSwingRadius = uefloats(0.0)

    # Movement
    MaxFallSpeed = uefloats(1200.0)
    FallDamageMultiplier = uefloats(165.0)

    FlyingRunSpeedModifier = uefloats(1.0)
    SwimmingRunSpeedModifier = uefloats(1.0)
    RidingSwimmingRunSpeedModifier = uefloats(1.0)
    RunningSpeedModifier = uefloats(1.5)
    UntamedWalkingSpeedModifier = uefloats(1.0)
    TamedWalkingSpeedModifier = uefloats(1.0)
    TamedRunningSpeedModifier = uefloats(1.0)
    UntamedRunningSpeedModifier = uefloats(1.0)
    ExtraUnTamedSpeedMultiplier = uefloats(1.0)
    ExtraTamedSpeedMultiplier = uefloats(1.0)

    ScaleExtraRunningMultiplierMax = uefloats(0.0)
    ScaleExtraRunningMultiplierMin = uefloats(0.0)
    ScaleExtraRunningMultiplierSpeed = uefloats(0.0)
    ScaleExtraRunningSpeedModifier = uebools(False)

    DefaultLandMovementMode = uebytes(('EMovementMode', 'MOVE_Walking'))
    SubmergedWaterMovementMode = uebytes(('EMovementMode', 'MOVE_Swimming'))
    WaterSubmergedDepthThreshold = uefloats(0.7)

    # Cloning
    CloneBaseElementCost = uefloats(0)
    CloneElementCostPerLevel = uefloats(0)

    # Experience
    OverrideDinoMaxExperiencePoints = uefloats(0)
    DestroyTamesOverLevelClampOffset = ueints(0)

    # DevKit Unverified


class PrimalGameData(UEProxyStructure, uetype=PGD_CLS):
    # DevKit Verified
    ModDescription = uestrings('')
    ModName = uestrings('')

    ColorDefinitions: Mapping[int, ArrayProperty]  # = []
    MasterDyeList: Mapping[int, ArrayProperty]  # = []

    # DevKit Unverified


class PrimalItem(UEProxyStructure, uetype=PRIMAL_ITEM_CLS):
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
    bCraftDontActuallyGiveItem = uebools(False)
    ItemQuantity = ueints(1)
    CraftingGivesItemQuantityOverride = ueints(0)
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


class PrimalItem_Dye(PrimalItem, uetype=PRIMAL_ITEM_DYE_CLS):
    bSupportDragOntoOtherItem = uebools(True)
    # DevKit Verified
    DyeColor: Mapping[int, LinearColor]  # = (0.0, 0.0, 0.0, 0.0)
    DyeUISceneTemplate: Mapping[int, ObjectProperty]  # = None

    # DevKit Unverified


class PrimalDinoSettings(UEProxyStructure, uetype=PRIMAL_DINO_SETTINGS_CLS):
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
