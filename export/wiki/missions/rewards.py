from typing import Any, Dict, cast

from export.wiki.loot.gathering import decode_item_name, decode_item_set
from export.wiki.types import MissionType, MissionType_Hunt


def collect_rewards(mission: MissionType):
    d = dict()
    hexagon = _convert_hexagon_values(mission)
    items = _convert_custom_item_sets(mission)
    loottable = _convert_loot_table(mission)

    if hexagon['qty'] != 0:
        d['hexagon'] = hexagon
    if loottable:
        d['loot'] = loottable
    if items and items['count'] != 0:
        d['items'] = items

    return d or None


def _convert_loot_table(mission: MissionType):
    d = mission.get('RewardLootTable', fallback=None)

    if not d or not bool(mission.bAutoRewardLootOnMissionComplete[0]):
        return None

    v = list()
    for entry in d.values:
        ed = entry.as_dict()
        v.append(
            dict(
                type=ed['LootItemType'].get_enum_value_name(),
                weight=ed['Weight'],
                qtyScale=dict(
                    min=ed['MinQuantity'],
                    max=ed['MaxQuantity'],
                    pow=ed['QuantityCurve'].get_enum_value_name(),
                ),
                quality=dict(
                    min=ed['QualityRange'].values[0].x,
                    max=ed['QualityRange'].values[0].y,
                    pow=ed['QualityCurve'].get_enum_value_name(),
                ),
                pool=[decode_item_name(item) for item in ed['LootItemClasses'].values],
            ))

    return v


def _convert_custom_item_sets(mission: MissionType):
    d = mission.get('CustomItemSets', fallback=None)

    if not d or not bool(mission.bAutoRewardFromCustomItemSets[0]):
        return None

    return dict(
        count=mission.RewardItemCount[0],
        qtyScale=dict(min=mission.MinItemSets[0], max=mission.MaxItemSets[0]),
        sets=[decode_item_set(itemset) for itemset in d.values],
    )


def _convert_hexagon_values(mission: MissionType) -> Dict[str, Any]:
    v: Dict[str, Any] = dict()

    v['qty'] = mission.HexagonsOnCompletion[0]
    if mission.bDivideHexogonsOnCompletion[0]:
        v['split'] = True

    # First time hexagon reward
    if int(mission.get('FirstTimeCompletionHexagonRewardOverride', fallback=-1)) != -1:
        v['firstTime'] = mission.FirstTimeCompletionHexagonRewardOverride[0]
    elif mission.has_override('FirstTimeCompletionHexagonRewardBonus'):
        v['bonusFirstTime'] = mission.FirstTimeCompletionHexagonRewardBonus[0]

    # Type-specific extra data
    if isinstance(mission, MissionType_Hunt):
        hunt = cast(MissionType_Hunt, mission)
        v['bonusLastHit'] = hunt.LastHitAdditionalHexagons[0]

    return v
