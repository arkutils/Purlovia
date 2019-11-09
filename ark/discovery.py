from logging import NullHandler, getLogger
from pathlib import Path
from typing import *

import ue.hierarchy
from automate.ark import ArkSteamManager
from config import ConfigFile, get_global_config
from ue.asset import ExportTableItem, UAsset
from ue.context import ue_parsing_context
from ue.loader import AssetLoader, AssetLoadException
from utils.cachefile import cache_data

from .asset import findSubComponentExports, findSubComponentParentPackages
from .common import CHR_CLS, CHR_PKG, DCSC_CLS, DCSC_PKG
from .overrides import get_overrides_for_species
from .tree import inherits_from, walk_parents

__all__ = [
    'SpeciesDiscoverer',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


def is_species(cls_name: str, loader: AssetLoader, *, skip_character_check=False) -> bool:
    '''
    Verify a class is a valid character class, complete with DCSC.

    `cls_name` should be the fullname of the class to test
    `loader` needs to be an asset loader
    `skip_character_check` to avoid checking
    '''
    if not skip_character_check and not ue.hierarchy.inherits_from(cls_name, CHR_CLS):
        return False

    with ue_parsing_context(properties=False):
        for parent_cls_name in ue.hierarchy.find_parent_classes(cls_name, include_self=True):
            if not parent_cls_name.startswith('/Game'):
                return False

            parent_asset_name = parent_cls_name[:parent_cls_name.rfind('.')]
            try:
                parent_asset = loader[parent_asset_name]
            except AssetLoadException:
                logger.exception(f'Unexpected loading error while checking for DCSCs of {cls_name}')
                return False  # no way to continue - abort

            for cmp_export in findSubComponentExports(parent_asset):
                if ue.hierarchy.inherits_from(cmp_export, DCSC_CLS):
                    return True

    return False


class SpeciesDiscoverer:
    def __init__(self, loader: AssetLoader):
        self.loader = loader
        self.global_excludes = tuple(set(get_global_config().optimisation.SearchIgnore))

    def discover_vanilla_species(self) -> Iterator[str]:
        config = get_global_config()
        official_modids = set(config.official_mods.ids())
        official_modids -= set(config.settings.SeparateOfficialMods)
        official_mod_prefixes = tuple(f'/Game/Mods/{modid}/' for modid in official_modids)

        for cls_name in ue.hierarchy.find_sub_classes(CHR_CLS):
            assetname = cls_name[:cls_name.rfind('.')]

            # Skip anything in the mods directory that isn't one of the listed official mods
            if assetname.startswith('/Game/Mods') and not any(assetname.startswith(prefix) for prefix in official_mod_prefixes):
                continue

            # Do a full check that this is a species asset
            if not is_species(cls_name, self.loader, skip_character_check=True):
                continue

            modid = self.loader.get_mod_id(assetname) or ''
            if get_overrides_for_species(assetname, modid).skip_export:
                continue

            yield assetname

    def discover_mod_species(self, modid: str) -> Iterator[str]:
        clean_path = self.loader.clean_asset_name(f'/Game/Mods/{modid}') + '/'
        for cls_name in ue.hierarchy.find_sub_classes(CHR_CLS):
            assetname = cls_name[:cls_name.rfind('.')]
            if assetname.startswith(clean_path):
                # Do a full check that this is a species asset
                if not is_species(cls_name, self.loader, skip_character_check=True):
                    continue

                if get_overrides_for_species(assetname, modid).skip_export:
                    continue

                yield assetname


def initialise_hierarchy(arkman: ArkSteamManager, config: ConfigFile = get_global_config()):
    version_key = _gather_version_data(arkman, config)
    loader = arkman.getLoader()
    gen_fn = lambda _: _generate_hierarchy(loader)
    output_path = f'{config.settings.DataDir}/asset_hierarchy'
    data = cache_data(version_key, output_path, gen_fn, force_regenerate=config.dev.ClearHierarchyCache)
    ue.hierarchy.tree = data


def _gather_version_data(arkman: ArkSteamManager, config: ConfigFile):
    # Gather identities and versions of all involved components
    key = dict(format=2,
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
