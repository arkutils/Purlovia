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

default_color_regions = [0, 0, 0, 0, 0, 0]

if str(character_props['bUseColorization'][0][-1]) is 'False':
    print('No Color Regions Used')
else:
    male_colorset_asset = loader.load_related(character_props['RandomColorSetsMale'][0][-1])
    male_colorset_props = ark.mod.gather_properties(male_colorset_asset)

    # Female Colorset
    # female_colorset_asset = loader.load_related(character_props['RandomColorSetsFemale'][0][-1])
    # female_colorset_props = ark.mod.gather_properties(female_colorset_asset)

    # Reference from ASB's values.json file
    # "colors":[{"name":"Body Main","colorIds":[25,28,8,51,52,30,36,38,48,50,56]}
    # {"name":null,"colorIds":[]}
    colors = []
    for i, region in enumerate(default_color_regions):
        prevent_region = stat_value(character_props, 'PreventColorizationRegions', i, region)
        color = dict()
        color_names = []

        if prevent_region:
            color['name'] = 'null'
        else:
            color_set_defs = male_colorset_props['ColorSetDefinitions'][i][-1]

            # Color Set has a Region Name
            if str(color_set_defs.values[0].name) == 'RegionName':
                color['name'] = str(color_set_defs.values[0].value)
            else:
                color['name'] = 'No Name Available'

            if str(color_set_defs.values[-1].name) == 'ColorEntryNames':
                for color_name in color_set_defs.values[-1].value.values:
                    if str(color_name) not in color_names:
                        color_names.append(str(color_name))

        color['colorIds'] = color_names
        colors.append(color)

    pprint(colors)

#%% Get the taming data for the species
# print('\nTaming:\n')
# print(f'requiredTameAffinity: {stat_value(character_props, "RequiredTameAffinity", 0)}')
# print(f'requiredtameaffinityperbaselevel: {stat_value(character_props, "RequiredTameAffinityPerBaseLevel", 0)}')
# print(f'tameIneffectivenessByAffinity: {stat_value(character_props, "TameIneffectivenessByAffinity", 0)}')
# print(
#     f'tamingIneffectivenessModifierIncreaseByDamagePercent: {stat_value(character_props, "TamingIneffectivenessModifierIncreaseByDamagePercent", 0)}'
# )
# print(f'damageTypeAdjusters: {pretty(character_props["DamageTypeAdjusters"][0][-1])}')

# dino_settings_asset = loader.load_related(character_props["DinoSettingsClass"][0][-1])
# dino_settings_props = ark.mod.gather_properties(dino_settings_asset)

# taming_foods = []
# for food in dino_settings_props["FoodEffectivenessMultipliers"][0][-1].values:
#     food["FoodEffectivenessMultiplier"]
#     food["HealthEffectivenessMultiplier"]
#     food["TorpidityEffectivenessMultiplier"]
#     food["AffinityEffectivenessMultiplier"]
#     food["AffinityOverride"] # second d entry
#     food["StaminaEffectivenessMultiplier"]
#     food["FoodItemCategory"]
#     food["FoodItemParent"] # asset for actual food
#     food["UntamedFoodConsumptionPriority"]
#     for value in food.values:
#         print(f'Name: {value.name}\t\t Value: {value.value}')