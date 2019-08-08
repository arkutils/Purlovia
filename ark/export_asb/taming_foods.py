# Hard coded 2.0 for taming_multiplier (multiplied against the server's taming_multiplier)
# Unsure if this is stored in an asset or the game's binary

# DinoSettings.FoodEffectivenessMultipliers[i].FoodEffectivenessMultiplier = food_mult
# DinoSettings.FoodEffectivenessMultipliers[i].HealthEffectivenessMultiplier = health_mult
# DinoSettings.FoodEffectivenessMultipliers[i].TorpidityEffectivenessMultiplier = torpor_mult
# DinoSettings.FoodEffectivenessMultipliers[i].AffinityEffectivenessMultiplier = affinity_mult
# DinoSettings.FoodEffectivenessMultipliers[i].AffinityOverride = affinity
# DinoSettings.FoodEffectivenessMultipliers[i].StaminaEffectivenessMultiplier = stamina_mult
# DinoSettings.FoodEffectivenessMultipliers[i].FoodItemCategory = food_category
# DinoSettings.FoodEffectivenessMultipliers[i].FoodItemParent = food_parent
# DinoSettings.FoodEffectivenessMultipliers[i].UntamedFoodConsumptionPriority = food_priority

# DinoSettings.ExtraFoodEffectivenessMultipliers[i].FoodEffectivenessMultiplier = extra_food_mult
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].HealthEffectivenessMultiplier = extra_health_mult
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].TorpidityEffectivenessMultiplier = extra_torpor_mult
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].AffinityEffectivenessMultiplier = extra_affinity_mult
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].AffinityOverride = extra_affinity
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].StaminaEffectivenessMultiplier = extra_stamina_mult
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].FoodItemCategory = extra_food_category
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].FoodItemParent = extra_food_parent
# DinoSettings.ExtraFoodEffectivenessMultipliers[i].UntamedFoodConsumptionPriority = extra_food_priority

# Item.UseItemAddCharacterStatusValues[i].BaseAmountToAdd = base_value
# Item.UseItemAddCharacterStatusValues[i].bPercentOfMaxStatusValue = is_percent_of_max
# Item.UseItemAddCharacterStatusValues[i].bPercentofCurrentStatusValue = is_percent_of_current
# Item.UseItemAddCharacterStatusValues[i].bUseItemQuality = use_quality
# Item.UseItemAddCharacterStatusValues[i].bDontRequireLessThanMaxToUse = not_require_less_than_max
# Item.UseItemAddCharacterStatusValues[i].bAddOverTime = is_over_time
# Item.UseItemAddCharacterStatusValues[i].bAddOverTimeSpeedInSeconds = is_over_time_in_secs
# Item.UseItemAddCharacterStatusValues[i].bSetValue = set_value
# Item.UseItemAddCharacterStatusValues[i].bSetAdditionalValue = set_add_value
# Item.UseItemAddCharacterStatusValues[i].bResetExistingModifierDescritionIndex = reset_existing_mod_desc_index
# Item.UseItemAddCharacterStatusValues[i].bForceUseStatOnDinos = use_stat_on_dino
# Item.UseItemAddCharacterStatusValues[i].LimitExistingModifierDescriptionToMaxAmount = limit_mod_desc_to_max
# Item.UseItemAddCharacterStatusValues[i].AddOverTimeSpeed = add_over_time_speed
# Item.UseItemAddCharacterStatusValues[i].PercentAbsoluteMaxValue = percent_absolute_max_value
# Item.UseItemAddCharacterStatusValues[i].PercentAbsoluteMinValue = percent_absolute_max_value
# Item.UseItemAddCharacterStatusValues[i].StatusValueModifierDescriptionIndex = stat_value_mod_desc_index #  2 (Used for Creatures?) || 1 (Used for Players?)
# Item.UseItemAddCharacterStatusValues[i].ItemQualityAddValueMultiplier = item_quality_add_value_multiplier
# Item.UseItemAddCharacterStatusValues[i].StatusValueType = stat_value_type #  EPrimalCharacterStatusValue::Food || EPrimalCharacterStatusValue::Torpidity || EPrimalCharacterStatusValue::Health
# Item.UseItemAddCharacterStatusValues[i].StopAtValueNearMax = stop_at_value_near_max
# Item.UseItemAddCharacterStatusValues[i].ScaleValueByCharacterDamageType = scale_value_by_character_damage_type

# for food_group in DinoSettings.FoodEffectivenessMultipliers:
#   for food in items[food_group]:
#        for food_stat in food.UseItemAddCharacterStatusValues:
#            if food_stat.StatusValueType == 'EPrimalCharacterStatusValue::Health'
#                health_value = food_group.HealthEffectivenessMultiplier * food.BaseAmountToAdd
#            elif food_stat.StatusValueType == 'EPrimalCharacterStatusValue::Stamina'
#                stamina_value = food_group.StaminaEffectivenessMultiplier * food.BaseAmountToAdd
#            elif food_stat.StatusValueType == 'EPrimalCharacterStatusValue::Food'
#                food_value = food_group.FoodEffectivenessMultiplier * food.BaseAmountToAdd
#            elif food_stat.StatusValueType == 'EPrimalCharacterStatusValue::Torpidity'
#                torpor_value = food_group.TorpidityEffectivenessMultiplier * food.BaseAmountToAdd
#
#   affinity = food_group.AffinityOverride
#   foods.add({food_name=food, affinity=affinity, food=food_value}) # health=health_value, stamina=stamina_value, torpor=torpor_value})
#
# for food in foods:
#   for food_group in DinoSettings.ExtraFoodEffectivenessMultipliers:
#       if food.has_parent(food_group.FoodItemParent):
#           food.affinity = food_group.AffinityOverride
#           food.food *= food_group.FoodEffectivenessMultiplier
#           if food.stamina:
#               food.stamina *= food_group.StaminaEffectivenessMultiplier
#           if food.torpor:
#               food.torpor *= food_group.TorpidityEffectivenessMultiplier
#           if food.health:
#               food.health *= food_group.HealthEffectivenessMultiplier

