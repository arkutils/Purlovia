from logging import NullHandler, getLogger
from typing import Iterable, Iterator

import ue.hierarchy
from config import ConfigFile, get_global_config
from ue.asset import UAsset
from ue.loader import AssetLoader, AssetLoadException

from .consts import LEVEL_SCRIPT_ACTOR_CLS, WORLD_CLS

logger = getLogger(__name__)
logger.addHandler(NullHandler())


class LevelDiscoverer:
    def __init__(self, loader: AssetLoader):
        self.loader = loader
        self.global_excludes = tuple(set(get_global_config().optimisation.SearchIgnore))

    def discover_vanilla_levels(self) -> Iterator[str]:
        config = get_global_config()
        official_modids = set(config.official_mods.ids())
        official_modids -= set(config.settings.SeparateOfficialMods)
        official_mod_prefixes = tuple(f'/Game/Mods/{modid}/' for modid in official_modids)

        all_cls_names = list(ue.hierarchy.find_sub_classes(WORLD_CLS))
        all_cls_names += ue.hierarchy.find_sub_classes(LEVEL_SCRIPT_ACTOR_CLS)

        for cls_name in all_cls_names:
            assetname = cls_name[:cls_name.rfind('.')]

            # Skip anything in the mods directory that isn't one of the listed official mods
            if assetname.startswith('/Game/Mods') and not any(assetname.startswith(prefix) for prefix in official_mod_prefixes):
                continue

            modid = self.loader.get_mod_id(assetname) or ''
            #if get_overrides_for_species(assetname, modid).skip_export:
            #    continue

            yield assetname
