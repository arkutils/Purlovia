from abc import ABC, abstractmethod
from typing import Any, Dict, cast

from export.wiki.types import MissionType, MissionType_Escort, MissionType_Fishing, MissionType_Gather, MissionType_Gauntlet, \
    MissionType_GlitchCounter, MissionType_Hunt, MissionType_Race, MissionType_Retrieve, MissionType_Sport


class BaseMissionType(ABC):
    @classmethod
    @abstractmethod
    def get_friendly_name(cls) -> str:
        ...

    @classmethod
    @abstractmethod
    def export(cls, proxy: MissionType, v: Dict[str, Any]):
        ...


class Hunt(BaseMissionType):
    @classmethod
    def get_friendly_name(cls) -> str:
        return 'hunt'

    @classmethod
    def export(cls, proxy: MissionType, v: Dict[str, Any]):
        ...


class Fishing(BaseMissionType):
    @classmethod
    def get_friendly_name(cls) -> str:
        return 'fishing'

    @classmethod
    def export(cls, proxy: MissionType, v: Dict[str, Any]):
        ...


class Gather(BaseMissionType):
    @classmethod
    def get_friendly_name(cls) -> str:
        return 'gather'

    @classmethod
    def export(cls, proxy: MissionType, v: Dict[str, Any]):
        ...


class Gauntlet(BaseMissionType):
    @classmethod
    def get_friendly_name(cls) -> str:
        return 'gauntlet'

    @classmethod
    def export(cls, proxy: MissionType, v: Dict[str, Any]):
        ...


class Retrieve(BaseMissionType):
    @classmethod
    def get_friendly_name(cls) -> str:
        return 'retrieval'

    @classmethod
    def export(cls, proxy: MissionType, v: Dict[str, Any]):
        mission = cast(MissionType_Retrieve, proxy)
        v['targetItem'] = mission.get('RetrieveItemClass', fallback=None)


class Escort(BaseMissionType):
    @classmethod
    def get_friendly_name(cls) -> str:
        return 'escort'

    @classmethod
    def export(cls, proxy: MissionType, v: Dict[str, Any]):
        mission = cast(MissionType_Escort, proxy)
        v['dinos']['movementTgt'] = dict(
            baseWalk=mission.EscortDinoBaseWalkSpeed[0],
            escortedWalk=mission.EscortDinoEscortedSpeed[0],
        )


class Race(BaseMissionType):
    @classmethod
    def get_friendly_name(cls) -> str:
        return 'race'

    @classmethod
    def export(cls, proxy: MissionType, v: Dict[str, Any]):
        ...


class GlitchCounter(BaseMissionType):
    @classmethod
    def get_friendly_name(cls) -> str:
        return 'glitchCounter'

    @classmethod
    def export(cls, proxy: MissionType, v: Dict[str, Any]):
        ...


class Sport(BaseMissionType):
    @classmethod
    def get_friendly_name(cls) -> str:
        return 'sport'

    @classmethod
    def export(cls, proxy: MissionType, v: Dict[str, Any]):
        ...


MISSION_TYPES = {
    MissionType_Hunt.get_ue_type(): Hunt,
    MissionType_Fishing.get_ue_type(): Fishing,
    MissionType_Gather.get_ue_type(): Gather,
    MissionType_Gauntlet.get_ue_type(): Gauntlet,
    MissionType_Retrieve.get_ue_type(): Retrieve,
    MissionType_Escort.get_ue_type(): Escort,
    MissionType_Race.get_ue_type(): Race,
    MissionType_GlitchCounter.get_ue_type(): GlitchCounter,
    MissionType_Gather.get_ue_type(): Gather,
    MissionType_Sport.get_ue_type(): Sport,
}
