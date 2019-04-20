#%% Setup
from interactive_utils import *
from ue.base import UEBase
from ue.asset import UAsset
from ue.loader import AssetLoader
from ue.stream import MemoryStream
from ue.utils import *
from ue.properties import *
import ark.mod
import ark.asset
from ark.properties import stat_value

# Equation References: https://ark.gamepedia.com/DevKit

# assetname = '/Game/PrimalEarth/Dinos/Dodo/Dodo_Character_BP'
# Note the Polar Bear's Asset path (Character is missing)
# assetname = '/Game/Mods/Ragnarok/Custom_Assets/Dinos/Polar_Bear/Polar_Bear'
# assetname = '/Game/PrimalEarth/Dinos/Direbear/Direbear_Character_BP'
assetname = '/Game/PrimalEarth/Dinos/Ptero/Ptero_Character_BP'
# assetname = '/Game/PrimalEarth/Dinos/Giganotosaurus/Gigant_Character_BP'

loader = AssetLoader()
character_asset = loader[assetname]
character_props = ark.mod.gather_properties(character_asset)

#%% Get the colorsets for both genders
# character_props['ColorizationIntensity'][0][-1]
# character_props['bUseColorization'][0][-1]

male_colorset_asset = loader.load_related(character_props['RandomColorSetsMale'][0][-1])
# female_colorset_asset = loader.load_related(character_props['RandomColorSetsFemale'][0][-1])

male_colorset_props = ark.mod.gather_properties(male_colorset_asset)
# female_colorset_props = ark.mod.gather_properties(female_colorset_asset)

male_colorset_props['ColorSetDefinitions'][0][-1]
# female_colorset_props['ColorSetDefinitions'][0][-1]

#%% Get the taming data for the species
print('\nTaming:\n')
print(f'requiredTameAffinity: {stat_value(character_props, "RequiredTameAffinity", 0)}')
print(f'requiredtameaffinityperbaselevel: {stat_value(character_props, "RequiredTameAffinityPerBaseLevel", 0)}')
print(f'tameIneffectivenessByAffinity: {stat_value(character_props, "TameIneffectivenessByAffinity", 0)}')
print(
    f'tamingIneffectivenessModifierIncreaseByDamagePercent: {stat_value(character_props, "TamingIneffectivenessModifierIncreaseByDamagePercent", 0)}'
)
print(f'damageTypeAdjusters: {pretty(character_props["DamageTypeAdjusters"][0][-1])}')

#%% Get the breeding data for the species
# Determines if a species is breedable (most likely anyways) :shrug:
# print(character_props['bCanHaveBaby'][0][-1])

# if this, 'incubationTime' = 0; else gestationTime = 0
incubation_time = 0
gestation_time = 0
fert_egg_props = None
if character_props['bUseBabyGestation']:
    # 'gestationTime' = 1 / (Baby Gestation Speed × Extra Baby Gestation Speed Multiplie)
    # gestation_speed = character_props['BabyGestationSpeed'][0][-1].value
    # READ ME!!! DevKit mentions this properties name is BITBREAK. It shares that name with
    #   several other properties, presumably a property only found in the binary. I haven't
    #   looked at much more than the properties thus far, but definitely worth a dig as
    #   it isn't showing up in the properties inherited, but there are other properties
    #   that we need to add to the file as well.
    # Values verified through DevKit, not the binary

    gestation_speed = stat_value(character_props, 'BabyGestationSpeed', 0, 0.000035)
    extra_gestation_speed_m = stat_value(character_props, 'ExtraBabyGestationSpeedMultiplier', 0, 1.0)
    gestation_time = 1 / gestation_speed / extra_gestation_speed_m

    print('\nGestation:\n')

elif character_props['FertilizedEggItemsToSpawn'][0]:
    # In the blueprint of the fertilized egg PrimalItemConsumable_Egg_…_Fertilized:
    # Usually an array(?) but ASB only supports 1 fertilized egg
    fert_egg_asset = loader.load_related(character_props['FertilizedEggItemsToSpawn'][0][-1].values[0])
    fert_egg_props = ark.mod.gather_properties(fert_egg_asset)

    # 'incubationTime' = 100 / (Egg Lose Durability Per Second × Extra Egg Lose Durability Per Second Multiplier)
    egg_decay = stat_value(fert_egg_props, 'EggLoseDurabilityPerSecond', 0)
    extra_egg_decay_m = stat_value(fert_egg_props, 'ExtraEggLoseDurabilityPerSecondMultiplier', 0)
    incubation_time = 100 / egg_decay / extra_egg_decay_m

    print('\nEggs:\n')
    min_temp = stat_value(fert_egg_props, 'EggMinTemperature', 0)
    print(f'eggTempMin: {min_temp}')
    max_temp = stat_value(fert_egg_props, 'EggMaxTemperature', 0)
    print(f'eggTempMax: {max_temp}')

