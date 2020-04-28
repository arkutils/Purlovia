from export.wiki.types import MissionType


def gather_dino_data(mission: MissionType):
    v = dict()

    if mission.has_override('MissionWildDinoOutgoingDamageScale') or mission.has_override('MissionWildDinoIncomingDamageScale'):
        v['incomingScaleW'] = mission.MissionWildDinoIncomingDamageScale[0]
        v['outgoingScaleW'] = mission.MissionWildDinoOutgoingDamageScale[0]

    # v['spawns'] (or 'setups'?)
    return v
