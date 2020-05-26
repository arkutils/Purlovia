from typing import Dict, Iterable, Iterator, List, Set

import ue.hierarchy
from ark.mod import get_core_mods
from ark.overrides import get_overrides_for_map
from config import ConfigFile, get_global_config
from export.wiki.consts import LEVEL_SCRIPT_ACTOR_CLS, WORLD_CLS
from ue.asset import UAsset
from ue.loader import AssetLoader, AssetLoadException
from ue.utils import get_assetpath_from_assetname
from utils.log import get_logger

__all__ = [
    'group_levels_by_directory',
    'LevelDiscoverer',
]

logger = get_logger(__name__)


def group_levels_by_directory(assetnames: Iterable[str]) -> Dict[str, List[str]]:
    '''Takes an unsorted list of levels and groups them by directory.'''
    levels: Dict[str, Set[str]] = dict()

    for assetname in assetnames:
        map_ = get_assetpath_from_assetname(assetname)
        if map_ not in levels:
            levels[map_] = set()
        levels[map_].add(assetname)

    return {path: list(sorted(names)) for path, names in levels.items()}


class LevelDiscoverer:
    def __init__(self, loader: AssetLoader):
        self.loader = loader
        self.global_excludes = tuple(set(get_global_config().optimisation.SearchIgnore))

    def discover_vanilla_levels(self) -> Iterator[str]:
        official_mod_prefixes = tuple(f'/Game/Mods/{modid}/' for modid in get_core_mods())

        all_cls_names = list(ue.hierarchy.find_sub_classes(WORLD_CLS))
        all_cls_names += ue.hierarchy.find_sub_classes(LEVEL_SCRIPT_ACTOR_CLS)

        for cls_name in all_cls_names:
            assetname = cls_name[:cls_name.rfind('.')]

            # Check if this asset is meant to be skipped
            overrides = get_overrides_for_map(assetname, '')
            if overrides.skip_export:
                continue

            # Skip anything in the mods directory that isn't one of the listed official mods
            if assetname.startswith('/Game/Mods') and not any(assetname.startswith(prefix) for prefix in official_mod_prefixes):
                continue

            yield assetname

    def discover_mod_levels(self, modid: str) -> Iterator[str]:
        clean_path = self.loader.clean_asset_name(f'/Game/Mods/{modid}') + '/'

        all_cls_names = list(ue.hierarchy.find_sub_classes(WORLD_CLS))
        all_cls_names += ue.hierarchy.find_sub_classes(LEVEL_SCRIPT_ACTOR_CLS)

        for cls_name in all_cls_names:
            assetname = cls_name[:cls_name.rfind('.')]

            if assetname.startswith(clean_path):
                # Check if this asset is meant to be skipped
                overrides = get_overrides_for_map(assetname, modid)
                if overrides.skip_export:
                    continue

                yield assetname
