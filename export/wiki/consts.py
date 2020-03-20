from ue.consts import SCRIPT_ENGINE_PKG

SCRIPT_ARK_PKG = '/Script/ShooterGame'
ABERRATION_PKG = '/Game/Aberration/'
SCORCHED_EARTH_PKG = '/Game/ScorchedEarth/'

ACTOR_CLS = SCRIPT_ENGINE_PKG + '.Actor'
WORLD_CLS = SCRIPT_ENGINE_PKG + '.World'
LEVEL_SCRIPT_ACTOR_CLS = SCRIPT_ENGINE_PKG + '.LevelScriptActor'

# Core
PRIMAL_WORLD_SETTINGS_CLS = SCRIPT_ARK_PKG + '.PrimalWorldSettings'
NPC_ZONE_MANAGER_CLS = SCRIPT_ARK_PKG + '.NPCZoneManager'
BIOME_ZONE_VOLUME_CLS = SCRIPT_ARK_PKG + '.BiomeZoneVolume'
SUPPLY_CRATE_SPAWN_VOLUME_CLS = SCRIPT_ARK_PKG + '.SupplyCrateSpawningVolume'
TOGGLE_PAIN_VOLUME_CLS = SCRIPT_ARK_PKG + '.TogglePainVolume'
CUSTOM_ACTOR_LIST_CLS = SCRIPT_ARK_PKG + '.CustomActorList'
EXPLORER_CHEST_BASE_CLS = '/Game/PrimalEarth/CoreBlueprints/ExplorerChest/ExplorerChest_Base.ExplorerChest_Base_C'
# Scorched Earth
OIL_VEIN_CLS = SCORCHED_EARTH_PKG + 'Structures/OilPump/OilVein_Base_BP.OilVein_Base_BP_C'
WATER_VEIN_CLS = SCORCHED_EARTH_PKG + 'Structures/WaterWell/WaterVein_Base_BP.WaterVein_Base_BP_C'
# Aberration
GAS_VEIN_CLS = ABERRATION_PKG + 'Structures/GasCollector/GasVein_Base_BP.GasVein_Base_BP_C'
CHARGE_NODE_CLS = ABERRATION_PKG + 'Structures/PowerNode/PrimalStructurePowerNode.PrimalStructurePowerNode_C'
WILD_PLANT_SPECIES_Z_CLS = ABERRATION_PKG + 'WeaponPlantSpeciesZ/Structure_PlantSpeciesZ_Wild.Structure_PlantSpeciesZ_Wild_C'
DAMAGE_TYPE_RADIATION_PKG = ABERRATION_PKG + 'CoreBlueprints/DamageTypes/DmgType_Radiation.DmgType_Radiation_C'
# Genesis
GAS_VEIN_GEN1_CLS = '/Game/Genesis/Structures/GasVein/GasVein_Base_Gen_BP.GasVein_Base_Gen_BP_C'
OIL_VENT_GEN1_CLS = '/Game/Genesis/Structures/GasVein/OilVent_BP.OilVent_BP_C'
LUNAR_OXYGEN_VENT_GEN1_CLS = '/Game/Genesis/Structures/GasVein/LunarOxygenVent_BP.LunarOxygenVent_BP_C'
POINT_OF_INTEREST_LIST_GEN1_CLS = '/Script/ShooterGame.PointOfInterestManagerList'
