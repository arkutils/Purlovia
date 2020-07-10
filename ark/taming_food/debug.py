from math import ceil
from operator import itemgetter
from typing import Any, List

from ark.types import PrimalDinoCharacter
from ue.gathering import gather_properties
from ue.loader import AssetLoader

from .calc import evaluate_food_for_species
from .datatypes import Item, ItemOverride

__all__ = (
    'print_species_overrides',
    'print_eval_by_affinity',
    'print_results_for_species',
    'print_item_effects',
)


def print_species_overrides(foods: List[ItemOverride], sort=True):
    data: List[Any] = [(
        _bp_to_clean_class(food.bp),
        food.untamed_priority,
        food.mults['food'],
        food.mults['torpor'],
        food.mults['affinity'],
        food.overrides.get('affinity', 0),
    ) for food in foods]

    headers = ('classname', 'pri', 'food*', 'torp*', 'aff*', 'aff=')
    if sort:
        data = sorted(data, reverse=True, key=itemgetter(5))

    from tabulate import tabulate
    table = tabulate([headers, *data], headers='firstrow')
    print(table)


def print_eval_by_affinity(evals: List[Item]):
    data = [(item.food.base, item.affinity.base, _bp_to_clean_class(item.bp)) for item in evals if item.affinity.base]
    data.sort(reverse=True, key=itemgetter(0))  # sort by food first
    data.sort(reverse=True, key=itemgetter(1))  # and primarily by affinity
    headers = ('food', 'aff', 'class')

    from tabulate import tabulate
    table = tabulate([headers, *data], headers='firstrow')
    print(table)


def print_results_for_species(species: str, loader: AssetLoader):
    proxy: PrimalDinoCharacter = gather_properties(loader[species])
    affinity_required = float(proxy.RequiredTameAffinity[0] + proxy.RequiredTameAffinityPerBaseLevel[0] * 149) / 2

    def items_to_tame(item: Item):
        return ceil(affinity_required / item.affinity.base)

    evals = evaluate_food_for_species(species, loader)
    data = [(item.food.base, item.affinity.base, items_to_tame(item), _bp_to_clean_class(item.bp)) for item in evals
            if item.affinity.base]
    data.sort(reverse=True, key=itemgetter(0))  # sort by food first
    data.sort(reverse=True, key=itemgetter(1))  # and primarily by affinity
    headers = ('food', 'aff', 'need', 'class')

    from tabulate import tabulate
    table = tabulate([headers, *data], headers='firstrow')
    print(f"{species}:  (needs {affinity_required} affinity @ level 150)")
    print(table)


def print_item_effects(item: Item):
    print(f"{item.name}:")
    print(f"      Food: {item.food if item.food else '-'}")
    print(f"    Torpor: {item.torpor if item.torpor else '-'}")
    print(f"  Affinity: {item.affinity if item.affinity else '-'}")


def _bp_to_clean_class(bp: str):
    bp = bp[bp.rfind('.') + 1:]
    bp = bp.replace('PrimalItemConsumable_', '')
    if bp.endswith('_C'):
        bp = bp[:-2]
    return bp
