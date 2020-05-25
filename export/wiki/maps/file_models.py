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
    oilVeins: List[models.OilVein] = []
    waterVeins: List[models.WaterVein] = []
    wyvernNests: List[models.WyvernNest] = []
    # Ragnarok
    iceWyvernNests: List[models.IceWyvernNest] = []
    # Aberration
    chargeNodes: List[models.ChargeNode] = []
    plantZNodes: List[models.PlantSpeciesZWild] = []
    drakeNests: List[models.DrakeNest] = []
    # Aberration and Genesis
    gasVeins: List[models.GasVein] = []
    # Valguero
    deinonychusNests: List[models.DeinonychusNest] = []
    # Genesis Part 1
    oilVents: List[models.OilVent] = []
    glitches: List[models.Glitch] = []
    magmasaurNests: List[models.MagmasaurNest] = []


EXPORTS: Dict[str, Type[ExportFileModel]] = {
    'world_settings': WorldSettings,
    'actors': Actors,
}
