#%% Setup
from interactive_utils import *
import logging
logging.basicConfig(level=logging.DEBUG)

from automate.ark import ArkSteamManager

data_path = os.path.abspath(os.path.join('.', 'livedata'))
arkman = ArkSteamManager(data_path)

#%% Init
arkman.ensureSteamCmd()

#%% Update game
gamever = arkman.ensureGameUpdated(skipInstall=False)
print(f'\nGame:\n')
print(f'Version: {gamever}')
print(f'Content path: {arkman.getContentPath()}')

#%% Update mods
modvers = arkman.ensureModsUpdated([1373744537, 1090809604], skipInstall=False)
print(f'\nMods:\n')
pprint(modvers)
