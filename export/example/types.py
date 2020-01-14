from typing import Mapping

from ue.properties import ArrayProperty
from ue.proxy import UEProxyStructure, uefloats

__all__ = [
    'NPCSpawnEntriesContainer',
]


class NPCSpawnEntriesContainer(UEProxyStructure, uetype='/Script/ShooterGame.NPCSpawnEntriesContainer'):
    # DevKit Unverified
    MaxDesiredNumEnemiesMultiplier = uefloats(1.0)

    NPCSpawnEntries: Mapping[int, ArrayProperty]  # = []
    NPCSpawnLimits: Mapping[int, ArrayProperty]  # = []
