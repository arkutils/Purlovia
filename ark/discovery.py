import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Generator, List, Set, Tuple

import ue.hierarchy
from ark.mod import get_managed_mods, get_official_mods
from automate.ark import ArkSteamManager
from config import get_global_config
from ue.asset import ExportTableItem
from ue.context import ue_parsing_context
from ue.loader import AssetLoadException
from utils.cachefile import cache_data
from utils.log import get_logger
from utils.tree import IndexedTree

__all__ = [
    'initialise_hierarchy',
]

FORMAT_VERSION = 1

logger = get_logger(__name__)


@dataclass
class NodeState:
    parent: str
    done: bool = False


def initialise_hierarchy(arkman: ArkSteamManager):
    logger.info('Beginning hierarchy discovery')

    path = Path(arkman.config.settings.DataDir) / 'hierarchy'
    if arkman.config.dev.ClearHierarchyCache:
        logger.info('Removing old hierarchy cached')
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)

    # Gather cached relationships from core and mods, re-generating as needed
    relations = _gather_relations(arkman, path)

    # Parse the relationships into ue.hierarchy.tree
    ue.hierarchy.tree.clear()
    ue.hierarchy.load_internal_hierarchy(Path('config') / 'hierarchy.yaml')
    _populate_tree_from_relations(ue.hierarchy.tree, relations)

    logger.info('Hierarchy reconstruction complete')


def _populate_tree_from_relations(tree: IndexedTree[str], relations: List[Tuple[str, str]]):
    # Convert inputs to a more useful form (a dict of tree segments for each parent)
    parents: Dict[str, Set[str]] = defaultdict(set)
    for name, parent in relations:
        parents[parent].add(name)

    # Create a list of parents ordered by path length ('/' count) to improve insertion order
    parent_order: List[NodeState] = [NodeState(key) for key in sorted(parents.keys(), key=lambda k: k.count('/'))]

    # Continually try to insert each of our segments until all done
    prev_not_done = -1
    not_done = 99999999
    while not_done and not_done != prev_not_done:
        prev_not_done = not_done
        not_done = 0
        for state in parent_order:
            if state.done:
                continue

            not_done += 1

            parent = state.parent

            # Can we insert this one yet?
            if state.parent in tree:
                for name in parents[parent]:
                    tree.add(parent, name)
                state.done = True
    else:
        # We hit stable state, but have entries remaining
        leftovers = {state.parent: parents[state.parent] for state in parent_order if not state.done}
        _process_leftover_relations(leftovers)


def _process_leftover_relations(entries: Dict[str, Set[str]]):
    transients = list(p for p in entries.keys() if p.startswith('/Engine/Transient.'))
    for parent in transients:
        del entries[parent]

    filename = Path(get_global_config().settings.DataDir) / 'hierarchy_skips.txt'

    with open(filename, 'wt') as f:
        for parent in sorted(entries.keys()):
            f.write(f'\n{parent}:\n')
            for name in sorted(entries[parent]):
                f.write(f'  {name}\n')

    total = sum(len(names) for names in entries.values())
    logger.warning(f"Could not place {total} entries from {len(entries)} parents (see {filename})")


def _gather_relations(arkman: ArkSteamManager, basepath: Path):
    relations: List[Tuple[str, str]]  # list of (name, parent)
    exclusions = arkman.config.optimisation.SearchIgnore

    basepath.mkdir(parents=True, exist_ok=True)

    # Scan core (or read cache)
    cachefile = basepath / 'core'
    version_key = dict(format=FORMAT_VERSION, game_buildid=arkman.getGameBuildId(), exclusions=exclusions)
    relations = cache_data(version_key, cachefile, lambda _: _scan_core(arkman))

    # Scan /Game/Mods/<modid> for each installed mod (or read cache)
    for modid in get_managed_mods():
        cachefile = basepath / f'mod-{modid}'
        mod_version = arkman.getModData(modid)['version']  # type:ignore
        version_key = dict(format=FORMAT_VERSION, mod_version=mod_version, exclusions=exclusions)
        mod_relations = cache_data(version_key, cachefile, lambda _: _scan_mod(modid, arkman))
        relations.extend(mod_relations)

    return relations


def _scan_core(arkman: ArkSteamManager, verbose: bool = False) -> List[Tuple[str, str]]:
    relations: List[Tuple[str, str]] = list()

    # Gather all inheritance relationships from core files
    logger.info('Discovering inheritance for: /Game')
    for name, parent in _explore_path('/Game', False, arkman, verbose=verbose):
        relations.append((name, parent))

    # Gather all inheritance relationships from core 'mods'
    for modid in get_official_mods():
        modpath = f'/Game/Mods/{modid}/'
        logger.info(f'Discovering inheritance for: {modpath}')
        for name, parent in _explore_path(modpath, True, arkman, verbose=verbose):
            relations.append((name, parent))

    # Make the result stable and repeatable for hashing purposes
    relations.sort()
    return relations


def _scan_mod(modid: str, arkman: ArkSteamManager, verbose=False) -> List[Tuple[str, str]]:
    relations: List[Tuple[str, str]] = list()

    modpath = f'/Game/Mods/{modid}/'
    logger.info('Discovering inheritance for mod: %s', modid)

    for name, parent in _explore_path(modpath, True, arkman, verbose=verbose):
        relations.append((name, parent))

    # Make the result stable and repeatable for hashing purposes
    relations.sort()
    return relations


def _explore_path(path: str,
                  is_mod: bool,
                  arkman: ArkSteamManager,
                  verbose: bool = False) -> Generator[Tuple[str, str], None, None]:
    n = 0

    mod_excludes = set(arkman.config.optimisation.SearchIgnore)
    core_excludes = set(['/Game/Mods/.*', *arkman.config.optimisation.SearchIgnore])
    excludes = mod_excludes if is_mod else core_excludes

    loader = arkman.getLoader()

    with ue_parsing_context(properties=False, bulk_data=False):
        asset_iterator = loader.find_assetnames('.*',
                                                path,
                                                exclude=excludes,
                                                extension=ue.hierarchy.asset_extensions,
                                                return_extension=True)
        for (assetname, ext) in asset_iterator:
            n += 1
            if verbose and n % 200 == 0:
                logger.info(assetname)

            try:
                asset = loader.load_asset(assetname, quiet=not verbose)
            except AssetLoadException:
                logger.warning("Failed to load asset: %s", assetname)
                continue

            try:
                export: ExportTableItem
                for export in ue.hierarchy._find_exports_to_store(asset, ext):
                    parent = ue.hierarchy._get_parent_cls(export)
                    fullname = export.fullname
                    if not parent:
                        raise ValueError(f"Unexpected missing parent for export: {fullname}")
                    if not fullname:
                        raise ValueError(f"Unexpected empty export name: {export.asset.assetname}.{export.name}")

                    yield (fullname, parent)

            except AssetLoadException:
                logger.warning("Failed to check parentage of %s", assetname)

            # Remove maps from the cache immediately as they are large and cannot be inherited from
            if ext == '.umap':
                loader.cache.remove(assetname)
