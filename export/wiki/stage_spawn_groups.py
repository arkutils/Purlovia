from typing import Any, Dict, Optional, cast

from automate.hierarchy_exporter import ExportFileModel, ExportModel, JsonHierarchyExportStage
from ue.asset import UAsset
from ue.proxy import UEProxyStructure

from .spawn_groups.additions import RuntimeGroupAddition, segregate_container_additions
from .spawn_groups.remaps import DinoRemap, convert_npc_remaps
from .spawn_groups.structs import NpcGroup, NpcLimit, WeighedClassSwap, \
    convert_class_swaps, convert_group_entry, convert_limit_entries
from .types import NPCSpawnEntriesContainer

__all__ = [
    'SpawnGroupStage',
]


class NpcGroupsContainer(ExportModel):
    bp: str
    maxNPCNumberMultiplier: float
    entries: List[NpcGroup] = list()
    limits: List[NpcLimit] = list()


class SpawnGroupsExportModel(ExportFileModel):
    spawngroups: List[NpcGroupsContainer]
    classSwaps: List[WeighedClassSwap]
    externalGroupChanges: List[RuntimeGroupAddition]
    dinoRemaps: List[DinoRemap]

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
        return '4'

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
                return self._get_pgd_data(pgd_asset)
        else:
            pgd_asset = self.manager.loader['/Game/PrimalEarth/CoreBlueprints/BASE_PrimalGameData_BP']
            return self._get_pgd_data(pgd_asset)

        return None

    def _get_pgd_data(self, pgd: UAsset) -> Dict[str, Any]:
        v: Dict[str, Any] = dict()

        class_swaps = list(convert_class_swaps(pgd))
        ext_group_changes = segregate_container_additions(pgd)
        npc_remaps = convert_npc_remaps(pgd)

        if class_swaps:
            v['classSwaps'] = class_swaps
        if ext_group_changes:
            v['externalGroupChanges'] = ext_group_changes
        if npc_remaps:
            v['dinoRemaps'] = npc_remaps

        return v

    def extract(self, proxy: UEProxyStructure) -> Any:
        container: NPCSpawnEntriesContainer = cast(NPCSpawnEntriesContainer, proxy)

        # Export basic values
        out = NpcGroupsContainer(
            bp=container.get_source().fullname,
            maxNPCNumberMultiplier=container.MaxDesiredNumEnemiesMultiplier[0],
        )

        # Export NPC class entries
        if container.has_override('NPCSpawnEntries'):
            out.entries = [convert_group_entry(entry) for entry in container.NPCSpawnEntries[0].values]

        # Export class spawn limits
        if container.has_override('NPCSpawnLimits'):
            out.limits = list(convert_limit_entries(container.NPCSpawnLimits[0].values))

        return out
