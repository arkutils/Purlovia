from typing import TYPE_CHECKING, Callable, Iterable, Iterator, Optional, Tuple, TypeAlias, TypeVar

from cachetools import LRUCache, cached

from ark.stats import Stat
from ark.taming_food.utils import bp_to_clean_class, match_searches
from ue.hierarchy import find_parent_classes
from utils.tree import Node

from .datatypes import Item, ItemUseResult
from .items import food_items

if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    Teffect: TypeAlias = SupportsRichComparison
else:
    Teffect = TypeVar('Teffect')

__all__ = [
    'simplify_for_taming',
    'filter_effects',
    'collapse_duplicates',
    'taming_key',
]

PE_CONSUMABLES = '/Game/PrimalEarth/CoreBlueprints/Items/Consumables'
AB_CONSUMABLES = '/Game/Aberration/CoreBlueprints/Items/Consumables'
EX_CONSUMABLES = '/Game/Extinction/CoreBlueprints/Items/Consumables'
SE_DINOS = '/Game/ScorchedEarth/Dinos'

replacement_bps: dict[str, str] = {
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_Base.PrimalItemConsumable_Kibble_Base_C':
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_Base_XSmall.PrimalItemConsumable_Kibble_Base_XSmall_C',
}

blacklist_bps: dict[str, bool] = {
    # Obsolete specific-egg kibbles
    f'{AB_CONSUMABLES}/PrimalItemConsumable_Kibble_LanternBirdEgg.PrimalItemConsumable_Kibble_LanternBirdEgg_C': True,
    f'{AB_CONSUMABLES}/PrimalItemConsumable_Kibble_LanternLizardEgg.PrimalItemConsumable_Kibble_LanternLizardEgg_C': True,
    f'{AB_CONSUMABLES}/PrimalItemConsumable_Kibble_RockDrakeEgg.PrimalItemConsumable_Kibble_RockDrakeEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_Allo.PrimalItemConsumable_Kibble_Allo_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_AnkyloEgg.PrimalItemConsumable_Kibble_AnkyloEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_ArchaEgg.PrimalItemConsumable_Kibble_ArchaEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_ArgentEgg.PrimalItemConsumable_Kibble_ArgentEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_BaryonyxEgg.PrimalItemConsumable_Kibble_BaryonyxEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_BoaEgg.PrimalItemConsumable_Kibble_BoaEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_CarnoEgg.PrimalItemConsumable_Kibble_CarnoEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_Compy.PrimalItemConsumable_Kibble_Compy_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_DiloEgg.PrimalItemConsumable_Kibble_DiloEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_DimetroEgg.PrimalItemConsumable_Kibble_DimetroEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_DimorphEgg.PrimalItemConsumable_Kibble_DimorphEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_DiploEgg.PrimalItemConsumable_Kibble_DiploEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_DodoEgg.PrimalItemConsumable_Kibble_DodoEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_GalliEgg.PrimalItemConsumable_Kibble_GalliEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_IchthyornisEgg.PrimalItemConsumable_Kibble_IchthyornisEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_IguanodonEgg.PrimalItemConsumable_Kibble_IguanodonEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_KairukuEgg.PrimalItemConsumable_Kibble_KairukuEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_KaproEgg.PrimalItemConsumable_Kibble_KaproEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_KentroEgg.PrimalItemConsumable_Kibble_KentroEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_LystroEgg.PrimalItemConsumable_Kibble_LystroEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_Megalania.PrimalItemConsumable_Kibble_Megalania_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_MegalosaurusEgg.PrimalItemConsumable_Kibble_MegalosaurusEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_MicroraptorEgg.PrimalItemConsumable_Kibble_MicroraptorEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_MoschopsEgg.PrimalItemConsumable_Kibble_MoschopsEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_OviraptorEgg.PrimalItemConsumable_Kibble_OviraptorEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_PachyEgg.PrimalItemConsumable_Kibble_PachyEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_PachyRhinoEgg.PrimalItemConsumable_Kibble_PachyRhinoEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_ParaEgg.PrimalItemConsumable_Kibble_ParaEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_PegomastaxEgg.PrimalItemConsumable_Kibble_PegomastaxEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_Pela.PrimalItemConsumable_Kibble_Pela_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_PteroEgg.PrimalItemConsumable_Kibble_PteroEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_QuetzEgg.PrimalItemConsumable_Kibble_QuetzEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_RaptorEgg.PrimalItemConsumable_Kibble_RaptorEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_RexEgg.PrimalItemConsumable_Kibble_RexEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_SarcoEgg.PrimalItemConsumable_Kibble_SarcoEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_SauroEgg.PrimalItemConsumable_Kibble_SauroEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_ScorpionEgg.PrimalItemConsumable_Kibble_ScorpionEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_SpiderEgg.PrimalItemConsumable_Kibble_SpiderEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_SpinoEgg.PrimalItemConsumable_Kibble_SpinoEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_StegoEgg.PrimalItemConsumable_Kibble_StegoEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_TapejaraEgg.PrimalItemConsumable_Kibble_TapejaraEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_TerrorbirdEgg.PrimalItemConsumable_Kibble_TerrorbirdEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_TherizinoEgg.PrimalItemConsumable_Kibble_TherizinoEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_TrikeEgg.PrimalItemConsumable_Kibble_TrikeEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_TroodonEgg.PrimalItemConsumable_Kibble_TroodonEgg_C': True,
    f'{PE_CONSUMABLES}/PrimalItemConsumable_Kibble_TurtleEgg.PrimalItemConsumable_Kibble_TurtleEgg_C': True,
    f'{SE_DINOS}/Camelsaurus/PrimalItemConsumable_Kibble_Camelsaurus.PrimalItemConsumable_Kibble_Camelsaurus_C': True,
    f'{SE_DINOS}/Mantis/PrimalItemConsumable_Kibble_Mantis.PrimalItemConsumable_Kibble_Mantis_C': True,
    f'{SE_DINOS}/Moth/PrimalItemConsumable_Kibble_Moth.PrimalItemConsumable_Kibble_Moth_C': True,
    f'{SE_DINOS}/SpineyLizard/PrimalItemConsumable_Kibble_SpineyLizard.PrimalItemConsumable_Kibble_SpineyLizard_C': True,
    f'{SE_DINOS}/Vulture/PrimalItemConsumable_Kibble_Vulture.PrimalItemConsumable_Kibble_Vulture_C': True,

    # Obsolete augmented kibbles
    f'{EX_CONSUMABLES}/PrimalItemConsumable_Kibble_Base_XSmall_EX.PrimalItemConsumable_Kibble_Base_XSmall_EX_C': True,
    f'{EX_CONSUMABLES}/PrimalItemConsumable_Kibble_Base_Small_EX.PrimalItemConsumable_Kibble_Base_Small_EX_C': True,
    f'{EX_CONSUMABLES}/PrimalItemConsumable_Kibble_Base_Medium_EX.PrimalItemConsumable_Kibble_Base_Medium_EX_C': True,
    f'{EX_CONSUMABLES}/PrimalItemConsumable_Kibble_Base_Large_EX.PrimalItemConsumable_Kibble_Base_Large_EX_C': True,
    f'{EX_CONSUMABLES}/PrimalItemConsumable_Kibble_Base_Special_EX.PrimalItemConsumable_Kibble_Base_Special_EX_C': True,
    f'{EX_CONSUMABLES}/PrimalItemConsumable_Kibble_Base_XLarge_EX.PrimalItemConsumable_Kibble_Base_XLarge_EX_C': True,
}


