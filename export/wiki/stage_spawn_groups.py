from pathlib import Path, PurePosixPath
from typing import *

from automate.hierarchy_exporter import JsonHierarchyExportStage
from ue.proxy import UEProxyStructure

from .types import NPCSpawnEntriesContainer

__all__ = [
    'SpawnGroupStage',
]


class SpawnGroupStage(JsonHierarchyExportStage):
    def get_skip(self) -> bool:
        return not self.manager.config.export_wiki.ExportSpawningGroups

    def get_field(self):
        return 'spawngroups'

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_format_version(self):
        return "1.0"

    def get_ue_type(self):
        return NPCSpawnEntriesContainer.get_ue_type()

    def extract(self, proxy: UEProxyStructure) -> Any:
        container: NPCSpawnEntriesContainer = cast(NPCSpawnEntriesContainer, proxy)

        # Export basic values
        values: Dict[str, Any] = dict()
        values['blueprintPath'] = container.get_source().fullname
        values['maxNPCNumberMultiplier'] = container.MaxDesiredNumEnemiesMultiplier[0]
        values['entries'] = []
        values['limits'] = []

        # Export NPC class entries
        if container.has_override('NPCSpawnEntries'):
            for entry in container.NPCSpawnEntries[0].values:
                struct_data = entry.as_dict()

                entry_values = dict()
                entry_values['name'] = struct_data['AnEntryName']
                entry_values['weight'] = struct_data['EntryWeight']
                entry_values['classes'] = struct_data['NPCsToSpawn']
                entry_values['spawnOffsets'] = struct_data['NPCsSpawnOffsets']
                entry_values['classChances'] = struct_data['NPCsToSpawnPercentageChance']

                values['entries'].append(entry_values)

        # Calculates chances for each entry (weigh them) and sort
        weight_sum = sum([entry['weight'] for entry in values['entries']])
        for entry in values['entries']:
            if weight_sum != 0:
                entry['chance'] = entry['weight'] / weight_sum  # type: ignore
            else:
                entry['chance'] = entry['weight']  # type: ignore
            del entry['weight']
        values['entries'].sort(key=lambda e: e['chance'], reverse=True)

        # Export class spawn limits
        if container.has_override('NPCSpawnLimits'):
            for entry in container.NPCSpawnLimits[0].values:
                struct_data = entry.as_dict()

                entry_values = dict()
                entry_values['class'] = struct_data['NPCClass']
                entry_values['desiredNumberMult'] = struct_data['MaxPercentageOfDesiredNumToAllow']

                values['limits'].append(entry_values)

        return values
