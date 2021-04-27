from typing import Optional, Tuple

from ark.types import PrimalItem
from automate.hierarchy_exporter import ExportModel, Field
from ue.properties import FloatProperty
from utils.log import get_logger

logger = get_logger(__name__)


class EggData(ExportModel):
    dinoClass: str = Field(..., title="Dino to be spawned")
    temperature: Tuple[FloatProperty, FloatProperty] = Field(..., title="Hatching temperature range")


def convert_egg_values(item: PrimalItem) -> Optional[EggData]:
    dino_class = item.get('EggDinoClassToSpawn', 0, None)
    if not dino_class or not dino_class.value or not dino_class.value.value:
        return None

    return EggData(
        dinoClass=dino_class.value.value.format_for_json(),
        temperature=(item.EggMinTemperature[0], item.EggMaxTemperature[0]),
    )