def simplify_for_taming(effects: Iterable[ItemUseResult]) -> Iterator[ItemUseResult]:
    # Apply blacklist
    effects = (effect for effect in filter_effects(effects))

    # Remove entries that apply no food
    effects = (effect for effect in remove_no_food(effects))

    # Collapse identical entries down to their parent
    effects = (effect for effect in collapse_duplicates(effects, taming_key))

    return effects


def filter_effects(effects: Iterable[ItemUseResult]) -> Iterator[ItemUseResult]:
    '''
    Filter out items that have been blacklisted, or that have a parent that's blacklisted.
    '''
    for effect in effects:
        # Process blacklists
        # Items are removed if they or any of their parents are blacklisted
        if any(bp in blacklist_bps for bp in find_parent_classes(effect.bp, include_self=True)):
            continue

        # Process replacements
        skip_this = False
        if effect.bp in replacement_bps:
            for other_effect in effects:
                # Don't match against ourself
                if other_effect is effect:
                    continue

                # If there's a match, just skip reporting this one
                if other_effect.bp == replacement_bps[effect.bp]:
                    skip_this = True
                    break
            else:
                # Go ahead and make the adjustment
                effect.bp = replacement_bps[effect.bp]

        if skip_this:
            continue

        yield effect


def collapse_duplicates(results: Iterable[ItemUseResult],
                        compare_by: Callable[[ItemUseResult], Teffect],
                        *,
                        dbg_terms: Optional[tuple[str]] = None) -> list[ItemUseResult]:
    '''
    Remove duplicate results by collapsing down entries where
    their parent is also present with the same values.

    Results are sorted by effect.

    Requires a comparison function that extracts the required information into a single Python-comparable value.
    '''

    # First apply the comparison function to all results
    data = [(result, compare_by(result)) for result in results]

    # Then sort by depth in the food_items tree
    data.sort(key=lambda x: _tree_depth(food_items[x[0].bp]))

    # Now step through the data, collapsing down any duplicates
    found_items: dict[str, Teffect] = {}
    accepted_results: list[ItemUseResult] = []
    for effect in data:
        # Skip this item if it has a matching parent
        if _has_matching_parent(effect[0].bp, effect[1], found_items, dbg_terms=dbg_terms):
            continue

        # Otherwise, add it to the found items
        found_items[effect[0].bp] = effect[1]
        accepted_results.append(effect[0])

    # Sort the results by effect
    accepted_results.sort(key=lambda x: compare_by(x))

    return accepted_results


