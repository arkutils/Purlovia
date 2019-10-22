#%% Init
try:
    from interactive_utils import *
except:  # pylint: disable=bare-except
    pass

from dataclasses import dataclass, field
from io import StringIO
from operator import attrgetter
from typing import *

import ark.discovery
from automate.ark import ArkSteamManager, readModData
from config import get_global_config
from ue.asset import UAsset
from ue.gathering import discover_inheritance_chain
from ue.loader import AssetLoader, AssetNotFound, ModNotFound
from utils.tree import IndexedTree, Node

arkman = ArkSteamManager()
loader = arkman.getLoader()


#%%
@dataclass  # simply to make instantiating easier
class Item:
    name: str
    # asset: UAsset
    # is_item: Optional[bool]


def register_item(tree: IndexedTree[Item], asset: UAsset, discards: Set[str]):
    '''Register an item within the item hierarchy.'''
    assert asset.default_class
    try:
        inheritance = discover_inheritance_chain(asset.default_class, reverse=False)
    except (ModNotFound, AssetNotFound):
        return

    base = inheritance[0]
    if base in discards:
        print(f'  Discarding incorrect base: {base}')
        return
    if base not in tree:
        raise TypeError("Unable to find root type: " + base)

    last_name = None
    while inheritance:
        name = inheritance.pop(0)
        new_node = tree.get(name, None)
        if not new_node and last_name:
            tree.add(last_name, Item(name))
        elif not new_node and not last_name:
            raise TypeError('Unknown base type: ' + name)

        last_name = name


def discover_item_assets(progress=False) -> Iterator[str]:
    '''Discover assets that are likely to be item assets.'''
    name_checker = ark.discovery.ByRawData(loader)
    if progress:
        num_assets = 0
        num_found = 0

    # Collect ignore paths
    search_ignores = get_global_config().optimisation.SearchIgnore  # type: List[str]
    excludes = tuple(search_ignores)

    # Step through all candidate asset files
    for assetname in loader.find_assetnames('.*', exclude=excludes):
        if progress:
            num_assets += 1
            if not (num_assets % 500):
                print(f'Scanned {num_assets}, found {num_found}')
                print(assetname)

        # Is it likely to be an item?
        try:
            if name_checker.is_inventory_item(assetname):
                if progress:
                    num_found += 1
                yield assetname
        except (ModNotFound, AssetNotFound):
            pass

    if progress:
        print(f'Completed: Scanned {num_assets}, found {num_found}')


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


def to_graph(tree: Node[Item]) -> str:
    s = StringIO()
    s.write('strict digraph {\n')

    def draw_node(node: Node[Item]):
        node_name = clean_name(node.data.name)
        for child in node.nodes:
            s.write(f'  "{clean_name(child.data.name)}" -> "{node_name}";\n')

    tree.walk(draw_node)
    s.write('}\n')

    return s.getvalue()


ROOT_NAME = '/Script/ShooterGame.PrimalItem'

KNOWN_TREE = (
    ('/Script/ShooterGame.PrimalItem', '/Script/ShooterGame.PrimalStructure'),
    ('/Script/ShooterGame.PrimalItem', '/Script/ShooterGame.PrimalWeapon'),
    ('/Script/ShooterGame.PrimalItem', '/Script/ShooterGame.PrimalItem_Dye'),
    ('/Script/ShooterGame.PrimalItem', '/Script/ShooterGame.PrimalItem_Radio'),
    ('/Script/ShooterGame.PrimalWeapon', '/Script/ShooterGame.PrimalWeaponGrenade'),
    ('/Script/ShooterGame.PrimalStructure', '/Script/ShooterGame.PrimalStructureWaterPipe'),
)

DISCARD_ROOTS = {
    '/Script/ShooterGame.PrimalDinoCharacter',
    '/Script/ShooterGame.PrimalBuff',
}


def run(loader: AssetLoader) -> IndexedTree[Item]:
    # Prep tree
    tree = IndexedTree[Item](Item(ROOT_NAME), attrgetter('name'))
    for parent, child in KNOWN_TREE:
        tree.add(parent, Item(child))

    # Add all discovered item assets to it
    for assetname in discover_item_assets(progress=True):
        try:
            asset = loader[assetname]
        except AssetNotFound:
            continue

        register_item(tree, asset, DISCARD_ROOTS)

    return tree


# #%%

# test_assetnames = '''
# # /Game/PrimalEarth/CoreBlueprints/Items/Structures/Pipes/PrimalItemStructure_MetalPipeIncline
# # /Game/PrimalEarth/Structures/Pipes/WaterPipe_Metal_Vertical

# # /Game/PrimalEarth/Structures/TekTier/Beam_Tek
# # /Game/PrimalEarth/Structures/Wooden/Ramp_Wood_SM_New

# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_DinoPoopMedium
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_CookedMeat
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_CookedMeat_Jerky
# # /Game/Aberration/CoreBlueprints/Items/Consumables/PrimalItemResource_CommonMushroom
# # /Game/Aberration/CoreBlueprints/Items/Structures/PrimalItemStructure_Furniture_Rug
# # /Game/Aberration/CoreBlueprints/Items/Structures/BuildingBases/PrimalItemStructure_BaseCliffPlatform
# # /Game/Aberration/CoreBlueprints/Items/Trophies/PrimalItemStructure_Flag_Rockwell
# # /Game/Aberration/CoreBlueprints/Items/Trophies/PrimalItemTrophy_Rockwell
# # /Game/Aberration/CoreBlueprints/Items/Trophies/PrimalItemTrophy_Rockwell_Beta
# # /Game/Aberration/CoreBlueprints/Items/Trophies/PrimalItemTrophy_Rockwell_Beta_Alpha

