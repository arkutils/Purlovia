from itertools import repeat
from typing import Mapping

from ue.properties import ArrayProperty, ObjectProperty
from ue.proxy import *

__all__ = [
    'ZONE_MANAGER_EXPORTED_PROPERTIES',
    'BIOME_VOLUME_EXPORTED_PROPERTIES',
    'NPCZoneManager',
    'BiomeZoneVolume'
]

ZONE_MANAGER_EXPORTED_PROPERTIES = {
    'NPCSpawnEntriesContainerObject': 'spawnGroup',
    'MinDesiredNumberOfNPC': 'MinDesiredNumberOfNPC',
    'bNeverSpawnInWater': 'bNeverSpawnInWater',
    'bForceUntameable': 'bForceUntameable',
}

BIOME_VOLUME_EXPORTED_PROPERTIES = {
    'BiomeZoneName': 'BiomeZoneName',
    'BiomeZonePriority': 'BiomeZonePriority',
    'bIsOutside': 'bIsOutside',
    'bPreventCrops': 'bPreventCrops',
    'AbsoluteTemperatureOverride': 'AbsoluteTemperatureOverride',
    'FinalTemperatureAddition': 'FinalTemperatureAddition',
    'PerOffsetTemperatureAddition': 'PerOffsetTemperatureAddition',
    'AboveTemperatureOffsetThreshold': 'AboveTemperatureOffsetThreshold',
    'AboveTemperatureOffsetMultiplier': 'AboveTemperatureOffsetMultiplier',
    'BelowTemperatureOffsetThreshold': 'BelowTemperatureOffsetThreshold',
    'BelowTemperatureOffsetMultiplier': 'BelowTemperatureOffsetMultiplier',
}

SUPPLY_DROP_EXPORTED_PROPERTIES = {
    'MaxNumCrates': 'maxNumCrates',
}

class NPCZoneManager(UEProxyStructure, uetype='/Script/ShooterGame.NPCZoneManager'):
    # DevKit Verified

    # DevKit Unverified
    bEnabled = uebools(True)
    bNeverSpawnInWater = uebools(False)
    MinDesiredNumberOfNPC = ueints(0)
    bForceUntameable = uebools(False)

    NPCSpawnEntriesContainerObject: Mapping[int, ObjectProperty]
    LinkedZoneVolumes: Mapping[int, ArrayProperty]
    LinkedZoneSpawnVolumeEntries: Mapping[int, ArrayProperty]
    SpawnPointOverrides: Mapping[int, ArrayProperty]


class BiomeZoneVolume(UEProxyStructure, uetype='/Script/ShooterGame.BiomeZoneVolume'):
    # DevKit Verified

    # DevKit Unverified
    BiomeZoneName = uestrings('')
    BiomeZonePriority = ueints(0)
    bHidden = uebools(False) # No idea what this does.
    bIsOutside = uebools(True)
    bPreventCrops = uebools(False)
    AbsoluteTemperatureOverride = uefloats(0)
    FinalTemperatureAddition = uefloats(0)
    PerOffsetTemperatureAddition = uefloats(0)
    AboveTemperatureOffsetThreshold = uefloats(0)
    AboveTemperatureOffsetMultiplier = uefloats(0)
    BelowTemperatureOffsetThreshold = uefloats(0)
    BelowTemperatureOffsetMultiplier = uefloats(0)


class SupplyCrateSpawningVolume(UEProxyStructure, uetype='/Script/ShooterGame.SupplyCrateSpawningVolume'):
    # DevKit Verified

    # DevKit Unverified
    bHidden = uebools(False) # No idea what this does.
    MaxNumCrates = ueints(1)

    LinkedSupplyCrateEntries: Mapping[int, ArrayProperty]
    LinkedSpawnPointEntries: Mapping[int, ArrayProperty]