#%%
from __future__ import annotations

from dataclasses import dataclass, field
from io import StringIO
from pprint import *
from time import perf_counter, process_time
from typing import *

import ark.discovery
from automate.ark import ArkSteamManager, readModData
from ue.asset import UAsset
from ue.gathering import discover_inheritance_chain
from ue.loader import AssetNotFound, ModNotFound

arkman = ArkSteamManager()
loader = arkman.createLoader()
names_file = '__names.txt'
straight_file = '__straight.txt'
reverse_file = '__reverse.txt'


@dataclass  # simply to make instantiating easier
class Item:
    name: str
    # parent_name: Optional[str]
    # is_item: Optional[bool]
    # other item data goes here


@dataclass  # simply to make instantiating easier
class Node:
    item: Optional[Item] = field(default=None)
    class_name: str = field(default='')
    nodes: List[Node] = field(default_factory=list)  #pylint: disable=undefined-variable


def walk_tree(node: Node, fn):
    fn(node)
    for child in node.nodes:
        walk_tree(child, fn)


def add_item(item_list: List[Item], node: Node):
    if node.item is not None:
        item_list.append(node.item)


def find_all_of_type(node: Node) -> List[Item]:
    found: List[Item] = list()
    walk_tree(node, lambda n: add_item(found, n))
    return found


#%%
def register_item(node_lookup: Dict[str, Node], asset: UAsset):
    try:
        inheritance = discover_inheritance_chain(asset.default_class)  #type: ignore
    except ModNotFound:
        return
    except AssetNotFound:
        return
    branch = Node(item=Item(name=inheritance[-1]))  # Should call a function to gather item data
    for asset_str in reversed(inheritance):
        # An existing branch wasn't found, continue building the branch backwards
        if not node_lookup.get(asset_str):
            node_lookup[asset_str] = branch
            branch = Node(nodes=[branch])

        # An existing tree branch was found
        else:
            node_lookup[asset_str].nodes.append(branch)
            return

    # To be removed once proper "/Script" inheritance is implemented
    node_lookup['/Script/ShooterGame'].nodes.append(branch)


def register_item_straight(node_lookup: Dict[str, Node], asset: UAsset):
    try:
        inheritance = discover_inheritance_chain(asset.default_class)  #type: ignore
    except ModNotFound:
        return
    except AssetNotFound:
        return
    parent_class: str = '/Script/ShooterGame'
    for asset_str in inheritance:
        current_node = Node()
        if not node_lookup.get(asset_str):
            node_lookup[parent_class].nodes.append(current_node)
            node_lookup[asset_str] = current_node
        parent_class = asset_str
        # print(f'Evaluating {asset}\n{item}')
    item = Item(name=inheritance[-1])  # Should call a function to gather item data
    node_lookup[parent_class].item = item


#%% Attempt to load assets and verify if they're a species asset or not
def gather_names() -> Set[str]:
    assets_from_name = set()
    num_assets = 0
    name_checker = ark.discovery.ByRawData(loader)

    # Clear the file
    with open(names_file, 'w') as names:
        names.write('')

    with open(names_file, 'a') as names:
        for assetname in loader.find_assetnames('.*', toppath='/Game'):
            num_assets += 1
            if (num_assets % 100) == 0:
                print(num_assets)

            try:
                _ = loader[assetname]
                if name_checker.is_inventory_item(assetname):
                    assets_from_name.add(assetname)
                    names.write(f'{assetname}\n')

            except:
                continue

            loader.wipe_cache_with_prefix(assetname)

    return assets_from_name


def test_suite():
    # names = gather_names()
    with open(names_file) as f:
        names = f.readlines()
    lookup = test_to_run(names, register_item)
    print(to_graph(lookup['/Game/PrimalEarth/CoreBlueprints/Weapons/PrimalItem_WeaponBaseClub.PrimalItem_WeaponBaseClub_C']))


def clean_name(name):
    name = name.split('.')[-1]
    if name.endswith('_C'):
        name = name[:-2]
    if name.endswith('BP'):
        name = name[:-2]
    if name in ('PrimalItem', 'PrimalItem_Base'):
        return name
    name = name.replace('PrimalItem', '')
    name = name.strip('_')
    return name


def to_graph(tree: Node) -> str:
    s = StringIO()
    s.write('strict digraph {\n')

    def draw_node(node: Node):
        node_name = clean_name(node.item.name)
        for child in node.nodes:
            s.write(f'  "{clean_name(child.item.name)}" -> "{node_name}";\n')

    walk_tree(tree, draw_node)
    s.write('}\n')

    return s.getvalue()


def test_to_run(names: Set[str], func: Callable):
    root_base = '/Script/ShooterGame'

    tree = Node()
    lookup: Dict[str, Node] = dict()
    lookup[root_base] = tree
    for asset_name in names:
        func(lookup, loader[asset_name])
    # found_items = find_all_of_type(lookup['/Script/ShooterGame'])
    return lookup


test_suite()

#%%
