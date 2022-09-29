'''Parse and cache taming food data for use in extraction phases.'''

from operator import attrgetter
from typing import Iterable, Iterator, List, Optional, Set, Tuple

from ue.loader import AssetLoader
from ue.tree import is_fullname_an_asset
from utils.tree import IndexedTree, Node

from .datatypes import Item, ItemStatus
from .food_items import food_items
from .species import collect_species_data

__all__ = [
    'make_eval_simplification_tree',
    'evaluate_food_for_species',
    'collapse_full_trees',
]

# Potentially interesting species for testing taming foods:
# Equus, Megatherium, Tuso, Giant Queen Bee... and eventually Gacha


def evaluate_food_for_species(cls_name: str,
                              loader: AssetLoader,
                              *,
                              limit_modids: Optional[Iterable[str]] = None) -> Iterator[Item]:
    '''
    Search for all taming foods relevant to the given species, and their effects.
    '''
    overrides = collect_species_data(cls_name, loader)
    for item in food_items.values():
        # Get modid of item and check if we want to include it
        if limit_modids is not None and item.modid not in limit_modids:
            continue

        # Apply overrides to the item
        effect = _apply_species_overrides_to_item(item, overrides)

        # Ignore if it has no relevant effect
        if effect.food.base == 0 and effect.affinity.base == 0:
            continue

        yield effect


def _insert_status_node(tree: IndexedTree[ItemStatus], status: ItemStatus):
    '''Insert the given node into the status tree, ensuring the structure mirrors the item tree.'''
    if status.bp in tree:
        raise ValueError("Duplicate entry")

    bp = status.bp
    item_node: Node[Item] = food_items[bp]
    insert_node: Node[ItemStatus] = Node[ItemStatus](status)
    while True:
        if item_node is item_node.parent or item_node.parent is None:
            raise LookupError("Could not find a place for %s", status.bp)

        item_node = item_node.parent
        bp = item_node.data.bp
        if bp in tree:
            break

        insert_parent_node = Node[ItemStatus](ItemStatus(bp=bp, food=0, affinity=0))
        insert_parent_node.add(insert_node)
        insert_node = insert_parent_node

    tree.insert_segment(bp, insert_node)


def make_eval_simplification_tree(evals: Iterable[Item],
                                  *,
                                  limit_modids: Optional[Iterable[str]] = None) -> IndexedTree[ItemStatus]:
    '''
    Produces a tree with the same structure as the main, full item tree but only containing
    items with affinity affects given the species evaluation passed in.
    '''
    # Begin with an empty tree
    status_root = ItemStatus(bp=food_items.root.data.bp, food=0, affinity=0)
    status_tree: IndexedTree[ItemStatus] = IndexedTree[ItemStatus](status_root, attrgetter('bp'))

    # Add each item that has taming affinity, with the same structure as the main item tree
    for effect in evals:
        item: Item = food_items[effect.bp].data
        if limit_modids is not None and item.modid not in limit_modids:
            continue
        if effect.affinity.base == 0:
            continue
        status = ItemStatus(bp=item.bp, food=effect.food.base, affinity=effect.affinity.base)
        _insert_status_node(status_tree, status)

    return status_tree


def _effect_from_item_status_node(node: Node[ItemStatus]) -> Tuple[float, float]:
    return (node.data.food, node.data.affinity)


def collapse_full_trees(tree: IndexedTree[ItemStatus], items: IndexedTree[Item] = food_items):
    '''
    Reduce trees where possible, removing sub-nodes of a tree if the parent can represent them completely.
    '''
    # Walk the tree from the bottom-up so we don't have to do multiple passes
    node: Node[ItemStatus]
    for node in tree.root.walk_post_iterator():
        # Ignore if there are no sub-nodes
        if not node.nodes:
            continue

        item_node = items[node.data.bp]

        # Must have *all* items covered
        if len(node.nodes) != len(item_node.nodes):
            continue

        data: ItemStatus = node.data

        # Group results by effects
        sub_effects = sorted(node.nodes, key=_effect_from_item_status_node)
        grouped_effects: Set[Tuple[float, float]] = set(_effect_from_item_status_node(n) for n in sub_effects)

        if len(grouped_effects) == 1:
            effect_src: ItemStatus = node.nodes[0].data

            # Give up if parent has an effect and it doesn't matched the sub-nodes
            if (data.food != 0 or data.affinity != 0) and (data.food != effect_src.food or data.affinity != effect_src.affinity):
                continue

            # Transfer effects to parent
            data.food = effect_src.food
            data.affinity = effect_src.affinity

            # Remove sub-nodes
            node.nodes.clear()

    # Fix the tree index after we directly messed with the node lists
    tree.reindex()


def flatten_tree(tree: IndexedTree[ItemStatus]) -> List[ItemStatus]:
    result: List[ItemStatus] = []
    for node in tree.root.walk_iterator(skip_self=False, breadth_first=True):
        if not is_fullname_an_asset(node.data.bp):
            continue
        result.append(node.data)

    return result


def _bp_to_clean_class(bp: str):
    bp = bp[bp.rfind('.') + 1:]
    bp = bp.replace('PrimalItemConsumable_', '')
    if bp.endswith('_C'):
        bp = bp[:-2]
    return bp
