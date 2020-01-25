from pathlib import Path, PurePosixPath
from typing import *

from automate.hierarchy_exporter import JsonHierarchyExportStage
from ue.asset import UAsset
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

    def get_pre_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:
        if modid:
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            title = mod_data['title'] or mod_data['name']
            return dict(mod=dict(id=modid, tag=mod_data['name'], title=title))

        return None


    def get_post_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:
        if modid:
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            package = mod_data.get('package', None)
            if package:
                pgd_asset = self.manager.loader[package]
                return dict(
                    classSwaps=convert_class_swaps(pgd_asset),
                    externalGroupChanges=segregate_container_changes(pgd_asset),
                )

        return None

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
                entry_values['chance'] = 0 # Add field so the order is right later
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

def convert_single_class_swap(d):
    return {
        'from': d['FromClass'],
        'to': d['ToClasses'],
        'chances': d['Weights'],
    }

def convert_class_swaps(pgd: UAsset):
    all_values = []
    export_data = pgd.default_export.properties
    d = export_data.get_property('GlobalNPCRandomSpawnClassWeights', fallback=None)
    if not d:
        return None
    
    for entry in d.values:
        all_values.append(convert_single_class_swap(entry.as_dict()))

    return all_values

def segregate_container_changes(pgd: UAsset):
    return None
