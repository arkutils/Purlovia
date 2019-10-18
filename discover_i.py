# Asset interactive experiments

#%% Setup
from logging import INFO, NullHandler, basicConfig, getLogger
from pathlib import Path
from typing import *

import yaml

from automate.ark import ArkSteamManager
from config import ConfigFile, get_global_config
from ue.hierarchy import Hierarchy

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
discoverer = Hierarchy(loader, config=config)
discoverer.load_internal_hierarchy(Path('config') / 'hierarchy.yaml')

# Official
discoverer.explore_path(f'/Game', exclude='/Game/Mods/.*')
official_modids = set(get_global_config().official_mods.ids())
official_modids -= set(get_global_config().settings.SeparateOfficialMods)
for modid in official_modids:
    discoverer.explore_path(f'/Game/Mods/{modid}')

# Mods
for modid in get_global_config().mods:
    discoverer.explore_path(f'/Game/Mods/{modid}')

#%%
with open('item-tree.txt', 'wt') as f:
    print(pretty(discoverer.tree, max_width=0), file=f)

#%%
print(f'High memory: {loader.cache.manager.highest_memory_seen / 1024.0 / 1024.0:.6}Mb')

#%% Show top-level nodes to help discover missing inheritance
# for node in sorted(discoverer.tree.root.nodes, key=lambda n: n.data.name):
#     print(node.data.name)

#%%
