from logging import NullHandler, getLogger
from pathlib import Path
from typing import *

import ue.hierarchy
from automate.ark import ArkSteamManager
from config import ConfigFile, get_global_config
from ue.context import ue_parsing_context
from ue.loader import AssetLoader, AssetLoadException
from utils.cachefile import cache_data

from .common import CHR_CLS, CHR_PKG, DCSC_CLS, DCSC_PKG

__all__ = [
    'initialise_hierarchy',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


def initialise_hierarchy(arkman: ArkSteamManager, config: ConfigFile = get_global_config()):
    version_key = _gather_version_data(arkman, config)
    loader = arkman.getLoader()
    gen_fn = lambda _: _generate_hierarchy(loader)
    output_path = f'{config.settings.DataDir}/asset_hierarchy'
    data = cache_data(version_key, output_path, gen_fn, force_regenerate=config.dev.ClearHierarchyCache)
    ue.hierarchy.tree = data


def _gather_version_data(arkman: ArkSteamManager, config: ConfigFile):
    # Gather identities and versions of all involved components
    if not arkman.mod_data_cache or not arkman.getGameVersion():
        raise AssertionError("ArkManager must be fully initialised")
    key = dict(format=4,
               core=dict(version=arkman.getGameVersion(), buildid=arkman.getGameBuildId()),
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
    ue.hierarchy.explore_path('/Game', loader, core_excludes)

    # Scan /Game/Mods/<modid> for each of the official mods, skipping ones in SeparateOfficialMods
    official_modids = set(config.official_mods.ids())
    official_modids -= set(config.settings.SeparateOfficialMods)
    for modid in official_modids:
        ue.hierarchy.explore_path(f'/Game/Mods/{modid}/', loader, mod_excludes)

    # Scan /Game/Mods/<modid> for each configured mod
    for modid in config.mods:
        ue.hierarchy.explore_path(f'/Game/Mods/{modid}/', loader, mod_excludes)

    return ue.hierarchy.tree
