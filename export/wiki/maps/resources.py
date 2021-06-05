from typing import Dict, List, Tuple

from ue.asset import ExportTableItem
from ue.utils import get_leaf_from_assetname
from utils.log import get_logger

logger = get_logger(__name__)

# Mapping of known harvesting components' names to wiki's internal marker types.
# If a name is not mapped at all, or is mapped to a None, all nodes this component is attached to will be skipped.
#
# Full list of all marker types: https://ark.fandom.com/wiki/Template:ResourceMap
# TODO: overrides.yaml
HARVEST_COMPONENT_MAPPING = {
    # Metal
    'MetalHarvestComponent_C': 'metal',
    'MetalHarvestComponent_Rich_C': 'metal-rich',
    'SpaceMetalHarvestComponent_Rich_C': 'metal-rich',
    'RAG_UnderwaterMetalHarvestComponent_C': 'metal-underwater',
    # Oil
    'OilHarvestComponent_C': 'oil-rock',
    'OilHarvestComponentRich_C': 'oil-rock',
    'OilHarvestComponentUnderwater_C': 'oil-rock',
    'OilSplatterHarvest_C': 'oil-rock',
    'SpaceOilHarvestComponent_C': 'oil-rock',
    # Obsidian
    'ObsidianHarvestComponent_C': 'obsidian',
    'MountainObsidianHarvestComponent_C': 'obsidian',
    'SpaceObsidianHarvestComponent_C': 'obsidian',
    # Crystal
    'CrystalHarvestComponent_C': 'crystal',
    'CrystalBushHarvestComponent_C': 'crystal',
    'CrystalHarvestComponent_Summit_C': 'crystal',
    'CrystalHarvestComponent_UnderwaterCave_C': 'crystal',
    'CrystalPickupHarvestComponent_C': 'crystal',
    'CrystalHarvestComponent_HIGH_C': 'crystal-rich',
    # Gems
    'GemFertileHarvestComponent_C': 'gem-green',
    'GemFertileHarvestComponent_Light_C': 'gem-green',
    'EX_GemFertileHarvestComponent_Light_C': 'gem-green',
    'GemGreenHarvestComponent_C': 'gem-green',
    'GemBioLumHarvestComponent_C': 'gem-blue',
    'GemBlueHarvestComponent_C': 'gem-blue',
    'GemElementHarvestComponent_C': 'gem-red',
    'GemDrakeTrenchHarvestComponent_Light_C': 'gem-red',
    'GemRedHarvestComponent_C': 'gem-red',
    # Salt
    'RawSaltHarvestComponent_C': 'salt',
    'StoneHarvestComponent_Salt_C': 'salt',
    # Sulfur
    'SulfurHarvestComponent_C': 'sulfur',
    'EX_SulfurHarvestComponent_C': 'sulfur',
    'SulfurHarvestComponent_C': 'sulfur',
    # Element
    'ElementOreHarvestComponent_C': 'element-ore',
    'ElementShardHarvestComponent_C': 'element-shard',
    'ElementDustHarvestComponent_C': 'dust-rich',
    'CityPropHarvestComponent_C': 'dust-rich',
    'CityPropHarvestComponent_Light_C': 'dust-rich',
    'CityPropHarvestComponent_NoLight_C': 'dust-rich',
    # Pearls
    'SiliconHarvestComponent_C': 'silica',
    'SiliconHarvestComponent_gen_C': 'silica',
    'BlackPearlHarvestComponent_C': 'black-pearl',
    'BlackPearlHarvest_C': 'black-pearl',
    # Keratin
    'BoneHarvestComponent_C': 'keratin',
    'BonesHarvestComponent_C': 'keratin',
    # Cactus
    'CactusHarvestComponent_C': 'cactus',
    'CactusHarvestComponent_GEN_C': 'cactus',
    'CactusHarvestComponent_Ex_Base_C': 'cactus',
    'CactusHarvestComponent_Ex_Large_C': 'cactus',
    'CactusLargeHarvestComponent_C': 'cactus',
    'CactusManyBerriesWithPlantYHarvestComponent_C': 'cactus',
    'CactusManyBerriesHarvestComponent_C': 'cactus',
    'CactusFewBerriesHarvestComponent_C': 'cactus',
    'CactusFewBerriesHarvestComponent_Ex_C': 'cactus',
    'CactusManyBerriesWithPlantYHarvestComponent_C': 'cactus',
    'SeedCactus_HarvestComponent_C': 'cactus',
    # Plants & Crops
    'RareFlowerHarvestComponent_C': 'rare-flower',
    'RareFlowerHarvestComponent_Jackson_C': 'rare-flower',
    'Carrot_Pickup_C': 'rockarrot',
    'Potatoe_Pickup_C': 'savoroot',
    # Ambergris
    'AmbergrisHarvestComponent_C': 'ambergris',
    # Mutagel
    'MutagelHarvestComponent_C': 'mutagel',
}

LEVEL_NAME_EXTRA_SUFFIX = {
    # Genesis 2 asteroid fields
    # Level names found in /Game/Genesis2/CoreBlueprints/Environment/DayCycleManager_Gen2
    # Ambergris
    'Space_Backdrop_Asteroids_0': ' rot0',
    'Space_Asteroids_0_Geo': ' rot0',
    # Crystal
    'Space_Backdrop_Asteroids_1': ' rot1',
    'Space_Asteroids_1_Geo': ' rot1',
    # Sulfur
    'Space_Backdrop_Asteroids_2': ' rot2',
    'Space_Asteroids_2_Geo': ' rot2',
    # Element Shard
    'Space_Backdrop_Asteroids_3': ' rot3',
    'Space_Asteroids_3_Geo': ' rot3',
    # Obsidian
    'Space_Backdrop_Asteroids_4': ' rot4',
    'Space_Asteroids_4_Geo': ' rot4',
    # Oil
    'Space_Backdrop_Asteroids_5': ' rot5',
    'Space_Asteroids_5_Geo': ' rot5',
    # Element Dust
    'Space_Backdrop_Asteroids_6': ' rot6',
    'Space_Asteroids_6_Geo': ' rot6',
    # Black Pearls
    'Space_Backdrop_Asteroids_7': ' rot7',
    'Space_Asteroids_7_Geo': ' rot7',
}

ResourceNodesByType = Dict[str, List[Tuple[float, float, float, bool]]]

# TODO: Move to overrides.yaml
CAVE_LEVEL_IDENTIFIERS = (
    'Cave',
    'Dungeon',
)


def collect_harvestable_resources(export: ExportTableItem, out: ResourceNodesByType):
    assert export.properties
    assert export.extended_data

    # Retrieve the harvesting component class and check if it's valid.
    component = export.properties.get_property('AttachedComponentClass', fallback=None)
    if not component or not component.value or not component.value.value:
        return

    # Get a resource type identifier if one is available. Skip otherwise.
    component_name = str(component.value.value.name)
    resource_type = HARVEST_COMPONENT_MAPPING.get(component_name, None)
    if not resource_type:
        return

    # Add a suffix to the resource type depending on level (Genesis 2 rotations)
    level_name = get_leaf_from_assetname(export.asset.assetname)
    suffix = LEVEL_NAME_EXTRA_SUFFIX.get(level_name, None)
    if suffix:
        resource_type += suffix

    # Naively determine if the level might be related to a cave.
    is_likely_cave = any(ident in export.asset.assetname for ident in CAVE_LEVEL_IDENTIFIERS)

    # Copy visible instances from export's extended data into the world.
    for x, y, z in export.extended_data.visible_instances:
        out[resource_type].append((x, y, z, is_likely_cave))
