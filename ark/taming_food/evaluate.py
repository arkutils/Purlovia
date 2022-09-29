'''
This file contains the logic that applies food overrides from species to items.

The results are usually large and need further processing to be useful.
'''

from copy import deepcopy
from typing import Iterable, Iterator, Optional

from ark.taming_food.datatypes import Item, ItemUseResult, SpeciesItemOverride
from ark.taming_food.items import food_items
from ark.taming_food.utils import bp_to_clean_class, match_searches
from ue.hierarchy import find_parent_classes

from .simplify import blacklist_bps

__all__ = [
    'evaluate_foods',
]


def evaluate_foods(overrides: list[SpeciesItemOverride],
                   require_dino_use: bool,
                   require_dino_taming: bool,
                   *,
                   limit_modids: Optional[Iterable[str]] = None,
                   dbg_terms: Optional[tuple[str]] = None) -> Iterator[ItemUseResult]:
    '''
    Evalulate the effect of a list of food overrides by applying them to all items (within the given modids).
    '''
    # Iterate over all items in the database
    for item in food_items.values():
        # Get modid of item and check if we want to include it
        if limit_modids is not None and item.modid not in limit_modids:
            continue

        # Ensure it can be used the way we want
        if require_dino_use and item.preventDinoUse:
            continue
        if require_dino_taming and item.preventDinoAutoUse:
            continue

        # Apply overrides to the item
        effect = _apply_species_overrides_to_item(item, overrides, dbg_terms=dbg_terms)

        # Ignore if it has no relevant effect
        if effect is None or _can_ignore_effect(effect):
            continue

        yield effect


def _apply_species_overrides_to_item(item: Item,
                                     overrides: list[SpeciesItemOverride],
                                     *,
                                     dbg_terms: Optional[tuple[str]] = None) -> ItemUseResult | None:
    '''
    Apply relevant overrides (from a species/settings) to an item.
    '''
    # From testing, this looks like it starts with the base item and applies
    # all overrides and multipliers that are relevant to it

    output = ItemUseResult(bp=item.bp)

    # Start with an unchanged copy of the original item effects
    output.affinity = 1
    output.affinity_mult = item.affinity_mult
    output.untamed_priority = item.untamed_priority
    output.use_item_stats = deepcopy(item.use_item_stats)
    unchanged = True

    dbg = match_searches(item.bp, dbg_terms) and item.bp not in blacklist_bps
    if dbg:
        print(f'{bp_to_clean_class(item.bp)}...')
        print(f'  Affinity: {output.affinity} * {output.affinity_mult}')

    # Apply every override that matches (parent match included)
    for override in overrides:
        dbgovr = dbg  # and match_searches(override.bp, dbg_terms)
        if dbgovr:
            print(f'  Checking override {bp_to_clean_class(override.bp)}')
        for cls_name in list(find_parent_classes(item.bp, include_self=True)):
            if dbgovr:
                print(f'    Checking: {bp_to_clean_class(cls_name)}')
            if override.bp == cls_name:
                changed = _apply_override_to_item(output, override, dbg=dbgovr)
                if changed:
                    unchanged = False
                if dbg:
                    if changed:
                        print('        =>')
                        print(f'          Affinity: {output.affinity} * {output.affinity_mult}')

    if dbg:
        if unchanged:
            print('    No changes')
        else:
            print("  Result:")
            print(f'    Affinity: {output.affinity} * {output.affinity_mult}')

    return None if unchanged else output


def _apply_override_to_item(result: ItemUseResult, override: SpeciesItemOverride, *, dbg=False) -> bool:
    '''
    Apply a food override to the current accumulated result data.

    Returns True if the result changed, False otherwise.
    '''
    changed = False

    if dbg:
        print(f'      Applying {bp_to_clean_class(override.bp)} to {bp_to_clean_class(result.bp)}:')

    # Apply stat overrides
    for stat, override_effect in override.mults.items():
        # Multiplying by zero removes the stat effect entirely
        if override_effect == 0:
            stat_was_present = stat in result.use_item_stats
            if stat_was_present:
                if dbg:
                    print(f'        removing {stat.name}')
                del result.use_item_stats[stat]
                changed = True
        else:
            original_effect = result.use_item_stats.get(stat, None)
            if original_effect is not None:
                if dbg:
                    print(f'        {stat.name} {original_effect.base} -> {original_effect.base * override_effect}')
                original_effect.base *= override_effect
                changed = True

    # Apply affinity override
    if result.affinity != override.affinity_override and override.affinity_override != 0:
        if dbg:
            print(f'        override affinity from {result.affinity} to {override.affinity_override}')
        result.affinity = override.affinity_override
        changed = True
    elif dbg:
        print(f'        affinity stays at {result.affinity}')

    # Apply affinity multiplier
    if override.affinity_mult != 1:
        if dbg:
            print(
                f'        affinity mult by {override.affinity_mult} to {result.affinity_mult * override.affinity_mult} !*!*!*!*!'
            )
        result.affinity_mult *= override.affinity_mult
        changed = True
    elif dbg:
        print(f'        affinity mult stays at {result.affinity_mult}')

    if result.untamed_priority != override.untamed_priority:
        if dbg:
            print(f'        override untamed_priority from {result.untamed_priority} to {override.untamed_priority}')
        result.untamed_priority = override.untamed_priority
        changed = True
    elif dbg:
        print(f'        untamed_priority stays at {result.untamed_priority}')

    return changed


def _can_ignore_effect(effect: ItemUseResult) -> bool:
    # If there's a non-zero effect on affinity, we need it
    if effect.affinity * effect.affinity_mult != 0:
        return False

    # If any stat effect is non-zero, we need it
    for stat in effect.use_item_stats.values():
        if stat.base != 0:
            return False

    # Otherwise, there's nothing useful here
    return True
