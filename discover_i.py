# Asset interactive experiments

#%% Setup
from logging import INFO, NullHandler, basicConfig, getLogger
from operator import attrgetter
from pathlib import Path
from typing import *

import yaml

import ark.asset
import ark.mod
import ark.properties
import ue.gathering
from ark.common import *
from automate.ark import ArkSteamManager
from automate.discovery import AssetTester, Discoverer
from config import ConfigFile, get_global_config
from ue.asset import ExportTableItem, ImportTableItem, UAsset
from ue.base import UEBase
from ue.coretypes import *
from ue.loader import AssetLoader, AssetLoadException
from ue.properties import *
from ue.stream import MemoryStream
from ue.tree import discover_inheritance_chain
from ue.utils import get_clean_name
from utils.tree import IndexedTree, Node

basicConfig(level=INFO)

try:
    from interactive_utils import *
except ImportError:
    pass

logger = getLogger(__name__)
logger.addHandler(NullHandler())

config = get_global_config()
config.settings.SkipInstall = True
# config.mods = tuple('111111111'.split(','))
config.mods = tuple('111111111,895711211,839162288'.split(','))

arkman = ArkSteamManager(config=config)
arkman.ensureSteamCmd()
arkman.ensureGameUpdated()
arkman.ensureModsUpdated(config.mods)
loader = arkman.createLoader()

#%%
ROOT_NAME = '/Script/ShooterGame.Object'


#%% Create discoverer
class AssetRef:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return self.name


class HierarchyDiscovery:
    def __init__(self, loader: AssetLoader, config: ConfigFile = get_global_config()):
        self.tree = IndexedTree[AssetRef](AssetRef(ROOT_NAME), attrgetter('name'))
        self.config = config
        self.extensions = ('.uasset', '.umap')
        self.loader = loader

    def load_internal_hierarchy(self, filename: Path):
        with open(filename, 'rt') as f:
            hierarchy_config = yaml.safe_load(f)

        def walk_config(name, content):
            if isinstance(content, str):
                discoverer.tree.add(name, AssetRef(content))
                return

            for value in content:
                if isinstance(value, str):
                    discoverer.tree.add(name, AssetRef(value))
                elif isinstance(value, dict):
                    key, subvalue = next(iter(value.items()))
                    discoverer.tree.add(name, AssetRef(key))
                    walk_config(key, subvalue)

        walk_config(ROOT_NAME, hierarchy_config[ROOT_NAME])

    def explore_path(self, path: str, exclude: str = None):
        '''Run hierarchy discovery over every matching asset within the given path.'''

        # Use globally configure ignore paths, plus optionally specified path
        excludes = set(self.config.optimisation.SearchIgnore)
        if exclude:
            excludes.add(exclude)

        logger.info('Exploring path: %s', path)

        n = 0

        asset_iterator = self.loader.find_assetnames('.*',
                                                     path,
                                                     exclude=excludes,
                                                     extension=self.extensions,
                                                     return_extension=True)
        for (assetname, ext) in asset_iterator:
            n += 1
            if n % 200 == 0: logger.info(assetname)
            try:
                asset = self.loader[assetname]
            except AssetLoadException:
                logger.warning("Failed to load asset: %s", assetname)
                continue

            try:
                self._ingest_asset(asset)
            except AssetLoadException:
                logger.warning("Failed to check parentage of %s", assetname)

            if ext == '.umap':
                loader.cache.remove(assetname)

    def _ingest_asset(self, asset: UAsset):
        if not asset.default_class: return

        chain = discover_inheritance_chain(asset.default_class)
        current = self.tree.root

        for cls_name in chain:
            if cls_name.startswith('/Game'):
                # Remove class name as it is redundant
                cls_name = cls_name[:cls_name.rfind('.')]

            if cls_name in self.tree:
                current = self.tree[cls_name]
            else:
                new_node = Node[AssetRef](AssetRef(cls_name))
                self.tree.add(current, new_node)
                # print(f'{current!r} -> {new_node!r}')
                current = new_node


#%%
discoverer = HierarchyDiscovery(loader)
discoverer.load_internal_hierarchy(Path('config') / 'hierarchy.yaml')

#%% Run
# discoverer.explore_path(f'/Game/')
# discoverer.explore_path(f'/Game/PrimalEarth/CoreBlueprints/Items/Consumables/Seeds')
# discoverer.explore_path(f'/Game/Maps/Extinction')

# Official
discoverer.explore_path(f'/Game', exclude='/Game/Mods/.*')
official_modids = set(get_global_config().official_mods.ids())
official_modids -= set(get_global_config().settings.SeparateOfficialMods)
for modid in official_modids:
    discoverer.explore_path(f'/Game/Mods/{modid}')

# Mods
for modid in get_global_config().mods:
    discoverer.explore_path(f'/Game/Mods/{modid}')

# for mod in ('PrimalEarth', ):
# for mod in ('PrimalEarth', 'Aberration', 'Extinction', 'Genesis', 'Valguero', 'ScorchedEarth'):
#     path = f'/Game/{mod}'
#     print(path)
#     discoverer.explore_path(path)

#%%
print(f'High memory: {loader.cache.highest_memory_seen / 1024.0 / 1024.0:.6}Mb')

#%%
with open('item-tree.txt', 'wt') as f:
    print(pretty(discoverer.tree, max_width=0), file=f)

#%% Show top-level nodes to help discover missing inheritance
# for node in sorted(discoverer.tree.root.nodes, key=lambda n: n.data.name):
#     print(node.data.name)

#%%
