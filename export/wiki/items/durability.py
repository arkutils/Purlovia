from typing import Optional

from ark.types import PrimalItem
from automate.hierarchy_exporter import ExportModel, Field
from ue.properties import FloatProperty


class DurabilityData(ExportModel):
    min: Optional[FloatProperty] = Field(..., title="Minimum number of units")


def convert_durability_values(item: PrimalItem) -> DurabilityData:
    return DurabilityData(min=item.MinItemDurability[0], )
