from typing import Mapping

from ark.types import PrimalItem
from ue.properties import ArrayProperty, ByteProperty, NameProperty, ObjectProperty, StructProperty
from ue.proxy import *

from .consts import *

__all__ = [
    'BiomeZoneVolume',
    'CustomActorList',
    'DayCycleManager_Gen1',
    'ExplorerNote',
    'GasVein',
    'GasVeinGen1',
    'LunarOxygenVentGen1',
    'MissionDispatcher_MultiUsePylon',
    'NPCSpawnEntriesContainer',
    'NPCZoneManager',
    'OilVein',
    'OilVentGen1',
    'PlayerStart',
    'PointOfInterestBP',
    'PointOfInterestListGen1',
    'PrimalEngramEntry',
    'PrimalStructureItemContainer_SupplyCrate',
    'PrimalStructurePowerNode',
    'PrimalWorldSettings',
    'SupplyCrateSpawningVolume',
    'TogglePainVolume',
    'WaterVein',
    'WildPlantSpeciesZ',
]


class PrimalWorldSettings(UEProxyStructure, uetype='/Script/ShooterGame.PrimalWorldSettings'):
    # DevKit Verified
    Title = uestrings('')
    LatitudeOrigin = uefloats(-400_000.0)
    LongitudeOrigin = uefloats(-400_000.0)
    LatitudeScale = uefloats(800.0)
    LongitudeScale = uefloats(800.0)
    OverrideDifficultyMax = uefloats(5.0)
    bPreventGlobalNonEventSpawnOverrides = uebools(False)

    # DevKit Unverified

    OverrideWeaponMapTextureEmpty: Mapping[int, ObjectProperty]
    OverrideWeaponMapTextureFilled: Mapping[int, ObjectProperty]
    OverrideUIMapTextureEmpty: Mapping[int, ObjectProperty]
    OverrideUIMapTextureFilled: Mapping[int, ObjectProperty]
    OverrideUIMapTextureSmall: Mapping[int, ObjectProperty]
    AllowDownloadDinoClasses: Mapping[int, ArrayProperty]
    NPCRandomSpawnClassWeights: Mapping[int, StructProperty]


class NPCZoneManager(UEProxyStructure, uetype='/Script/ShooterGame.NPCZoneManager'):
    # DevKit Verified
    bEnabled = uebools(True)
    MinDesiredNumberOfNPC = ueints(-1)
    bNeverSpawnInWater = uebools(False)
    bForceUntameable = uebools(False)

    # DevKit Unverified

    NPCSpawnEntriesContainerObject: Mapping[int, ObjectProperty]
    LinkedZoneVolumes: Mapping[int, ArrayProperty]
    LinkedZoneSpawnVolumeEntries: Mapping[int, ArrayProperty]
    SpawnPointOverrides: Mapping[int, ArrayProperty]


class BiomeZoneVolume(UEProxyStructure, uetype='/Script/ShooterGame.BiomeZoneVolume'):
    # DevKit Verified
    BiomeZoneName = uestrings('')  # Should be None.
    BiomeZonePriority = ueints(0)
    bIsOutside = uebools(True)
    bPreventCrops = uebools(False)

    FinalTemperatureMultiplier = uefloats(1.0)
    FinalTemperatureExponent = uefloats(1.0)
    FinalTemperatureAddition = uefloats(0)

    PreOffsetTemperatureMultiplier = uefloats(1.0)
    PreOffsetTemperatureExponent = uefloats(1.0)
    PreOffsetTemperatureAddition = uefloats(0)

    AboveTemperatureOffsetThreshold = uefloats(1_000_000.0)
    AboveTemperatureOffsetMultiplier = uefloats(1.0)
    AboveTemperatureOffsetExponent = uefloats(1.0)

    BelowTemperatureOffsetThreshold = uefloats(-1_000_000.0)
    BelowTemperatureOffsetMultiplier = uefloats(1.0)
    BelowTemperatureOffsetExponent = uefloats(1.0)

    AbsoluteTemperatureOverride = uefloats(-1_000_000.0)
    AbsoluteMaxTemperature = uefloats(70.0)
    AbsoluteMinTemperature = uefloats(-999.0)

    AbsoluteWindOverride = uefloats(-1_000_000.0)

    PreOffsetWindMultiplier = uefloats(1.0)
    PreOffsetWindExponent = uefloats(1.0)
    PreOffsetWindAddition = uefloats(0.0)

    AboveWindOffsetThreshold = uefloats(1_000_000.0)
    AboveWindOffsetMultiplier = uefloats(1.0)
    AboveWindOffsetExponent = uefloats(1.0)

    BelowWindOffsetThreshold = uefloats(-1_000_000.0)
    BelowWindOffsetMultiplier = uefloats(1.0)
    BelowWindOffsetExponent = uefloats(1.0)

    FinalWindMultiplier = uefloats(0.0)
    FinalWindExponent = uefloats(1.0)
    FinalWindAddition = uefloats(0.0)

    # DevKit Unverified


