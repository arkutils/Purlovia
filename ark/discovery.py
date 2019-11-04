from logging import NullHandler, getLogger
from pathlib import Path
from typing import *

import ue.hierarchy
from automate.ark import ArkSteamManager
from config import ConfigFile, get_global_config
from ue.asset import UAsset
from ue.loader import AssetLoader, AssetLoadException
from utils.cachefile import cache_data

from .asset import findSubComponentParentPackages
from .common import CHR_CLS, CHR_PKG, DCSC_PKG
from .overrides import get_overrides_for_species
from .tree import inherits_from, walk_parents

__all__ = [
    'SpeciesDiscoverer',
]

logger = getLogger(__name__)
logger.addHandler(NullHandler())


# Obsolete
class ByRawData:
    '''Very fast/cheap method for bulk searching. Over-selects slightly.'''
    def __init__(self, loader: AssetLoader):
        self.loader = loader

    def is_species(self, assetname: str):
        '''Use binary string matching to check if an asset is a character.'''
        # Load asset as raw data
        mem, _ = self.loader.load_raw_asset(assetname)

        # Check for the presence of required string
        result = b'ShooterCharacterMovement' in mem.obj  # type: ignore # just a bad type definition

        return result

    def is_structure(self, assetname: str):
        '''Use binary string matching to check if an asset is a placeable structure.'''
        # Load asset as raw data
        mem, _ = self.loader.load_raw_asset(assetname)

        # Check for the presence of required string
        result = b'StructureMesh' in mem.obj  # type: ignore # just a bad type definition

        return result

    def is_inventory_item(self, assetname: str):
        '''Use binary string matching to check if an asset is an inventory item.'''
        # Load asset as raw data
        mem, _ = self.loader.load_raw_asset(assetname)

        # Check for the presence of required string
        result = b'DescriptiveNameBase' in mem.obj  # type: ignore # just a bad type definition

        return result


# Obsolete
class ByInheritance:
    '''Totally accurate but expensive method, to be used to verify results from other discovery methods.'''
    def __init__(self, loader: AssetLoader):
        self.loader = loader

    def is_species(self, assetname: str):
        '''
        Load the asset fully and check that it inherits from Character and it or one of
        its parents has a component that inherits from DCSC.
        '''
        if not assetname.startswith('/Game'):
            return False

        asset = self.loader[assetname]

        # Must inherit from Character somewhere down the line
        if not inherits_from(asset, CHR_PKG):
            return False

        # Check all parents - if any has a sub-component that inherits from DCSC, we're good
        def check_component(assetname: str):
            if not assetname.startswith('/Game'):
                return False

            try:
                asset = self.loader[assetname]

                for cmpassetname in findSubComponentParentPackages(asset):
                    if not cmpassetname.startswith('/Game'):
                        continue
                    cmpasset = self.loader[cmpassetname]
                    if inherits_from(cmpasset, DCSC_PKG):
                        return True  # finish walk early

            except AssetLoadException as ex:
                logger.warning("Failed to check inheritance of potential species: %s", str(ex))
                return False  # abort early

        # Check this asset first
        if check_component(assetname):
            return True

        # Then check all parents in the tree
        found_dcsc = walk_parents(asset, check_component)

        return found_dcsc


class SpeciesDiscoverer:
    def __init__(self, loader: AssetLoader):
        self.loader = loader
        self.global_excludes = tuple(set(get_global_config().optimisation.SearchIgnore))

    def discover_vanilla_species(self) -> Iterator[str]:
        config = get_global_config()
        official_modids = set(config.official_mods.ids())
        official_modids -= set(config.settings.SeparateOfficialMods)
        official_mod_prefixes = tuple(f'/Game/Mods/{modid}' for modid in official_modids)

        for cls_name in ue.hierarchy.find_sub_classes(CHR_CLS):
            assetname = cls_name[:cls_name.rfind('.')]

            # Skip anything in the mods directory that isn't one of the listed official mods
            if assetname.startswith('/Game/Mods') and not any(assetname.startswith(prefix) for prefix in official_mod_prefixes):
                continue

            modid = self.loader.get_mod_id(assetname) or ''
            if get_overrides_for_species(assetname, modid).skip_export:
                continue

            yield assetname

    def discover_mod_species(self, modid: str) -> Iterator[str]:
        clean_path = self.loader.clean_asset_name(f'/Game/Mods/{modid}')
        for cls_name in ue.hierarchy.find_sub_classes(CHR_CLS):
            assetname = cls_name[:cls_name.rfind('.')]
            if assetname.startswith(clean_path):
                if get_overrides_for_species(assetname, modid).skip_export:
                    continue
                yield assetname


def initialise_hierarchy(arkman: ArkSteamManager, config: ConfigFile = get_global_config()):
    version_key = _gather_version_data(arkman, config)
    loader = arkman.getLoader()
    gen_fn = lambda _: _generate_hierarchy(loader)
    data = cache_data(version_key, 'purlovia_asset_hierarchy', gen_fn, force_regenerate=config.dev.ClearHierarchyCache)
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
        ue.hierarchy.explore_path(f'/Game/Mods/{modid}', loader, mod_excludes)

    # Scan /Game/Mods/<modid> for each configured mod
    for modid in config.mods:
        ue.hierarchy.explore_path(f'/Game/Mods/{modid}', loader, mod_excludes)

    return ue.hierarchy.tree
