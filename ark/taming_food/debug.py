'''Debug and experimentation functions for testing food calculations.'''

from math import ceil
from operator import itemgetter
from typing import Iterable, List

from ark.stats import Stat
from ark.types import PrimalDinoCharacter
from interactive.tables import display_table
from ue.gathering import gather_properties
from ue.loader import AssetLoader

from .datatypes import Item, ItemStatEffect, ItemUseResult, SpeciesFoods, SpeciesItemOverride
from .evaluate import evaluate_foods
from .simplify import collapse_duplicates, filter_effects, simplify_for_taming, taming_key
from .species import collect_species_data
from .utils import bp_to_clean_class

__all__ = (
    'print_species_overrides',
    'print_eval_by_taming',
    'print_taming_for_species',
    'print_item_effects',
    'print_food_for_species',
)


def print_species_overrides(foods: SpeciesFoods, sort=True):
    '''
    Print the food overrides for a species.

    Example:
    ```
    >>> print_species_overrides(collect_species_data(DODO_CHR, loader))`
    ```
    '''
    print(f"{bp_to_clean_class(foods.bp)}:")
    _print_food_overrides(foods.adult_eats, sort)
    if foods.child_eats is None:
        print('(no child food overrides)')
    else:
        print("\nChild:")
        _print_food_overrides(foods.child_eats, sort)


def _print_food_overrides(foods: List[SpeciesItemOverride] | None, sort=True):
    if foods is None:
        print("  No overrides")
        return

    data = [(
        bp_to_clean_class(food.bp),
        food.untamed_priority,
        food.mults[Stat.Food],
        food.mults[Stat.Torpidity],
        food.affinity_mult,
        food.affinity_override,
    ) for food in foods]

    headers = ('classname', 'pri', 'food*', 'torp*', 'aff*', 'aff=')
    if sort:
        data = sorted(data, reverse=True, key=itemgetter(5))

    display_table(data, headers)


def print_eval_by_taming(evals: Iterable[ItemUseResult]):
    '''
    Print the results of evaluating food for a species, sorted by taming effect.

    Example:
    ```
    >>> gather_items(loader, limit_modids=CORE_MODIDS)
    >>> dodo_food = collect_species_data(DODO_CHR, loader)
    >>> effects = list(evaluate_foods(dodo_food.adult_eats, True, True, limit_modids=CORE_MODIDS))
    >>> print_eval_by_taming(effects)
    ```
    '''
    data = [(item.use_item_stats.get(Stat.Food, ItemStatEffect()), item.get_affinity_total(), item.untamed_priority,
             bp_to_clean_class(item.bp)) for item in evals if item.get_affinity_total()]
    data.sort(reverse=True, key=itemgetter(2))  # sort by priority
    data.sort(reverse=False, key=itemgetter(0))  # then by food
    data.sort(reverse=True, key=itemgetter(1))  # then by affinity first
    headers = ('food', 'aff', 'pri', 'class')

    display_table(data, headers)


def print_food_for_species(species: str,
                           loader: AssetLoader,
                           *,
                           limit_modids: Iterable[str] = None,
                           dbg_terms: tuple[str] | None = None):
    proxy: PrimalDinoCharacter = gather_properties(loader[species])
    foods = collect_species_data(proxy)
    _display_food_for_species(species, foods.adult_eats, limit_modids=limit_modids, dbg_terms=dbg_terms)
    if foods.child_eats is not None:
        print("\nAs child:")
        _display_food_for_species(species, foods.child_eats, limit_modids=limit_modids, dbg_terms=dbg_terms)


def _display_food_for_species(species: str,
                              eats: list[SpeciesItemOverride],
                              *,
                              limit_modids: Iterable[str] | None = None,
                              dbg_terms: tuple[str] | None = None):
    evals = evaluate_foods(eats, True, False, limit_modids=limit_modids, dbg_terms=dbg_terms)
    evals = collapse_duplicates(evals, taming_key, dbg_terms=dbg_terms)  # type: ignore
    evals = filter_effects(evals)  # type: ignore
    data = [(item.use_item_stats.get(Stat.Food, ItemStatEffect()), bp_to_clean_class(item.bp)) for item in evals
            if Stat.Food in item.use_item_stats]
    data.sort(reverse=False, key=itemgetter(1))  # sort by name
    data.sort(reverse=True, key=itemgetter(0))  # and primarily by food
    headers = ('food', 'class')

    print(f"{bp_to_clean_class(species)} food:")
    display_table(data, headers)


def print_taming_for_species(species: str,
                             loader: AssetLoader,
                             level=150,
                             *,
                             limit_modids: Iterable[str] = None,
                             dbg_terms: tuple[str] | None = None):
    proxy: PrimalDinoCharacter = gather_properties(loader[species])
    affinity_required = float(proxy.RequiredTameAffinity[0] + proxy.RequiredTameAffinityPerBaseLevel[0] * level) / 4

    def items_to_tame(item: ItemUseResult):
        return ceil(affinity_required / item.get_affinity_total())

    foods = collect_species_data(proxy)
    evals = evaluate_foods(foods.adult_eats, True, True, limit_modids=limit_modids, dbg_terms=dbg_terms)
    evals = simplify_for_taming(evals)
    data = [(item.use_item_stats.get(Stat.Food, ItemStatEffect()), item.untamed_priority, item.get_affinity_total(),
             round(item.get_affinity_total() / affinity_required * 100, 3), items_to_tame(item), bp_to_clean_class(item.bp))
            for item in evals if item.get_affinity_total()]
    data.sort(reverse=False, key=itemgetter(0))  # sort by food first
    data.sort(reverse=False, key=itemgetter(4))  # and primarily by items needed
    headers = ('food', 'pri', 'aff', 'tame%', 'need', 'class')

    print(f"{bp_to_clean_class(species)} needs {affinity_required} affinity @ level {level}:")
    display_table(data, headers)


def print_item_effects(item: Item):
    print(f"{item.name}:")
    for stat, value in item.use_item_stats.items():
        print(f"{stat.name:>10}: {value}")
    print(f"  Affinity: {item.affinity_mult if item.affinity_mult else '-'}")