class SupplyCrateSpawningVolume(UEProxyStructure, uetype='/Script/ShooterGame.SupplyCrateSpawningVolume'):
    # DevKit Verified
    bIsEnabled = uebools(False)
    MaxNumCrates = ueints(0)
    DelayBeforeFirstCrate = uefloats(0)
    MaxDelayBeforeFirstCrate = uefloats(0)
    IntervalBetweenCrateSpawns = uefloats(0)
    MaxIntervalBetweenCrateSpawns = uefloats(0)
    IntervalBetweenMaxedCrateSpawns = uefloats(0)
    MaxIntervalBetweenMaxedCrateSpawns = uefloats(0)
    SP_IntervalBetweenCrateSpawns = uefloats(0)
    SP_MaxIntervalBetweenCrateSpawns = uefloats(0)
    SP_IntervalBetweenMaxedCrateSpawns = uefloats(0)
    SP_MaxIntervalBetweenMaxedCrateSpawns = uefloats(0)
    MinTimeBetweenCrateSpawnsAtSamePoint = uefloats(0)

    # DevKit Unverified

    LinkedSupplyCrateEntries: Mapping[int, ArrayProperty]
    LinkedSpawnPointEntries: Mapping[int, ArrayProperty]


class TogglePainVolume(UEProxyStructure, uetype='/Script/ShooterGame.TogglePainVolume'):
    # DevKit Verified
    bPainCausing = uebools(True)

    # DevKit Unverified

    ActorClassesToExclude: Mapping[int, ArrayProperty]
    DamageType: Mapping[int, ObjectProperty]
    RootComponent: Mapping[int, ObjectProperty]  # SceneComponent


class CustomActorList(UEProxyStructure, uetype='/Script/ShooterGame.CustomActorList'):
    # No properties we can assume type for.
    CustomTag: Mapping[int, NameProperty]
    ActorList: Mapping[int, ArrayProperty]


class PointOfInterestListGen1(UEProxyStructure, uetype=POINT_OF_INTEREST_LIST_GEN1_CLS):
    # No properties we can assume type for.
    ActorList: Mapping[int, ArrayProperty]


class PointOfInterestBP(
        UEProxyStructure,
        uetype=
        '/Game/Genesis/Missions/Debugging/PointOfInterestBP_MissionStart_Debugging.PointOfInterestBP_MissionStart_Debugging_C'):
    # DevKit Verified
    Specific_Unlocked_Explorer_Note_Index = ueints(-1)
    number_of_hexagons_to_reward_upon_fixing = ueints(1000)

    # DevKit Unverified

    MyPointOfInterestData: Mapping[int, StructProperty]


class OilVein(UEProxyStructure, uetype=OIL_VEIN_CLS):
    # No properties we can assume type for.
    RootComponent: Mapping[int, ObjectProperty]  # SceneComponent


class OilVentGen1(UEProxyStructure, uetype=OIL_VENT_GEN1_CLS):
    # No properties we can assume type for.
    RootComponent: Mapping[int, ObjectProperty]  # SceneComponent


class GasVeinGen1(UEProxyStructure, uetype=GAS_VEIN_GEN1_CLS):
    # No properties we can assume type for.
    RootComponent: Mapping[int, ObjectProperty]  # SceneComponent


class LunarOxygenVentGen1(UEProxyStructure, uetype=LUNAR_OXYGEN_VENT_GEN1_CLS):
    # No properties we can assume type for.
    RootComponent: Mapping[int, ObjectProperty]  # SceneComponent


