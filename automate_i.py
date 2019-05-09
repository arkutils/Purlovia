#%% Setup
from interactive_utils import *
import logging
logging.basicConfig(level=logging.INFO)

from automate.ark import ArkSteamManager

arkman = ArkSteamManager('./livedata', skipInstall=False)

#%% Init
arkman.ensureSteamCmd()

#%% Update game
gamever = arkman.ensureGameUpdated()
print(f'\nGame:\n')
print(f'Version: {gamever}')
print(f'Content path: {arkman.getContentPath()}')
print()

#%% Update mods
modvers = arkman.ensureModsUpdated([895711211, 919470289])
print(f'\nMods:\n')
pprint(modvers)
print()

#%% Check assets load properly
loader = arkman.createLoader()
print(f'\nChecking loader:\n')

assetnames = (
    'Game/Extinction/Dinos/Owl/Owl_Character_BP',
    '/Game/Mods/ClassicFlyers/Dinos/Ptero/Ptero_Character_BP',
)

for assetname in assetnames:
    asset = loader[assetname]
    assert asset, 'Asset failed to load: ' + assetname
    print(f'  {asset.assetname}')

print(f'\nDone.\n')
