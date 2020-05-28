from typing import Dict, List, Optional, Tuple, Type, Union

from automate.hierarchy_exporter import ExportFileModel, Field

from . import models

__all__ = ['EXPORTS']


class MapExportFileModel(ExportFileModel):
    persistentLevel: str


class WorldSettings(MapExportFileModel):
    # Core
    worldSettings: Optional[models.WorldSettings] = None
    playerSpawns: List[models.PlayerSpawn] = []


class RadiationZones(MapExportFileModel):
    radiationVolumes: List[models.PainVolume]


class NPCSpawns(MapExportFileModel):
    spawns: List[models.NPCManager]


class Biomes(MapExportFileModel):
    biomes: List[models.Biome]


class LootCrates(MapExportFileModel):
    lootCrates: List[models.SupplyCrateSpawn]


class Actors(MapExportFileModel):
    # Core
    notes: List[models.ExplorerNote] = []
    # Scorched Earth
    oilVeins: List[models.OilVein] = []
    waterVeins: List[models.WaterVein] = []
    wyvernNests: List[models.WyvernNest] = []
    # Ragnarok
    iceWyvernNests: List[models.IceWyvernNest] = []
    # Genesis Part 1
    oilVents: List[models.OilVent] = []
    lunarOxygenVents: List[models.LunarOxygenVent] = []
    # Aberration
    gasVeins: List[models.GasVein] = []
    chargeNodes: List[models.ChargeNode] = []
    plantZNodes: List[models.PlantSpeciesZWild] = []
    drakeNests: List[models.DrakeNest] = []
    # Valguero
    deinonychusNests: List[models.DeinonychusNest] = []
    # Genesis Part 1
    glitches: List[models.Glitch] = []
    magmasaurNests: List[models.MagmasaurNest] = []
    poisonTrees: List[models.PoisonTree]


class Missions(MapExportFileModel):
    dispatchers: List[models.MissionDispatcher]


EXPORTS: Dict[str, Tuple[Type[ExportFileModel], str]] = {
    # File name -> ExportFileModel, FormatVersion
    'world_settings': (WorldSettings, '2'),
    'radiation_zones': (RadiationZones, '1'),
    'npc_spawns': (NPCSpawns, '1'),
    'biomes': (Biomes, '2'),
    'loot_crates': (LootCrates, '2'),
    'actors': (Actors, '1'),
    'missions': (Missions, '1'),
}