class WaterVein(UEProxyStructure, uetype=WATER_VEIN_CLS):
    # No properties we can assume type for.
    RootComponent: Mapping[int, ObjectProperty]  # SceneComponent


class GasVein(UEProxyStructure, uetype=GAS_VEIN_CLS):
    # No properties we can assume type for.
    RootComponent: Mapping[int, ObjectProperty]  # SceneComponent


class PrimalStructurePowerNode(UEProxyStructure, uetype=CHARGE_NODE_CLS):
    # No properties we can assume type for.
    RootComponent: Mapping[int, ObjectProperty]  # SceneComponent


class WildPlantSpeciesZ(UEProxyStructure, uetype=WILD_PLANT_SPECIES_Z_CLS):
    # No properties we can assume type for.
    RootComponent: Mapping[int, ObjectProperty]  # SceneComponent


class ExplorerNote(UEProxyStructure, uetype=EXPLORER_CHEST_BASE_CLS):
    # DevKit Verified
    bIsVisible = uebools(True)

    # DevKit Unverified
    ExplorerNoteIndex = ueints(0)

    # No properties we can assume type for.
    RootComponent: Mapping[int, ObjectProperty]  # SceneComponent


class NPCSpawnEntriesContainer(UEProxyStructure, uetype='/Script/ShooterGame.NPCSpawnEntriesContainer'):
    # DevKit Unverified
    MaxDesiredNumEnemiesMultiplier = uefloats(1.0)

    NPCSpawnEntries: Mapping[int, ArrayProperty]  # = []
    NPCSpawnLimits: Mapping[int, ArrayProperty]  # = []


class PrimalStructureItemContainer_SupplyCrate(UEProxyStructure,
                                               uetype='/Script/ShooterGame.PrimalStructureItemContainer_SupplyCrate'):
    # DevKit Verified
    bSetsRandomWithoutReplacement = uebools(False)
    InitialTimeToLoseHealth = uefloats(20.0)
    IntervalTimeToLoseHealth = uefloats(120.0)
    MaxLevelToAccess = ueints(0)
    MinItemSets = uefloats(1.0)
    MaxItemSets = uefloats(1.0)
    MinQualityMultiplier = uefloats(1.0)
    MaxQualityMultiplier = uefloats(1.0)
    NumItemSetsPower = uefloats(1.0)
    RequiredLevelToAccess = ueints(0)

    # DevKit Unverified

    ItemSets: Mapping[int, ArrayProperty]
    AdditionalItemSets: Mapping[int, ArrayProperty]


class PrimalEngramEntry(UEProxyStructure, uetype='/Script/ShooterGame.PrimalEngramEntry'):
    # DevKit Verified
    RequiredCharacterLevel = ueints(0)
    RequiredEngramPoints = ueints(1)
    bGiveBlueprintToPlayerInventory = uebools(True)
    bCanBeManuallyUnlocked = uebools(True)
    ExtraEngramDescription = uestrings('')

    # DevKit Unverified

    BluePrintEntry: Mapping[int, ObjectProperty]  # PrimalItem ref
    EngramRequirementSets: Mapping[int, ArrayProperty]
    EngramGroup: Mapping[int, ByteProperty]


class DayCycleManager_Gen1(UEProxyStructure, uetype='/Script/ShooterGame.DayCycleManager'):
    # No properties we can assume type for.
    GenesisTradableOptions: Mapping[int, ArrayProperty]


class MissionDispatcher_MultiUsePylon(
        UEProxyStructure, uetype='/Game/Genesis/Missions/MissionDispatcher_MultiUsePylon.MissionDispatcher_MultiUsePylon_C'):
    # DevKit Verified

    # DevKit Unverified
    MissionTypeIndex = ueints(0)

    MissionTypes: Mapping[int, ArrayProperty]
    RootComponent: Mapping[int, ObjectProperty]


class PlayerStart(UEProxyStructure, uetype='/Script/Engine.PlayerStart'):
    # DevKit Verified
    SpawnPointRegion = ueints(-1)

    # DevKit Unverified

    RootComponent: Mapping[int, ObjectProperty]  # Collision/Trigger component
