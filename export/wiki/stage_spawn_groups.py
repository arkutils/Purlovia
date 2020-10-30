from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, cast

from automate.hierarchy_exporter import ExportFileModel, ExportModel, Field, JsonHierarchyExportStage
from ue.asset import UAsset
from ue.proxy import UEProxyStructure
from ue.utils import sanitise_output

from .maps.models import WeighedClassSwap
from .types import NPCSpawnEntriesContainer

__all__ = [
    'SpawnGroupStage',
]


class Vector(ExportModel):
    x: float
    y: float
    z: float


class NpcGroup(ExportModel):
    name: str
    weight: float
    classes: List[Optional[str]]
    spawnOffsets: List[Vector]
    classWeights: List[float]
    classSwaps: Optional[List[WeighedClassSwap]]


class NpcLimit(ExportModel):
    klass: Optional[str] = Field(..., alias="class")
    desiredNumberMult: float

    class Config:
        allow_population_by_field_name = True


class NpcGroupsContainer(ExportModel):
    blueprintPath: str
    maxNPCNumberMultiplier: float
    entries: Optional[List[NpcGroup]]
    limits: Optional[List[NpcLimit]]


class RuntimeGroupAddition(ExportModel):
    blueprintPath: Optional[str] = Field(...)
    entries: List[NpcGroup] = list()
    limits: List[NpcLimit] = list()


class SpawnGroupsExportModel(ExportFileModel):
    spawngroups: List[NpcGroupsContainer]
    classSwaps: List[WeighedClassSwap]
    externalGroupChanges: List[RuntimeGroupAddition]

    class Config:
        title = "NPC spawning groups data for the Wiki"


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

    def get_schema_model(self):
        return SpawnGroupsExportModel

    def get_post_data(self, modid: Optional[str]) -> Optional[Dict[str, Any]]:
        if modid:
            mod_data = self.manager.arkman.getModData(modid)
            assert mod_data
            package = mod_data.get('package', None)
            if package:
                pgd_asset = self.manager.loader[package]
                result: Dict[str, Any] = dict()
                # Export global NPC replacements and runtime group
                # additions from the mod PGD.
                class_swaps = list(convert_class_swaps(pgd_asset))
                ext_group_changes = segregate_container_additions(pgd_asset)
                if class_swaps:
                    result['classSwaps'] = class_swaps
                if ext_group_changes:
                    result['externalGroupChanges'] = ext_group_changes
                return result
        else:
            pgd_asset = self.manager.loader['/Game/PrimalEarth/CoreBlueprints/BASE_PrimalGameData_BP']
            result = dict()
            # Export global NPC replacements from core PGD.
            class_swaps = list(convert_class_swaps(pgd_asset))
            if class_swaps:
                result['classSwaps'] = class_swaps
            return result

        return None

    def extract(self, proxy: UEProxyStructure) -> Any:
        container: NPCSpawnEntriesContainer = cast(NPCSpawnEntriesContainer, proxy)

        # Export basic values
        out = NpcGroupsContainer(
            blueprintPath=container.get_source().fullname,
            maxNPCNumberMultiplier=container.MaxDesiredNumEnemiesMultiplier[0],
        )

        # Export NPC class entries
        if container.has_override('NPCSpawnEntries'):
            out.entries = [convert_group_entry(entry) for entry in container.NPCSpawnEntries[0].values]

        # Export class spawn limits
        if container.has_override('NPCSpawnLimits'):
            out.limits = [convert_limit_entry(entry) for entry in container.NPCSpawnLimits[0].values]

        return out


def convert_group_entry(struct) -> NpcGroup:
    d = struct.as_dict()
    out = NpcGroup(
        name=str(d['AnEntryName']),
        weight=d['EntryWeight'],
        classes=sanitise_output(d['NPCsToSpawn']),
        spawnOffsets=sanitise_output(d['NPCsSpawnOffsets']),
        classWeights=d['NPCsToSpawnPercentageChance'].values,
    )

    # Export local random class swaps if any exist
    swaps = d['NPCRandomSpawnClassWeights'].values
    if swaps:
        out.classSwaps = [convert_single_class_swap(entry.as_dict()) for entry in swaps]

    return out


def convert_limit_entry(struct) -> NpcLimit:
    d = struct.as_dict()
    return NpcLimit(
        klass=sanitise_output(d['NPCClass']),
        desiredNumberMult=d['MaxPercentageOfDesiredNumToAllow'],
    )


def convert_single_class_swap(d) -> WeighedClassSwap:
    result = WeighedClassSwap(from_class=sanitise_output(d['FromClass']),
                              exact=bool(d.get('bExactMatch', True)),
                              to=sanitise_output(d['ToClasses']),
                              weights=d['Weights'].values)

    if d['ActiveEvent'] and d['ActiveEvent'].value and d['ActiveEvent'].value.value:
        # Assigning "None" here is safe as it is the field default and therefore omitted
        result.during = str(d['ActiveEvent'])

    return result


def convert_class_swaps(pgd: UAsset) -> Iterable[WeighedClassSwap]:
    assert pgd.default_export
    export_data = pgd.default_export.properties
    d = export_data.get_property('GlobalNPCRandomSpawnClassWeights', fallback=None)
    if not d:
        return None

    for entry in d.values:
        yield convert_single_class_swap(entry.as_dict())


def segregate_container_additions(pgd: UAsset) -> Optional[List[RuntimeGroupAddition]]:
    if not pgd.default_export:
        return None

    export_data = pgd.default_export.properties
    d = export_data.get_property('TheNPCSpawnEntriesContainerAdditions', fallback=None)
    if not d:
        return None

    # Extract the addition entries
    change_queues: Dict[str, List[RuntimeGroupAddition]] = defaultdict(list)
    for add in d.values:
        add = add.as_dict()
        klass = add['SpawnEntriesContainerClass']
        entries = add['AdditionalNPCSpawnEntries'].values
        limits = add['AdditionalNPCSpawnLimits'].values
        if not klass.value.value or (not entries and not limits):
            continue

        out = RuntimeGroupAddition(
            blueprintPath=sanitise_output(klass),
            entries=[convert_group_entry(entry) for entry in entries],
            limits=[convert_limit_entry(entry) for entry in limits],
        )

        # Skip if no data
        if not out.limits and not out.entries:
            continue

        # Append to the fragment list
        klass_name = klass.format_for_json()
        change_queues[klass_name].append(out)

    # Merge
    vs = []
    for klass_name, changes in change_queues.items():
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
