from abc import ABCMeta, abstractmethod
from pathlib import Path, PurePosixPath
from typing import *
from typing import cast

from automate.hierarchy_exporter import JsonHierarchyExportStage
from automate.jsonutils import save_as_json
from config import ConfigFile
from ue.asset import ExportTableItem
from ue.hierarchy import find_sub_classes
from ue.loader import AssetLoadException
from ue.proxy import UEProxyStructure

from .types import NPCSpawnEntriesContainer

__all__ = [
    'SpawnGroupStage',
]


class SpawnGroupStage(JsonHierarchyExportStage):
    def get_skip(self) -> bool:
        return False
        # return not self.manager.config.export_wiki.ExportBiomeData

    def get_field(self):
        return 'spawngroups'

    def get_use_pretty(self) -> bool:
        return True
        # return self.manager.config.export_asb.PrettyJson

    def get_core_file_path(self):
        return PurePosixPath('spawngroups/core.json')

    def get_mod_file_path(self, modid: str):
        return PurePosixPath(f'spawngroups/{modid}.json')

    def get_format_version(self):
        return "1"

    def get_ue_type(self):
        return NPCSpawnEntriesContainer.get_ue_type()

    def extract(self, proxy: UEProxyStructure) -> Any:
        container: NPCSpawnEntriesContainer = cast(NPCSpawnEntriesContainer, proxy)

        v: Dict[str, Any] = dict()
        v['blueprintPath'] = container.get_source().fullname
        v['maxNPCNumberMultiplier'] = container.MaxDesiredNumEnemiesMultiplier[0]
        v['dinoEntries'] = []
        v['dinoLimits'] = []

        for entry in container.NPCSpawnEntries[0].values:
            struct_data = entry.as_dict()

            entry_values = dict()
            entry_values['name'] = struct_data['AnEntryName']
            entry_values['weight'] = struct_data['EntryWeight']
            entry_values['classes'] = struct_data['NPCsToSpawn']
            entry_values['spawnOffsets'] = struct_data['NPCsSpawnOffsets']
            entry_values['perClassChance'] = struct_data['NPCsToSpawnPercentageChance']

            v['dinoEntries'].append(entry_values)

        weight_sum = sum([entry['weight'] for entry in v['dinoEntries']])
        for entry in v['dinoEntries']:
            if weight_sum != 0:
                entry['chance'] = entry['weight'] / weight_sum  # type: ignore
            else:
                entry['chance'] = entry['weight']  # type: ignore
            del entry['weight']

        v['dinoEntries'].sort(key=lambda e: e['chance'], reverse=True)

        if container.has_override('NPCSpawnLimits'):
            for entry in container.NPCSpawnLimits[0].values:
                struct_data = entry.as_dict()

                entry_values = dict()
                entry_values['class'] = struct_data['NPCClass']
                if struct_data['MaxDesiredNumEnemiesMultiplier']:
                    entry_values['maxNumberMultiplier'] = struct_data['MaxDesiredNumEnemiesMultiplier']
                else:
                    entry_values['maxNumberMultiplier'] = 1.0  # FIXME: Verify this value

                v['dinoLimits'].append(entry_values)

        return v
