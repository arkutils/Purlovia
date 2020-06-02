from pathlib import Path

import ue.hierarchy
from ark.mod import get_managed_mods, get_official_mods
from automate.ark import ArkSteamManager
from config import ConfigFile, get_global_config
from ue.loader import AssetLoader
from utils.cachefile import cache_data
from utils.log import get_logger

__all__ = [
    'initialise_hierarchy',
]

logger = get_logger(__name__)


def initialise_hierarchy(arkman: ArkSteamManager, config: ConfigFile = get_global_config()):
    version_key = _gather_version_data(arkman, config)
    loader = arkman.getLoader()

    def gen_fn(_):
        return _generate_hierarchy(loader)

    output_path = f'{config.settings.DataDir}/asset_hierarchy'
    data = cache_data(version_key, output_path, gen_fn, force_regenerate=config.dev.ClearHierarchyCache)
    ue.hierarchy.tree = data


def _gather_version_data(arkman: ArkSteamManager, config: ConfigFile):
    # Gather identities and versions of all involved components
    if not arkman.mod_data_cache or not arkman.getGameBuildId():
        raise AssertionError("ArkManager must be fully initialised")
    key = dict(format=5,
               core=dict(buildid=arkman.getGameBuildId()),
               mods=dict((modid, arkman.getModData(modid)['version']) for modid in config.mods))  # type: ignore
    return key


def _generate_hierarchy(loader: AssetLoader):
    config = get_global_config()

    core_excludes = set(['/Game/Mods/.*', *config.optimisation.SearchIgnore])
    mod_excludes = set(config.optimisation.SearchIgnore)

    # Always load the internal hierarchy
    ue.hierarchy.tree.clear()
    ue.hierarchy.load_internal_hierarchy(Path('config') / 'hierarchy.yaml')

    # Scan /Game, excluding /Game/Mods and any excludes from config
    ue.hierarchy.explore_path('/Game', loader, core_excludes, disable_debug=True)

    # Scan /Game/Mods/<modid> for each of the 'core' (build-in) mods
    for modid in get_official_mods():
        ue.hierarchy.explore_path(f'/Game/Mods/{modid}/', loader, mod_excludes, disable_debug=True)

    # Scan /Game/Mods/<modid> for each installed mod
    for modid in get_managed_mods():
        ue.hierarchy.explore_path(f'/Game/Mods/{modid}/', loader, mod_excludes, disable_debug=True)

    return ue.hierarchy.tree
