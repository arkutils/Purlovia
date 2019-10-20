from typing import List, Optional

from ue.asset import UAsset
from ue.loader import AssetLoader, ModNotFound

from .spawncontainers import (SpawnGroupEntry, SpawnGroupLimitEntry,
                              SpawnGroupObject, get_spawn_entry_container_data)


def gather_spawn_groups_from_pgd(loader: AssetLoader, pgd: UAsset) -> Optional[List[SpawnGroupObject]]:
    groups = []
    pgd_data = pgd.default_export.properties.as_dict()
    additions = pgd_data['TheNPCSpawnEntriesContainerAdditions'][0]
    if not additions:
        return None
    
    for addition in additions.values:
        data = addition.as_dict()
        klass = data['SpawnEntriesContainerClass']
        entries = data['AdditionalNPCSpawnEntries']
        limits = data['AdditionalNPCSpawnLimits']
        if not klass.format_for_json():
            continue

        try:
            group_data = get_spawn_entry_container_data(loader, klass.format_for_json())
            if not group_data:
                continue
        except ModNotFound:
            continue

        for add_entry in entries.values:
            group_data.entries.append(SpawnGroupEntry(add_entry))
        for add_limit in limits.values:
            group_data.limits.append(SpawnGroupLimitEntry(add_limit))
        group_data.calculate_chances()
        groups.append(group_data)

    return groups
