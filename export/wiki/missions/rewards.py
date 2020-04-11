from typing import *

from export.wiki.stage_drops import decode_item_set
from export.wiki.types import MissionType, MissionType_Hunt


def collect_rewards(mission: MissionType):
    d = dict()
    hexagon = _convert_hexagon_values(mission)
    items = _convert_item_rewards(mission)

    if hexagon['qty'] != 0:
        d['hexagon'] = hexagon
    if items['count'] != 0:
        d['items'] = items

    return d or None


def _convert_item_rewards(mission: MissionType):
    d = mission.get('CustomItemSets', fallback=None)
    v = list()

    if d:
        for itemset in d.values:
            v.append(decode_item_set(itemset))

    return dict(
        count=mission.RewardItemCount[0],
        qtyScale=(mission.MinItemSets[0], mission.MaxItemSets[0]),
        sets=v,
    )


def _convert_hexagon_values(mission: MissionType) -> Dict[str, Any]:
    v: Dict[str, Any] = dict()

    v['qty'] = mission.HexagonsOnCompletion[0]
    if mission.bDivideHexogonsOnCompletion[0]:
        v['split'] = True
    if mission.has_override('FirstTimeCompletionHexagonRewardBonus'):
        v['bonusFirstTime'] = mission.FirstTimeCompletionHexagonRewardBonus[0]

    # Type-specific extra data
    if isinstance(mission, MissionType_Hunt):
        hunt = cast(MissionType_Hunt, mission)
        v['bonusLastHit'] = hunt.LastHitAdditionalHexagons[0]

    return v
