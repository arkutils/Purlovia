from typing import List

from export.wiki.models import ClassRemap
from ue.asset import UAsset
from ue.utils import sanitise_output

__all__ = ['convert_npc_remaps']


def convert_npc_remaps(pgd: UAsset) -> List[ClassRemap]:
    assert pgd.default_export

    export_data = pgd.default_export.properties
    npcs = export_data.get_property('Remap_NPC', fallback=None)
    containers = export_data.get_property('Remap_NPCSpawnEntries', fallback=None)
    remaps = []

    if npcs:
        remaps += npcs.values
    if containers:
        remaps += containers.values

    out = []
    for entry in remaps:
        d = entry.as_dict()
        v = ClassRemap(
            from_bp=sanitise_output(d.get('FromClass', None)),
            to=sanitise_output(d.get('ToClass', None)),
        )

        if v.from_bp:
            out.append(v)

    return out
