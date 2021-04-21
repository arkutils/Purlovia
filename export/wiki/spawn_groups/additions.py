from collections import defaultdict
from typing import Dict, List, Optional

from automate.hierarchy_exporter import ExportModel, Field
from ue.asset import UAsset
from ue.utils import sanitise_output

from .structs import NpcGroup, NpcLimit, convert_group_entry, convert_limit_entries

__all__ = [
    'segregate_container_additions',
    'RuntimeGroupAddition',
]


class RuntimeGroupAddition(ExportModel):
    bp: Optional[str] = Field(...)
    entries: List[NpcGroup] = list()
    limits: List[NpcLimit] = list()


def _merge_changes(dc: Dict[str, List[RuntimeGroupAddition]]) -> List[RuntimeGroupAddition]:
    vs = []
    for klass_name, changes in dc.items():
        if len(changes) == 1:
            vs.append(changes[0])
            continue

        out = changes.pop(0)

        # Concat data arrays
        for extra in changes:
            out.entries += extra.entries
            out.limits += extra.limits

        vs.append(out)
    return vs


def segregate_container_additions(pgd: UAsset) -> Optional[List[RuntimeGroupAddition]]:
    if not pgd.default_export:
        return None

    export_data = pgd.default_export.properties
    d = export_data.get_property('TheNPCSpawnEntriesContainerAdditions', fallback=None)
    if not d:
        return None

    # Extract the addition entries
    changes: Dict[str, List[RuntimeGroupAddition]] = defaultdict(list)
    for add in d.values:
        add = add.as_dict()
        klass = add['SpawnEntriesContainerClass']
        entries = add['AdditionalNPCSpawnEntries'].values
        limits = add['AdditionalNPCSpawnLimits'].values
        if not klass.value.value or (not entries and not limits):
            continue

        out = RuntimeGroupAddition(
            bp=sanitise_output(klass),
            entries=[convert_group_entry(entry) for entry in entries],
            limits=convert_limit_entries(limits),
        )

        # Skip if no data
        if not out.limits and not out.entries:
            continue

        # Append to the fragment list
        klass_name = klass.format_for_json()
        changes[klass_name].append(out)

    return _merge_changes(changes)