print(f'gestationTime: {gestation_time}')
print(f'incubationTime: {incubation_time}')

print('\nRaising:\n')
# 'maturationTime' = 1 / (Baby Age Speed × Extra Baby Age Speed Multiplier)
baby_age_speed = stat_value(character_props, 'BabyAgeSpeed', 0)
extra_baby_age_speed_m = stat_value(character_props, 'ExtraBabyAgeSpeedMultiplier', 0)
mature_time = 1 / baby_age_speed / extra_baby_age_speed_m
print(f'maturationTime: {mature_time}')

# Not included in most Character assets (inherited from the Primal Dino Character asset)
# 'matingCooldownMin' (default: 64800.0)
min_mating_cooldown = stat_value(character_props, 'NewFemaleMinTimeBetweenMating', 0, 64800.0)
print(f'matingCooldownMin: {min_mating_cooldown}')

# Not included in most Character assets (inherited from the Primal Dino Character asset)
# 'matingCooldownMax' (default: 172800.0)
max_mating_cooldown = stat_value(character_props, 'NewFemaleMaxTimeBetweenMating', 0, 172800.0)
print(f'matingCooldownMax: {max_mating_cooldown}')

###############################
# Seemingly irrelevant properties
###############################
# Baby's size compared to parent
# print(character_props['BabyScale'][0][-1].value)

# Might be related to recent imprinting overhaul and just coincidence it's close to maturity time
# print(character_props['BabyImprintingQualityTotalMaturationTime'][0][-1].value)

# Appears to be a time to mate during mating session (2 minutes of mating)
# print(character_props['FemaleMatingTime'][0][-1].value)

# Baby's relative movement speed (too slow, Wildcard!)
# print(character_props['BabySpeedMultiplier'][0][-1].value)

# How fast it is ejected from the womb?
# print(character_props['BabyPitchMultiplier'][0][-1].value)
# How annoyingly loud the baby's sounds are?
# print(character_props['BabyVolumeMultiplier'][0][-1].value)

# I know, I know, just trying to have some fun while I die of banging my head
#   against my keyboard. Just left it for you to chuckle about

###############################
# Data Dumps
###############################
# values.json - Polar Bear
# "breeding":{
#     "gestationTime":14285.713867,
#     "incubationTime":0,
#     "maturationTime":166666.65625,
#     "matingCooldownMin":64800,
#     "matingCooldownMax":172800
# }

# ark-data - Dire Bear
# "breeding":{
#     "gestationTime":14285.713867,
#     "maturationTime":166666.65625,
#     "babyTime":16666.666016,
#     "juvenileTime":66666.664063,
#     "adolescentTime":83333.328125,
#     "minTimeBetweenMating":64800,
#     "maxTimeBetweenMating":172800
# },

# ark-data for Pteranodon
# "breeding":{
#     "eggs":[
#         {
#             "minTemp":29,
#             "maxTemp":32,
#             "incubationTime":5999.520508
#         }
#     ],
#     "maturationTime":133333.328125,
#     "babyTime":13333.333008,
#     "juvenileTime":53333.332031,
#     "adolescentTime":66666.664063,
#     "minTimeBetweenMating":64800,
#     "maxTimeBetweenMating":172800
# },

# ark-data for Gigant
# "breeding":{
#     "eggs":[
#         {
#             "minTemp":43,
#             "maxTemp":44,
#             "incubationTime":179985.609375
#         }
#     ],
#     "maturationTime":1010100.875,
#     "babyTime":101010.085938,
#     "juvenileTime":404040.34375,
#     "adolescentTime":505050.4375,
#     "minTimeBetweenMating":64800,
#     "maxTimeBetweenMating":172800
# },

# values.json - Ice Wyvern
# "breeding":{
#     "gestationTime":0,
#     "incubationTime":17998.560547,
#     "maturationTime":333333.3125,
#     "matingCooldownMin":64800,
#     "matingCooldownMax":172800,
#     "eggTempMin":80,
#     "eggTempMax":90
# },
