from typing import Optional, Tuple

from ark.types import PrimalItem
from automate.hierarchy_exporter import ExportModel, Field
from ue.properties import FloatProperty
from utils.log import get_logger

logger = get_logger(__name__)


class EggData(ExportModel):
    dinoClass: Optional[str] = Field(..., title="Dino to be spawned")
    temperature: Optional[Tuple[FloatProperty, FloatProperty]] = Field(False, title="Hatching temperature range")


def convert_egg_values(item: PrimalItem) -> Optional[EggData]:
    dino_class = item.get('EggDinoClassToSpawn', 0, None)
    if not dino_class:
        return None

    return EggData(
        dinoClass=str(dino_class),
        temperature=(item.EggMinTemperature[0], item.EggMaxTemperature[0]),
    )
