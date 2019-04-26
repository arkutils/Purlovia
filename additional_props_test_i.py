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
# assetname = '/Game/Mods/Ragnarok/Custom_Assets/Dinos/Polar_Bear/Polar_Bear'
# assetname = '/Game/PrimalEarth/Dinos/Direbear/Direbear_Character_BP'
# assetname = '/Game/PrimalEarth/Dinos/Ptero/Ptero_Character_BP'
assetname = '/Game/PrimalEarth/Dinos/Giganotosaurus/Gigant_Character_BP'


def create_dict(prop):
    return dict((str(v.name), v.value) for v in prop.values)


# Using rounded as it matches the export file values
def get_lcolor(color):
    return [color[0].r.rounded, color[0].g.rounded, color[0].b.rounded, color[0].a.rounded]


def get_color_defs(asset):
    props = ark.mod.gather_properties(asset)

    color_defs = []
    for color_def in props['ColorDefinitions'][0][-1].values:
        color_dict = create_dict(color_def)
        color_defs.append([str(color_dict['ColorName']), get_lcolor(color_dict['ColorValue'].values)])
    return color_defs


loader = AssetLoader()

# Get Colors
core_media = loader['/Game/PrimalEarth/CoreBlueprints/COREMEDIA_PrimalGameData_BP']
#%%
color_defs = get_color_defs(core_media)
# print()
# pprint(color_defs)

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
        color_ids = []

        if prevent_region:
            color['name'] = 'null'
        else:
            color_set_defs = create_dict(male_colorset_props['ColorSetDefinitions'][i][-1])

            try:
                color['name'] = str(color_set_defs['RegionName'])
            except:
                color['name'] = 'No Name Available'

            for color_name in color_set_defs['ColorEntryNames'].values:
                color_id = [c_def[0] for c_def in color_defs].index(str(color_name)) + 1
                if str(color_id) not in color_ids:
                    color_ids.append(color_id)

        color['colorIds'] = color_ids
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