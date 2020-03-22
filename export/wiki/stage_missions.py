from logging import NullHandler, getLogger
from pathlib import PurePosixPath
from typing import *

from automate.hierarchy_exporter import JsonHierarchyExportStage
from export.wiki.types import *
from ue.asset import UAsset
from ue.proxy import UEProxyStructure

from .stage_drops import decode_item_set

__all__ = [
    'MissionsStage',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class MissionsStage(JsonHierarchyExportStage):
    def get_format_version(self) -> str:
        return "1"

    def get_name(self):
        return 'missions'

    def get_field(self) -> str:
        return "missions"

    def get_use_pretty(self) -> bool:
        return bool(self.manager.config.export_wiki.PrettyJson)

    def get_ue_type(self) -> str:
        return MissionType.get_ue_type()

    def extract(self, proxy: UEProxyStructure) -> Any:
        mission: MissionType = cast(MissionType, proxy)

        v: Dict[str, Any] = dict()
        v['bp'] = proxy.get_source().fullname
        v['type'] = 'Base'
        v['name'] = mission.MissionDisplayName[0]
        v['description'] = mission.MissionDescription[0]

        v['targetPlayerLevel'] = mission.TargetPlayerLevel[0]
        v['maxPlayers'] = mission.MaxPlayerCount[0]
        v['maxDuration'] = mission.MissionMaxDurationSeconds[0]
        v['globalCooldown'] = mission.GlobalMissionCooldown[0]
        v['canBeRepeated'] = mission.bRepeatableMission[0]

        v['dinos'] = dict()
        if mission.has_override('MissionWildDinoOutgoingDamageScale') or mission.has_override(
                'MissionWildDinoIncomingDamageScale'):
            v['dinos']['incomingScaleW'] = mission.MissionWildDinoIncomingDamageScale[0]
            v['dinos']['outgoingScaleW'] = mission.MissionWildDinoOutgoingDamageScale[0]

        v['rewards'] = dict(
            hexagons=_convert_hexagon_values(mission),
            items=_convert_item_rewards(mission),
        )

        _get_more_values(mission, v)

        if not v['dinos']:
            del v['dinos']

        return v


def _get_more_values(mission: MissionType, v: Dict[str, Any]):
    if isinstance(mission, MissionType_Retrieve):
        retrieval = cast(MissionType_Retrieve, mission)
        v['type'] = 'Retrieve'

        v['retrieval'] = dict(item=retrieval.get('RetrieveItemClass', fallback=None))
    elif isinstance(mission, MissionType_Escort):
        escort = cast(MissionType_Escort, mission)
        v['type'] = 'Escort'

        v['dinos']['walkSpeedTgt'] = escort.EscortDinoBaseWalkSpeed[0]
        v['dinos']['escortedSpeedTgt'] = escort.EscortDinoEscortedSpeed[0]
    elif isinstance(mission, MissionType_Hunt):
        _hunt = cast(MissionType_Hunt, mission)
        v['type'] = 'Hunt'
    elif isinstance(mission, MissionType_Race):
        _race = cast(MissionType_Race, mission)
        v['type'] = 'Race'
    elif isinstance(mission, MissionType_Fishing):
        _fishing = cast(MissionType_Fishing, mission)
        v['type'] = 'Fishing'
    elif isinstance(mission, MissionType_Gauntlet):
        _gauntlet = cast(MissionType_Gauntlet, mission)
        v['type'] = 'Gauntlet'
    elif isinstance(mission, MissionType_GlitchCounter):
        _counter = cast(MissionType_GlitchCounter, mission)
        v['type'] = 'GlitchCounter'
    elif isinstance(mission, MissionType_Gather):
        _gather = cast(MissionType_Gather, mission)
        v['type'] = 'Gather'
    elif isinstance(mission, MissionType_Sport):
        _sport = cast(MissionType_Sport, mission)
        v['type'] = 'SportGeneric'
        if isinstance(mission, MissionType_Basketball):
            _basketball = cast(MissionType_Basketball, _sport)
            v['type'] = 'SportBasketball'


def _convert_item_rewards(mission: MissionType):
    d = mission.get('CustomItemSets', fallback=None)
    v = list()

    if d:
        for itemset in d.values:
            v.append(decode_item_set(itemset))

    return dict(
        qtyScale=(mission.MinItemSets[0], mission.MaxItemSets[0]),
        sets=v,
    )


def _convert_hexagon_values(mission: MissionType) -> Dict[str, Any]:
    v: Dict[str, Any] = dict()

    v['qty'] = mission.HexagonsOnCompletion[0]
    if mission.bDivideHexogonsOnCompletion[0]:
        v['split'] = True
    if mission.has_override('FirstTimeCompletionHexagonRewardBonus'):
        v['firstTimeBonus'] = mission.FirstTimeCompletionHexagonRewardBonus[0]

    # Type-specific extra data
    if isinstance(mission, MissionType_Hunt):
        hunt = cast(MissionType_Hunt, mission)
        v['lastHitBonus'] = hunt.LastHitAdditionalHexagons[0]

    return v