def remove_no_food(results: Iterable[ItemUseResult]) -> Iterator[ItemUseResult]:
    '''
    Remove results that don't have an effect on food.
    '''
    for result in results:
        food = result.use_item_stats.get(Stat.Food, None)
        if food is None or food.base == 0:
            continue
        yield result


def _has_matching_parent(bp: str,
                         effect: Teffect,
                         found_items: dict[str, Teffect],
                         *,
                         dbg_terms: Optional[tuple[str]] = None) -> bool:
    dbg = match_searches(bp, dbg_terms)
    if dbg:
        print(f'{bp_to_clean_class(bp)}: {effect}')
    for parent in find_parent_classes(bp, include_self=True):
        if dbg:
            print(f'  {bp_to_clean_class(parent)}: {found_items.get(parent, None)}')
        if parent in found_items and dbg:
            print(f'  parent: {found_items[parent]}')
        if parent in found_items and found_items[parent] == effect:
            return True
    return False


@cached(cache=LRUCache(maxsize=200), key=lambda node: node.data.bp)
def _tree_depth(node: Node[Item]) -> int:
    '''
    Return the depth of the given node in the food_items tree.

    The result of this function is cached by blueprint path.
    '''
    if node.parent is None:
        return 0

    return 1 + _tree_depth(node.parent)


def taming_key(result: ItemUseResult) -> Tuple[float, float]:
    '''
    Return a key for sorting taming food items, consisting of the effect on affinity and food.
    '''
    food_effect = result.use_item_stats.get(Stat.Food, None)
    return result.get_affinity_total(), food_effect.base if food_effect else 0


def pure_food_key(result: ItemUseResult) -> float:
    '''
    Return a key for sorting by food effect only.
    '''
    food_effect = result.use_item_stats.get(Stat.Food, None)
    return food_effect.base if food_effect else 0