# # /Game/Aberration/CoreBlueprints/Resources/PrimalItemConsumable_NamelessVenom
# # /Game/Aberration/CoreBlueprints/Resources/PrimalItemResource_ApexDrop_Basilisk
# # /Game/Aberration/CoreBlueprints/Resources/PrimalItemResource_ApexDrop_Basilisk_Alpha
# # /Game/Aberration/CoreBlueprints/Resources/PrimalItemResource_ApexDrop_CrabClaw
# # /Game/Aberration/CoreBlueprints/Resources/PrimalItemResource_ApexDrop_ReaperBarb
# # /Game/Aberration/CoreBlueprints/Resources/PrimalItemResource_ApexDrop_RockDrake
# # /Game/Aberration/CoreBlueprints/Resources/PrimalItemResource_ElementOre
# # /Game/Aberration/CoreBlueprints/Resources/PrimalItemResource_FungalWood
# # /Game/Aberration/CoreBlueprints/Resources/PrimalItemResource_Gas
# # /Game/Aberration/CoreBlueprints/Resources/PrimalItemResource_Gem_Base
# # /Game/Aberration/CoreBlueprints/Resources/PrimalItemResource_Gem_BioLum
# # /Game/Aberration/CoreBlueprints/Resources/PrimalItemResource_Gem_Element
# # /Game/Aberration/CoreBlueprints/Resources/PrimalItemResource_XenomorphPheromoneGland

# # /Game/Aberration/CoreBlueprints/Weapons/PrimalItemAmmo_Zipline
# # /Game/Aberration/WeaponGlowStickThrow/PrimalItem_GlowStick
# # /Game/Aberration/WeaponPlantSpeciesZ/PrimalItemConsumable_Seed_PlantSpeciesZ
# # /Game/Aberration/WeaponPlantSpeciesZ/PrimalItemConsumable_Seed_PlantSpeciesZ_SpeedHack
# # /Game/Aberration/WeaponPlantSpeciesZ/PrimalItem_PlantSpeciesZ_Grenade
# # /Game/Aberration/WeaponRadioactiveLanternCharge/PrimalItem_WeaponRadioactiveLanternCharge
# # /Game/Aberration/WeaponTekSniper/PrimalItem_TekSniper

# # /Game/Extinction/CoreBlueprints/Items/PrimalItemStructure_CryoFridge
# # /Game/Extinction/CoreBlueprints/Items/PrimalItemStructure_TaxidermyBase_Large
# # /Game/Extinction/CoreBlueprints/Items/PrimalItemStructure_TaxidermyBase_Medium
# # /Game/Extinction/CoreBlueprints/Items/PrimalItemStructure_TaxidermyBase_Small
# # /Game/Extinction/CoreBlueprints/Items/PrimalItem_DinoSpawner_Base
# # /Game/Extinction/CoreBlueprints/Items/PrimalItem_Spawner_Enforcer
# # /Game/Extinction/CoreBlueprints/Items/PrimalItem_Spawner_Mek
# # /Game/Extinction/CoreBlueprints/Items/Artifacts/PrimalItemArtifact_Extinction_DesertKaiju
# # /Game/Extinction/CoreBlueprints/Items/Artifacts/PrimalItemArtifact_Extinction_ForestKaiju
# # /Game/Extinction/CoreBlueprints/Items/Artifacts/PrimalItemArtifact_Extinction_IceKaiju
# # /Game/Extinction/CoreBlueprints/Items/Saddle/PrimalItemArmor_DesertKaiju

# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Allo
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_AnkyloEgg
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_ArchaEgg
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_BaryonyxEgg
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Base
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Base_Large
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Base_Medium
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Base_Small
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Base_Special
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Base_XLarge
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Base_XSmall
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_BoaEgg
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_CarnoEgg
# /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_ArgentEgg
# /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Compy
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_DiloEgg
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_DimetroEgg
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_DimorphEgg
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_DiploEgg
# # /Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_DodoEgg

# /Game/Extinction/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Base_Large_EX
# /Game/Extinction/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Base_Medium_EX
# /Game/Extinction/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Base_Small_EX
# # /Game/Extinction/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Base_Special_EX
# # /Game/Extinction/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Base_XLarge_EX
# # /Game/Extinction/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Base_XSmall_EX
# '''
# assetnames = {n.strip() for n in test_assetnames.split('\n') if n and not n.startswith('#')}

#%%
tree = run(loader)

#%%
check_node = '/Game/PrimalEarth/CoreBlueprints/Items/Consumables/PrimalItemConsumable_Kibble_Base_XSmall.PrimalItemConsumable_Kibble_Base_XSmall_C'
with open('tmp/graph.dot', 'w') as f:
    f.write(to_graph(tree[check_node]))

#%%
# print(f'\n{check_node}:')
# tree[check_node].walk(lambda node: print('  ' + node.data.name))

#%%
