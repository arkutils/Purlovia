from typing import Dict, List, Optional, Tuple, Type, Union

from automate.hierarchy_exporter import ExportFileModel, Field

from . import gathering, models

__all__ = ['EXPORTS']


class WorldSettings(ExportFileModel):
    # Core
    worldSettings: Optional[models.WorldSettings] = None
    playerSpawns: List[models.PlayerSpawn] = []
    notes: List[models.ExplorerNote] = []
    # Genesis Part 1
    trades: List[models.ObjectPath] = []


class Actors(ExportFileModel):
    # Core
    notes: List[models.ExplorerNote] = []
    # Scorched Earth
    oilVeins: List[models.Actor] = []
    waterVeins: List[models.Actor] = []
    wyvernNests: List[models.Actor] = []
    # Ragnarok
    iceWyvernNests: List[models.Actor] = []
    # Aberration
    chargeNodes: List[models.Actor] = []
    plantZNodes: List[models.Actor] = []
    drakeNests: List[models.Actor] = []
    # Aberration and Genesis
    gasVeins: List[models.Actor] = []
    # Valguero
    deinonychusNests: List[models.Actor] = []
    # Genesis Part 1
    oilVents: List[models.Actor] = []
    glitches: List[models.Glitch] = []
    magmasaurNests: List[models.Actor] = []


EXPORTS: Dict[Tuple[str, Type[ExportFileModel]], Dict[str, gathering.MapGathererBase]] = {
    ('world_settings', WorldSettings): {},
    ('actors', Actors): {
        'oilVeins': gathering.OilVeinExport,
        'waterVeins': gathering.WaterVeinExport,
        'wyvernNests': gathering.WyvernNests,
        'iceWyvernNests': gathering.IceWyvernNests,
        'chargeNodes': gathering.ChargeNodeExport,
        'plantZNodes': gathering.WildPlantSpeciesZExport,
        'drakeNests': gathering.RockDrakeNests,
        'gasVeins': gathering.GasVeinExport,
        'deinonychusNests': gathering.DeinonychusNests,
        'oilVents': gathering.OilVentExport,
        'magmasaurNests': gathering.MagmasaurNests,
    }
}
