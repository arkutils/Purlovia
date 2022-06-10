from logging import NullHandler, getLogger
from typing import Any, Dict, cast

from automate.hierarchy_exporter import JsonHierarchyExportStage
from ue.hierarchy import find_parent_classes, get_parent_class
from ue.proxy import UEProxyStructure

from .flags import gather_flags
from .missions.dinos import gather_dino_data
from .missions.rewards import collect_rewards
from .missions.typedata import MISSION_TYPES
from .types import MissionType

__all__ = [
    'MissionsStage',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())

OUTPUT_FLAGS = (
    # Meta
    'bShowInUI',
    'bRepeatableMission',
    # Prerequisites
    'bUseBPStaticIsPlayerEligibleForMission',
    'bTreatPlayerLevelRangeAsHardCap',
    # Restrictions
    'bAbsoluteForcePreventLeavingMission',
    'bRemovePlayerFromMissionOnDeath',
    'bDestroyMissionDinosOnDeactivate',
    'bAllowHarvestingMissionDinos',
    'bMissionPreventsCryoDeploy',
    'bMissionPreventsMekDeploy',
    'bMissionWeaponsHaveInfiniteAmmo',
    # Rewards
    'bUseBPGenerateMissionRewards',
)


class MissionsStage(JsonHierarchyExportStage):

    def get_format_version(self) -> str:
        return "3"

    def get_name(self):
        return 'missions'

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_ue_type(self) -> str:
        return MissionType.get_ue_type()

    def extract(self, proxy: UEProxyStructure) -> Any:
        mission: MissionType = cast(MissionType, proxy)

        v: Dict[str, Any] = dict(
            bp=proxy.get_source().fullname,
            type='unknown',
            name=mission.MissionDisplayName[0],
            description=mission.MissionDescription[0],
        )
        v['parent'] = get_parent_class(v['bp'])
        v['flags'] = gather_flags(mission, OUTPUT_FLAGS)
        v['duration'] = mission.MissionMaxDurationSeconds[0]

        v['cooldown'] = {
            'player': mission.PerPlayerMissionCooldown[0],
            'mission': mission.GlobalMissionCooldown[0],
        }

        if not bool(mission.bUseBPStaticIsPlayerEligibleForMission[0]):
            v['prereqs'] = dict(
                missions=mission.get('PrereqMissionTags', fallback=None),
                playerCount=dict(max=mission.MaxPlayerCount[0], ),
                playerLevel=dict(
                    min=mission.MinPlayerLevel[0],
                    tgt=mission.TargetPlayerLevel[0],
                    max=mission.MaxPlayerLevel[0],
                ),
            )

        v['dinos'] = gather_dino_data(mission)
        if not bool(mission.bUseBPGenerateMissionRewards[0]):
            v['rewards'] = collect_rewards(mission)

        _get_subclass_data(mission, v)

        if not v['dinos']:
            del v['dinos']

        return v


def _get_subclass_data(mission: MissionType, v: Dict[str, Any]):
    parents = set(find_parent_classes(mission.get_source()))

    for subtype, support_class in MISSION_TYPES.items():
        if subtype in parents:
            v['type'] = support_class.get_friendly_name()
            support_class.export(mission, v)
            return
