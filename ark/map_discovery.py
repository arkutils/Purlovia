from typing import *

from config import get_global_config
from ue.loader import AssetLoader

__all__ = [
    'ToplevelMapsDiscoverer',
]


class ByRawData:
    '''Very fast/cheap method for bulk searching. Over-selects slightly.'''

    def __init__(self, loader: AssetLoader):
        self.loader = loader

    def is_persistent_level(self, assetname: str):
        '''Use binary string matching to check if an asset is a character.'''
        # Load asset as raw data
        #print("  ** Doing the fast test")
        mem = self.loader._load_raw_asset(assetname)

        # Check for the presence of required string
        result = b'LevelScriptActor' in mem.obj

        return result


class ByDefaultExportKlass:

    def __init__(self, loader: AssetLoader):
        self.loader = loader

    def is_persistent_level(self, assetname: str):
        #print("  ** Doing the expensive test")
        if not assetname.startswith('/Game'):
            return False

        asset = self.loader[assetname]

        if asset.asset.default_export is not None:
            if str(asset.asset.default_export.klass.value.super.value.name) == 'LevelScriptActor':
                #print("  *** OK")
                return True

        del self.loader.cache[assetname]
        return False


class ToplevelMapsDiscoverer:
    def __init__(self, loader: AssetLoader):
        self.loader = loader
        self.testByRawData = ByRawData(self.loader)
        self.testByExportKlass = ByDefaultExportKlass(self.loader)

        self.global_excludes = tuple(set(get_global_config().optimisation.SearchIgnore))

    def _is_persistent_level(self, assetname: str) -> bool:
        #print("TEST", assetname)
        return self.testByRawData.is_persistent_level(assetname) and self.testByExportKlass.is_persistent_level(assetname)

    def discover_vanilla_toplevel_maps(self) -> Iterator[str]:
        # Scan /Game/Maps, excluding excludes from config
        for level in self.loader.find_assetnames('.*', '/Game/Maps', exclude=('/Game/Maps/PGARK/PGARK', *self.global_excludes), extension='.umap'):
            if self._is_persistent_level(level):
                yield level

        # Scan /Game/Mods/<modid> for each of the official mods, skipping ones in SeparateOfficialMods
        #official_modids = set(get_global_config().official_mods.ids())
        #official_modids -= set(get_global_config().settings.SeparateOfficialMods)
        #for modid in official_modids:
        #    for species in self.loader.find_assetnames('.*', f'/Game/Mods/{modid}', exclude=self.global_excludes):
        #        if self._is_persistent_level(level):
        #            yield level
