from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, cast

from automate.hierarchy_exporter import JsonHierarchyExportStage
from ue.asset import UAsset
from ue.proxy import UEProxyStructure
from ue.utils import clean_double as cd

from .types import NPCSpawnEntriesContainer

__all__ = [
    'SpawnGroupStage',
]


class SpawnGroupStage(JsonHierarchyExportStage):
    def get_name(self) -> str:
        return 'spawn_groups'

    def get_field(self) -> str:
        return 'spawngroups'

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_format_version(self):
        return '3'

    def get_ue_type(self):
        return NPCSpawnEntriesContainer.get_ue_type()

    def get_post_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:
        if modid:
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            package = mod_data.get('package', None)
            if package:
                pgd_asset = self.manager.loader[package]
                result = dict()
                class_swaps = convert_class_swaps(pgd_asset)
                ext_group_changes = segregate_container_additions(pgd_asset)
                if class_swaps:
                    result['classSwaps'] = class_swaps
                if ext_group_changes:
                    result['externalGroupChanges'] = ext_group_changes
                return result
        else:
            pgd_asset = self.manager.loader['/Game/PrimalEarth/CoreBlueprints/BASE_PrimalGameData_BP']
            result = dict()
            class_swaps = convert_class_swaps(pgd_asset)
            if class_swaps:
                result['classSwaps'] = class_swaps
            return result

        return None

    def extract(self, proxy: UEProxyStructure) -> Any:
        container: NPCSpawnEntriesContainer = cast(NPCSpawnEntriesContainer, proxy)

        # Export basic values
        values: Dict[str, Any] = dict()
        values['blueprintPath'] = container.get_source().fullname
        values['maxNPCNumberMultiplier'] = container.MaxDesiredNumEnemiesMultiplier[0]

        # Export NPC class entries
        if container.has_override('NPCSpawnEntries'):
            values['entries'] = [convert_group_entry(entry) for entry in container.NPCSpawnEntries[0].values]

        # Export class spawn limits
        if container.has_override('NPCSpawnLimits'):
            values['limits'] = [convert_limit_entry(entry) for entry in container.NPCSpawnLimits[0].values]

        return values


def convert_group_entry(struct):
    d = struct.as_dict()

    v = dict()
    v['name'] = d['AnEntryName']
    v['weight'] = d['EntryWeight']
    v['classes'] = d['NPCsToSpawn']
    v['spawnOffsets'] = d['NPCsSpawnOffsets']

    # Weights, as confirmed by ZenRowe. It's up to the user to calculate actual chances.
    v['classWeights'] = d['NPCsToSpawnPercentageChance']

    d_swaps = d['NPCRandomSpawnClassWeights'].values
    if d_swaps:
        v['classSwaps'] = [convert_single_class_swap(entry.as_dict()) for entry in d_swaps]

    return v


def convert_limit_entry(struct):
    d = struct.as_dict()

    v = dict()
    v['class'] = d['NPCClass']
    v['desiredNumberMult'] = d['MaxPercentageOfDesiredNumToAllow']

    return v


def convert_single_class_swap(d):
    v = {
        'from': d['FromClass'],
        'exact': d['bExactMatch'],
        'to': d['ToClasses'],
        'weights': d['Weights'],
    }

    if d['ActiveEvent'] and d['ActiveEvent'].value and d[
            'ActiveEvent'].value.value and d['ActiveEvent'].value.value.value != 'None':
        v['during'] = d['ActiveEvent']

    return v


def convert_class_swaps(pgd: UAsset):
    assert pgd.default_export
    all_values = []
    export_data = pgd.default_export.properties
    d = export_data.get_property('GlobalNPCRandomSpawnClassWeights', fallback=None)
    if not d:
        return None

    for entry in d.values:
        all_values.append(convert_single_class_swap(entry.as_dict()))

    return all_values


def segregate_container_additions(pgd: UAsset):
    if not pgd.default_export:
        return None

    export_data = pgd.default_export.properties
    d = export_data.get_property('TheNPCSpawnEntriesContainerAdditions', fallback=None)
    if not d:
        return None

    # Extract the addition entries
    change_queues: Dict[str, List[Dict[str, Any]]] = dict()
    for add in d.values:
        add = add.as_dict()
        klass = add['SpawnEntriesContainerClass']
        entries = add['AdditionalNPCSpawnEntries'].values
        limits = add['AdditionalNPCSpawnLimits'].values
        if not klass.value.value or (not entries and not limits):
            continue

        v = dict()
        v['blueprintPath'] = klass
        if entries:
            v['entries'] = [convert_group_entry(entry) for entry in entries]

        if limits:
            v['limits'] = [convert_limit_entry(entry) for entry in limits]

        # Skip if no data
        if 'limits' not in v and 'entries' not in v:
            continue

        # Append to the fragment list
        klass_name = klass.format_for_json()
        if klass_name not in change_queues:
            change_queues[klass_name] = []
        change_queues[klass_name].append(v)

    # Merge
    vs = []
    for klass_name, changes in change_queues.items():
        if len(changes) == 1:
            vs.append(changes[0])
            continue

        v = changes.pop(0)
        # Make sure 'entries' and 'limits' are initialised.
        if 'entries' not in v:
            v['entries'] = []
        if 'limits' not in v:
            v['limits'] = []

        # Concat data arrays
        for extra in changes:
            if 'entries' in extra:
                v['entries'] += extra['entries']
            if 'limits' in extra:
                v['limits'] += extra['limits']

        # Remove empty arrays and add the container mod
        if not v['limits']:
            del v['limits']
        if not v['entries']:
            del v['entries']
        vs.append(v)

    return vs
