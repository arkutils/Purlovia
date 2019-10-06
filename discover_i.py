# Asset interactive experiments

#%% Setup
try:
    from interactive_utils import *
except ImportError:
    pass

from operator import attrgetter
from typing import *

import yaml

import ark.asset
import ark.mod
import ark.properties
import ue.gathering
from ark.common import *
from automate.ark import ArkSteamManager
from automate.discovery import AssetTester, Discoverer
from ue.asset import ExportTableItem, ImportTableItem, UAsset
from ue.base import UEBase
from ue.coretypes import *
from ue.loader import AssetLoader, AssetNotFound
from ue.properties import *
from ue.stream import MemoryStream
from ue.tree import discover_inheritance_chain
from ue.utils import get_clean_name
from utils.tree import IndexedTree, Node

arkman = ArkSteamManager()
loader = arkman.createLoader()

#%%
ROOT_NAME = '/'


#%% Create discoverer
class AssetRef:
    def __init__(self, name: str):
        self.name = name

    def __repr__(self):
        return self.name


class HierarchyGatherer(AssetTester):
    def __init__(self):
        self.root = AssetRef(ROOT_NAME)
        self.tree = IndexedTree[AssetRef](self.root, attrgetter('name'))

    @classmethod
    def get_category_name(cls):
        return "hierarchy"

    @classmethod
    def get_file_extensions(cls):
        return ('.uasset', '.umap')

    @classmethod
    def get_requires_properties(cls):
        return False

    def is_a_fast_match(self, mem: bytes):
        return True

    def is_a_full_match(self, asset: UAsset):
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

        return False


#%%
discoverer = Discoverer(loader)
gatherer = HierarchyGatherer()
discoverer.register_asset_tester(gatherer)

#%%
with open('config/hierarchy.yaml', 'rt') as f:
    hierarchy_config = yaml.safe_load(f)


def walk_config(name, content):
    if isinstance(content, str):
        gatherer.tree.add(name, AssetRef(content))
        return

    for value in content:
        if isinstance(value, str):
            gatherer.tree.add(name, AssetRef(value))
        elif isinstance(value, dict):
            key, subvalue = next(iter(value.items()))
            gatherer.tree.add(name, AssetRef(key))
            walk_config(key, subvalue)


walk_config(ROOT_NAME, hierarchy_config['/'])

#%% Run
# discoverer.run(f'/Game/')
# discoverer.run(f'/Game/PrimalEarth/CoreBlueprints/Items/Consumables/Seeds')

# for mod in ('PrimalEarth', ):
for mod in ('PrimalEarth', 'Aberration', 'Extinction', 'Genesis', 'Valguero', 'ScorchedEarth'):
    path = f'/Game/{mod}/'
    print(path)
    discoverer.run(path)

#%%
with open('item-tree.txt', 'wt') as f:
    print(pretty(gatherer.tree, max_width=0), file=f)

#%%
for node in sorted(gatherer.tree.root.nodes, key=lambda n: n.data.name):
    print(node.data.name)

#%%
