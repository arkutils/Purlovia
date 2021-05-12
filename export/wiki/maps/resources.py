from typing import Dict, List, Tuple

from ue.asset import ExportTableItem
from utils.log import get_logger

logger = get_logger(__name__)

# Mapping of known harvesting components' names to wiki's internal marker types.
# If a name is not mapped at all, or is mapped to a None, all nodes this component is attached to will be skipped.
#
# Full list of all marker types: https://ark.fandom.com/wiki/Template:ResourceMap
HARVEST_COMPONENT_MAPPING = {
    # Metal
    'MetalHarvestComponent_C': 'metal',
    'MetalHarvestComponent_Rich_C': 'metal-rich',
    'RAG_UnderwaterMetalHarvestComponent_C': 'metal-underwater',
    # Oil
    'OilHarvestComponent_C': 'oil-rock',
    'OilHarvestComponentRich_C': 'oil-rock',
    'OilHarvestComponentUnderwater_C': 'oil-rock',
    'OilSplatterHarvest_C': 'oil-rock',
    # Obsidian
    'ObsidianHarvestComponent_C': 'obsidian',
    'MountainObsidianHarvestComponent_C': 'obsidian',
    # Crystal
    'CrystalHarvestComponent_C': 'crystal',
    'CrystalBushHarvestComponent_C': 'crystal',
    'CrystalHarvestComponent_Summit_C': 'crystal',
    'CrystalHarvestComponent_UnderwaterCave_C': 'crystal',
    'CrystalPickupHarvestComponent_C': 'crystal',
    # Gems
    'GemFertileHarvestComponent_C': 'gem-green',
    'GemFertileHarvestComponent_Light_C': 'gem-green',
    'EX_GemFertileHarvestComponent_Light_C': 'gem-green',
    'GemBioLumHarvestComponent_C': 'gem-blue',
    'GemElementHarvestComponent_C': 'gem-red',
    'GemDrakeTrenchHarvestComponent_Light_C': 'gem-red',
    # Salt
    'RawSaltHarvestComponent_C': 'salt',
    'StoneHarvestComponent_Salt_C': 'salt',
    # Sulfur
    'SulfurHarvestComponent_C': 'sulfur',
    'EX_SulfurHarvestComponent_C': 'sulfur',
    # Element
    'ElementOreHarvestComponent_C': 'element-ore',
    'ElementShardHarvestComponent_C': 'element-shard',
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
    # Plants & Crops
    'RareFlowerHarvestComponent_C': 'rare-flower',
    'RareFlowerHarvestComponent_Jackson_C': 'rare-flower',
    'Carrot_Pickup_C': 'rockarrot',
    'Potatoe_Pickup_C': 'savoroot',
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

    # Naively determine if the level might be related to a cave.
    is_likely_cave = any(ident in export.asset.assetname for ident in CAVE_LEVEL_IDENTIFIERS)

    # Copy visible instances from export's extended data into the world.
    for x, y, z in export.extended_data.visible_instances:
        out[resource_type].append((x, y, z, is_likely_cave))
